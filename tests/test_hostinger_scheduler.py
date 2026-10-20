import contextlib
import io
import argparse
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import check_hostinger_scheduler as smoke
from scripts import hostinger_scheduler_state as scheduler


class SchedulerStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "state.json"
        self.success = datetime(2026, 10, 15, 13, 47, 18, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp_dir.cleanup()

    def initialize(self):
        scheduler.initialize_state(
            self.state_file,
            last_success_utc=scheduler.format_utc(self.success),
        )

    def test_rolling_interval_blocks_before_48_hours_and_allows_at_threshold(self):
        self.initialize()
        self.assertEqual(
            self.success + timedelta(hours=48),
            scheduler.eligibility_deadline(self.state_file),
        )
        self.assertFalse(
            scheduler.is_eligible(
                self.state_file,
                self.success + timedelta(hours=47, minutes=59, seconds=59),
            )
        )
        self.assertFalse(
            scheduler.is_eligible(
                self.state_file,
                self.success + timedelta(hours=48, microseconds=-1),
            )
        )
        self.assertTrue(
            scheduler.is_eligible(
                self.state_file,
                self.success + timedelta(hours=48),
            )
        )

    def test_durable_state_survives_process_restart_and_missed_hourly_slots(self):
        self.initialize()
        before_eligibility = self.success + timedelta(hours=47)
        after_missed_slots = self.success + timedelta(days=3)
        restarted_process_state = scheduler.read_state(self.state_file)
        self.assertEqual(scheduler.format_utc(self.success), restarted_process_state["last_success_utc"])
        self.assertFalse(scheduler.is_eligible(self.state_file, before_eligibility))
        self.assertTrue(scheduler.is_eligible(self.state_file, after_missed_slots))

    def test_a_success_after_catchup_resets_eligibility_and_blocks_hourly_check(self):
        self.initialize()
        catchup_success = self.success + timedelta(days=3)
        scheduler.mark_attempt(self.state_file, "catchup-run", catchup_success - timedelta(minutes=1))
        scheduler.record_success(self.state_file, "catchup-run", catchup_success)
        self.assertFalse(
            scheduler.is_eligible(
                self.state_file,
                catchup_success + timedelta(hours=24),
            )
        )
        self.assertTrue(
            scheduler.is_eligible(
                self.state_file,
                catchup_success + timedelta(hours=48),
            )
        )

    def test_conservative_first_run_anchor_is_not_reported_as_a_success(self):
        first_run_after = self.success + timedelta(hours=48)
        scheduler.initialize_state(
            self.state_file,
            first_run_after_utc=scheduler.format_utc(first_run_after),
        )
        state = scheduler.read_state(self.state_file)
        self.assertIsNone(state["last_success_utc"])
        self.assertEqual(first_run_after, scheduler.eligibility_deadline(self.state_file))

    def test_success_record_restarts_the_rolling_interval(self):
        self.initialize()
        recorded_at = self.success + timedelta(hours=49)
        scheduler.mark_attempt(self.state_file, "successful-run", recorded_at - timedelta(minutes=1))
        scheduler.record_success(self.state_file, "successful-run", recorded_at)
        self.assertEqual(
            recorded_at + timedelta(hours=48),
            scheduler.eligibility_deadline(self.state_file),
        )

    def test_failed_attempt_is_recorded_and_retried_no_sooner_than_six_hours(self):
        self.initialize()
        attempt_at = self.success + timedelta(hours=48)
        scheduler.mark_attempt(self.state_file, "failed-run", attempt_at)
        failure_at = attempt_at + timedelta(minutes=30)
        scheduler.record_failure(self.state_file, "exit-code", "failed-run", failure_at)
        self.assertEqual(
            failure_at + timedelta(hours=6),
            scheduler.next_attempt_after(self.state_file),
        )
        self.assertFalse(
            scheduler.is_eligible(
                self.state_file,
                failure_at + timedelta(hours=6) - timedelta(microseconds=1),
            )
        )
        self.assertTrue(
            scheduler.is_eligible(
                self.state_file,
                failure_at + timedelta(hours=6),
            )
        )
        self.assertEqual(
            scheduler.format_utc(failure_at),
            scheduler.read_state(self.state_file)["last_failure_utc"],
        )

    def test_outcome_from_skipped_or_other_invocation_cannot_mark_prior_attempt_failed(self):
        self.initialize()
        self.assertIsNone(
            scheduler.record_failure(
                self.state_file,
                "exec-condition",
                "unrelated-run",
                self.success + timedelta(hours=48),
            )
        )
        self.assertIsNone(scheduler.read_state(self.state_file)["last_failure_utc"])

    def test_clock_rollback_before_completion_fails_closed(self):
        self.initialize()
        attempt_at = self.success + timedelta(hours=48)
        scheduler.mark_attempt(self.state_file, "clock-test", attempt_at)
        with self.assertRaisesRegex(scheduler.SchedulerStateError, "Host clock precedes"):
            scheduler.record_success(
                self.state_file,
                "clock-test",
                attempt_at - timedelta(seconds=1),
            )

    def test_initialization_will_not_overwrite_state(self):
        self.initialize()
        with self.assertRaisesRegex(scheduler.SchedulerStateError, "Refusing to overwrite"):
            self.initialize()

    def test_eligible_dry_run_never_records_an_attempt(self):
        self.initialize()
        with patch.dict("os.environ", {"INVOCATION_ID": "must-not-be-used"}):
            status = scheduler.run_command(argparse.Namespace(
                command="eligible",
                state_file=self.state_file,
                dry_run=True,
            ))
        self.assertEqual(0, status)
        self.assertIsNone(scheduler.read_state(self.state_file)["last_attempt_utc"])

    def test_missing_or_invalid_state_fails_closed(self):
        with self.assertRaisesRegex(scheduler.SchedulerStateError, "state is missing"):
            scheduler.eligibility_deadline(self.state_file)
        self.state_file.write_text('{"version": 1, "last_success_utc": "not-a-date"}', encoding="utf-8")
        with self.assertRaisesRegex(scheduler.SchedulerStateError, "Invalid timestamp"):
            scheduler.eligibility_deadline(self.state_file)


class SchedulerSmokeTestTests(unittest.TestCase):
    def test_old_success_is_reported_stale_even_when_systemd_result_is_success(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            last_success = datetime(2026, 10, 15, 13, 47, 18, tzinfo=timezone.utc)
            scheduler.initialize_state(
                state_file,
                last_success_utc=scheduler.format_utc(last_success),
            )
            now = last_success + timedelta(hours=61)
            with patch.object(
                smoke,
                "systemd_properties",
                side_effect=[
                    "ActiveState=active\nResult=success",
                    "ActiveState=inactive\nResult=success\nExecMainStatus=0",
                ],
            ) as systemd, contextlib.redirect_stdout(io.StringIO()) as output:
                result = smoke.run_check(state_file, now)

        self.assertEqual(1, result)
        self.assertIn("Result=success", output.getvalue())
        self.assertIn("is stale (>60h)", output.getvalue())
        self.assertEqual(2, systemd.call_count)
        self.assertEqual(
            ["vutrulabs-job-tracker-public.timer", "vutrulabs-job-tracker-public.service"],
            [call.args[0] for call in systemd.call_args_list],
        )

    def test_systemd_inspection_uses_only_show_operations(self):
        with patch.object(
            smoke.subprocess,
            "run",
            return_value=type("Result", (), {"returncode": 0, "stdout": "ActiveState=active\n", "stderr": ""})(),
        ) as run:
            smoke.systemd_properties("sample.timer", ("ActiveState",))
        self.assertEqual("show", run.call_args.args[0][1])


if __name__ == "__main__":
    unittest.main()
