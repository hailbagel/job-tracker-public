import csv
import json
import os
import subprocess
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import publish_public_data as publication
from scripts import hostinger_scheduler_state as scheduler
from jobtracker.pipeline import run_source
from jobtracker.processing import (
    CHANGE_FIELDS,
    COMMON_OUTPUTS,
    DETAIL_FIELDS,
    LATEST_FIELDS,
)
from jobtracker.registry import get_source


def completed(command, returncode=0, stdout=""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout)


class ScriptEntrypointTests(unittest.TestCase):
    def test_documented_command_imports_package_without_pythonpath(self):
        repo = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        environment["PYTHONNOUSERSITE"] = "1"
        environment["JOB_TRACKER_PUBLISH_BRANCH"] = "__import_contract_test__"
        with tempfile.TemporaryDirectory() as runtime:
            environment["JOB_TRACKER_RUNTIME_DIR"] = runtime
            result = subprocess.run(
                ["python3", "scripts/publish_public_data.py"],
                cwd=repo,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertEqual(1, result.returncode)
        self.assertNotIn("ModuleNotFoundError", result.stdout)
        self.assertIn("Expected publication branch __import_contract_test__", result.stdout.replace(chr(39), ""))


class ProviderConfigurationTests(unittest.TestCase):
    @patch.object(publication, "sources", return_value=[{"id": "spacex"}])
    def test_registry_enabled_sources_are_authoritative(self, configured):
        enabled = publication.validate_enabled_providers(Path("."))
        self.assertEqual([{"id": "spacex"}], enabled)
        configured.assert_called_once_with(Path("configs/sources.json"), enabled_only=True)


class GitPublicationTests(unittest.TestCase):
    counts = {name: index + 1 for index, name in enumerate(publication.REQUIRED_PROVIDERS)}

    @patch.object(publication, "changed_paths", return_value={"data/spacex/processed/jobs_latest.csv"})
    @patch.object(publication, "run")
    def test_success_stages_allowlist_commits_counts_and_pushes_without_force(self, command, _changed):
        command.side_effect = lambda args, check=True: completed(args, 1 if args[1:4] == ["diff", "--cached", "--quiet"] else 0)
        self.assertTrue(publication.commit_and_push(self.counts, 4, "main"))
        commands = [item.args[0] for item in command.call_args_list]
        add = next(item for item in commands if item[:2] == ["git", "add"])
        self.assertEqual(set(publication.OUTPUT_ALLOWLIST), set(add[3:]))
        commit = next(item for item in commands if item[:2] == ["git", "commit"])
        self.assertIn("neura=1 spacex=2 tesla=3 jacobs=4; patrick=4", commit[-1])
        self.assertIn(["git", "push", "origin", "HEAD:main"], commands)
        self.assertFalse(any("--force" in item for item in commands))

    @patch.object(publication, "changed_paths", return_value=set())
    @patch.object(publication, "run")
    def test_no_change_creates_no_empty_commit_or_push(self, command, _changed):
        command.side_effect = lambda args, check=True: completed(args)
        self.assertFalse(publication.commit_and_push(self.counts, 4, "main"))
        commands = [item.args[0] for item in command.call_args_list]
        self.assertFalse(any(item[:2] == ["git", "commit"] for item in commands))
        self.assertFalse(any(item[:2] == ["git", "push"] for item in commands))

    @patch.object(publication, "changed_paths", return_value={"data/private/profile.json"})
    def test_output_outside_allowlist_fails_before_staging(self, _changed):
        with self.assertRaisesRegex(publication.PublicationError, "outside the public output allowlist"):
            publication.commit_and_push(self.counts, 4, "main")

    @patch.object(publication, "changed_paths", return_value={"data/spacex/processed/jobs_latest.csv"})
    @patch.object(publication, "run")
    def test_push_failure_preserves_commit_and_gives_nonforce_recovery(self, command, _changed):
        def behavior(args, check=True):
            if args[:2] == ["git", "diff"]:
                return completed(args, 1)
            if args[:2] == ["git", "push"]:
                raise publication.PublicationError("denied")
            if args[:2] == ["git", "rev-parse"]:
                return completed(args, stdout="abc123\n")
            return completed(args)
        command.side_effect = behavior
        with self.assertRaisesRegex(publication.PublicationError, "abc123 was preserved") as raised:
            publication.commit_and_push(self.counts, 4, "main")
        self.assertIn("without force", str(raised.exception))


    @patch.object(publication, "run", return_value=completed([], returncode=1))
    def test_untracked_allowlist_is_rejected_before_collection(self, command):
        with self.assertRaisesRegex(publication.PublicationError, "reviewed and tracked"):
            publication.require_tracked_allowlist()
        self.assertEqual(command.call_args.args[0][:4], ["git", "ls-files", "--error-unmatch", "--"])

    def test_sms_outputs_are_allowlisted_and_tracked_only_for_automated_source(self):
        repo = Path(__file__).resolve().parents[1]
        sms_paths = {
            f"data/sms-group/processed/{name}" for name in COMMON_OUTPUTS
        } | {"data/sms-group/processed/acquisition.json"}
        self.assertTrue(sms_paths.issubset(publication.OUTPUT_ALLOWLIST))

        manual_source = dict(get_source("sms-group"), acquisition_mode="manual_discovery")
        with patch.object(publication, "sources", return_value=[manual_source]):
            self.assertTrue(
                sms_paths.isdisjoint(publication.output_allowlist())
            )

        tracked = set(subprocess.check_output(
            ["git", "ls-files", "--", "data"], cwd=repo, text=True
        ).splitlines())
        expected_data = set(publication.OUTPUT_ALLOWLIST)
        self.assertEqual(expected_data, tracked)

    @unittest.skipUnless(
        os.environ.get("GITHUB_EVENT_NAME") == "pull_request",
        "Pull request path-scope check runs in GitHub Actions",
    )
    def test_pull_request_changes_only_reviewed_non_sensitive_paths(self):
        repo = Path(__file__).resolve().parents[1]
        changed = set(subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            cwd=repo,
            text=True,
        ).splitlines())
        expected = {
            ".github/workflows/industrial-source-ci.yml",
            ".github/workflows/hostinger-scheduler-ci.yml",
            "configs/sources.json",
            "data/source_status.json",
            "data/sms-group/processed/acquisition.json",
            "data/sms-group/processed/department_summary.csv",
            "data/sms-group/processed/job_changes.csv",
            "data/sms-group/processed/job_details.csv",
            "data/sms-group/processed/job_history.csv",
            "data/sms-group/processed/jobs_latest.csv",
            "data/sms-group/processed/location_summary.csv",
            "docs/INDUSTRIAL_EMPLOYER_FEASIBILITY_2026-10-21.md",
            "docs/public_data_publication.md",
            "jobtracker/acquisition.py",
            "scripts/audit_public_data.py",
            "scripts/publish_public_data.py",
            "tests/test_dvinci.py",
            "tests/test_public_data_audit.py",
            "tests/test_publication.py",
        }
        self.assertEqual(expected, changed)
        sensitive_path_terms = (
            "private_profiles", "credentials", "secrets", "cookies", "sessions",
        )
        self.assertFalse(any(
            term in path.lower()
            for path in changed
            for term in sensitive_path_terms
        ))


class GitPreparationTests(unittest.TestCase):
    @patch.object(publication, "changed_paths", return_value={"README.md"})
    @patch.object(publication, "run", return_value=completed([], stdout="main\n"))
    def test_dirty_worktree_fails_before_fetch(self, command, _changed):
        with self.assertRaisesRegex(publication.PublicationError, "existing worktree changes"):
            publication.git_prepare("main")
        commands = [item.args[0] for item in command.call_args_list]
        self.assertFalse(any(item[:2] == ["git", "fetch"] for item in commands))

    @patch.object(publication, "changed_paths", return_value=set())
    @patch.object(publication, "run")
    def test_diverged_history_fails_before_pull(self, command, _changed):
        def behavior(args, check=True):
            if args[:3] == ["git", "branch", "--show-current"]:
                return completed(args, stdout="main\n")
            if args[:2] == ["git", "rev-list"]:
                return completed(args, stdout="1 1\n")
            return completed(args)
        command.side_effect = behavior
        with self.assertRaisesRegex(publication.PublicationError, "diverges"):
            publication.git_prepare("main")
        commands = [item.args[0] for item in command.call_args_list]
        self.assertFalse(any(item[:2] == ["git", "pull"] for item in commands))


class OrchestrationTests(unittest.TestCase):
    def test_provider_failure_classification_is_parsed(self):
        output = (
            'traceback\nPROVIDER_FAILURE: {"classification": '
            '"upstream_access_challenge", "reason": "HTTP 202"}\n'
        )
        self.assertEqual(
            {"failure_classification": "upstream_access_challenge", "reason": "HTTP 202"},
            publication.classified_provider_failure(output),
        )

    def test_failed_source_restores_partial_tracked_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            processed = repo / "data/tesla/processed"
            processed.mkdir(parents=True)
            latest = processed / "jobs_latest.csv"
            acquisition = processed / "acquisition.json"
            latest.write_text("last-known-good\n", encoding="utf-8")
            acquisition.write_text('{"status":"success"}\n', encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
            latest.write_text("partial-current-run\n", encoding="utf-8")
            acquisition.write_text(
                '{"status":"failed","coverage_complete":false,"reason":"fixture failure"}\n',
                encoding="utf-8",
            )
            source = {
                "id": "tesla", "company": "Tesla",
                "acquisition_mode": "existing_provider",
            }
            real_run = publication.run

            def behavior(args, check=True):
                if args[:3] == [publication.sys.executable, "run_pipeline.py", "--company"]:
                    return completed(args, returncode=1)
                return real_run(args, check=check)

            with patch.object(publication, "run", side_effect=behavior):
                result = publication.collect_source(repo, source, 0)

            self.assertEqual("failed", result["status"])
            self.assertFalse(result["coverage_complete"])
            self.assertEqual("last-known-good\n", latest.read_text(encoding="utf-8"))
            self.assertEqual("failed", json.loads(acquisition.read_text(encoding="utf-8"))["status"])

    def _assert_legacy_failure_does_not_block(self, source_id, company):
        failed_source = {
            "id": source_id, "company": company, "acquisition_mode": "existing_provider",
            "sector": "Technology", "tags": ["legacy"],
        }
        spacex = {
            "id": "spacex", "company": "SpaceX", "acquisition_mode": "existing_provider",
            "sector": "Space/Rocket", "tags": ["patrick"],
        }
        results = [
            publication.source_result(failed_source, "failed", False, reason="fixture failure"),
            publication.source_result(spacex, "success", True, records_written=3),
        ]
        feed_metadata = {
            "coverage_complete": True,
            "source_coverage": [{"source_id": "spacex", "coverage_complete": True}],
        }
        coverage = {"patrick_feed_coverage_complete": True}
        with patch.object(publication, "git_prepare"), \
                patch.object(publication, "require_tracked_allowlist"), \
                patch.object(
                    publication, "validate_enabled_providers",
                    return_value=[failed_source, spacex],
                ), \
                patch.object(publication, "collect_source", side_effect=results), \
                patch.object(
                    publication, "publish_patrick_feed", return_value=(3, feed_metadata),
                ) as feed, \
                patch.object(
                    publication, "write_publication_status", return_value=coverage,
                ) as status, \
                patch.object(publication, "commit_and_push", return_value=True) as commit, \
                patch("builtins.print") as output:
            self.assertTrue(publication.collect_and_publish(
                Path("."), Path("runtime"), Path("profile"), "main", "main"
            ))

        feed_results = feed.call_args.args[4]
        self.assertFalse(feed_results[source_id]["coverage_complete"])
        status.assert_called_once_with(Path("."), feed_results, feed_metadata)
        commit.assert_called_once_with({"spacex": 3}, 3, "main")
        self.assertTrue(any(
            f"{source_id}: fixture failure" in call.args[0]
            for call in output.call_args_list
        ))

    def test_neura_failure_does_not_block_publication(self):
        self._assert_legacy_failure_does_not_block("neura", "NEURA Robotics")

    def test_tesla_failure_does_not_block_publication(self):
        self._assert_legacy_failure_does_not_block("tesla", "Tesla")

    def test_jacobs_failure_does_not_block_publication(self):
        self._assert_legacy_failure_does_not_block("jacobs", "Jacobs")

    def test_failed_patrick_contributor_blocks_all_publication_stages(self):
        spacex = {
            "id": "spacex", "company": "SpaceX", "acquisition_mode": "existing_provider",
            "sector": "Space/Rocket", "tags": ["patrick"],
        }
        result = publication.source_result(spacex, "failed", False, reason="fixture failure")
        with patch.object(publication, "git_prepare") as git, \
                patch.object(publication, "require_tracked_allowlist") as tracked, \
                patch.object(publication, "validate_enabled_providers", return_value=[spacex]), \
                patch.object(publication, "collect_source", return_value=result), \
                patch.object(publication, "publish_patrick_feed") as feed, \
                patch.object(publication, "write_publication_status") as status, \
                patch.object(publication, "commit_and_push") as commit:
            with self.assertRaisesRegex(
                publication.PublicationError, "Patrick contributor.*spacex: fixture failure"
            ):
                publication.collect_and_publish(
                    Path("."), Path("runtime"), Path("profile"), "main", "main"
                )
        git.assert_called_once_with("main")
        tracked.assert_called_once()
        feed.assert_not_called()
        status.assert_not_called()
        commit.assert_not_called()

    def test_all_required_providers_succeed_and_publish(self):
        spacex = {"id": "spacex", "company": "SpaceX", "acquisition_mode": "existing_provider"}
        result = publication.source_result(spacex, "success", True, records_written=3)
        feed_metadata = {
            "coverage_complete": True,
            "source_coverage": [{"source_id": "spacex", "coverage_complete": True}],
        }
        coverage = {"patrick_feed_coverage_complete": True}
        with patch.object(publication, "git_prepare"), \
                patch.object(publication, "require_tracked_allowlist"), \
                patch.object(publication, "validate_enabled_providers", return_value=[spacex]), \
                patch.object(publication, "collect_source", return_value=result), \
                patch.object(publication, "publish_patrick_feed", return_value=(3, feed_metadata)), \
                patch.object(publication, "write_publication_status", return_value=coverage) as status, \
                patch.object(publication, "commit_and_push", return_value=True) as commit:
            self.assertTrue(publication.collect_and_publish(
                Path("."), Path("runtime"), Path("profile"), "main", "main"
            ))
        status.assert_called_once()
        commit.assert_called_once_with({"spacex": 3}, 3, "main")

    def test_incomplete_feed_blocks_status_staging_commit_and_push(self):
        spacex = {"id": "spacex", "company": "SpaceX", "acquisition_mode": "existing_provider"}
        result = publication.source_result(spacex, "success", True, records_written=3)
        feed_metadata = {"coverage_complete": False, "source_coverage": []}
        with patch.object(publication, "git_prepare"), \
                patch.object(publication, "require_tracked_allowlist"), \
                patch.object(publication, "validate_enabled_providers", return_value=[spacex]), \
                patch.object(publication, "collect_source", return_value=result), \
                patch.object(publication, "publish_patrick_feed", return_value=(3, feed_metadata)), \
                patch.object(publication, "write_publication_status") as status, \
                patch.object(publication, "commit_and_push") as commit:
            with self.assertRaisesRegex(publication.PublicationError, "feed generation was incomplete"):
                publication.collect_and_publish(
                    Path("."), Path("runtime"), Path("profile"), "main", "main"
                )
        status.assert_not_called()
        commit.assert_not_called()

    def test_required_contributor_failure_records_incomplete_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "data").mkdir()
            results = {
                "spacex": {"source_id": "spacex", "status": "success", "coverage_complete": True},
                "rocket-factory-augsburg": {
                    "source_id": "rocket-factory-augsburg", "status": "failed",
                    "coverage_complete": False, "reason": "fixture failure",
                },
            }
            metadata = {
                "coverage_complete": False,
                "source_coverage": [
                    {"source_id": "spacex", "coverage_complete": True},
                    {"source_id": "rocket-factory-augsburg", "coverage_complete": False},
                ],
            }
            coverage = publication.write_publication_status(repo, results, metadata)
            self.assertFalse(coverage["patrick_feed_coverage_complete"])
            self.assertEqual(["spacex"], coverage["published_feed_contributors"])
            self.assertEqual(
                ["rocket-factory-augsburg"], coverage["failed_or_incomplete_sources"]
            )


class SmsPublisherTests(unittest.TestCase):
    def sms_source(self):
        return get_source("sms-group")

    def sms_fetch(self):
        record = {
            "id": 701,
            "language": "en",
            "position": "Plant Reliability Engineer",
            "jobPublicationURL": (
                "https://career.sms-group.com/en/jobs/701/"
                "plant-reliability-engineer"
            ),
            "introduction": "<p>Maintain reliable plants.</p>",
            "tasks": "<p>Support plant operations.</p>",
            "profile": "<p>Engineering experience.</p>",
            "weOffer": "<p>Flexible work.</p>",
            "jobOpening": {
                "id": 9001,
                "reference": "SMS-9001",
                "company": {"name": "SMS group GmbH"},
                "location": "Duesseldorf",
                "department": {"name": "Plant Engineering"},
            },
        }
        feed = json.dumps([record]).encode()
        sitemap = (
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            "<url><loc>https://career.sms-group.com/en/jobs/701/"
            "plant-reliability-engineer</loc></url></urlset>"
        ).encode()

        def fetch(url):
            if url == self.sms_source()["adapter_config"]["url"]:
                return feed
            if url == self.sms_source()["adapter_config"]["sitemap_url"]:
                return sitemap
            raise AssertionError(f"Unexpected URL: {url}")

        return fetch

    def bootstrap_sms(self, repo):
        processed = repo / "data/sms-group/processed"
        processed.mkdir(parents=True)
        fields = {
            "jobs_latest.csv": LATEST_FIELDS,
            "job_details.csv": DETAIL_FIELDS,
            "job_history.csv": DETAIL_FIELDS + ("first_seen", "last_seen", "active"),
            "job_changes.csv": CHANGE_FIELDS,
            "department_summary.csv": ("department", "count"),
            "location_summary.csv": ("location", "count"),
        }
        for filename, header in fields.items():
            with (processed / filename).open(
                "w", newline="", encoding="utf-8"
            ) as stream:
                csv.writer(stream).writerow(header)
        (processed / "acquisition.json").write_text(
            json.dumps({
                "source_id": "sms-group",
                "status": "incomplete",
                "coverage_complete": False,
                "records_written": 0,
                "publication_status": "awaiting_first_verified_production_run",
            }),
            encoding="utf-8",
        )
        return processed

    def test_disabled_host_gate_skips_sms_without_blocking_other_sources(self):
        sms = self.sms_source()
        spacex = {
            "id": "spacex",
            "company": "SpaceX",
            "acquisition_mode": "existing_provider",
            "sector": "Space/Rocket",
            "tags": ["patrick"],
        }
        spacex_result = publication.source_result(
            spacex, "success", True, records_written=3
        )
        feed_metadata = {
            "coverage_complete": True,
            "source_coverage": [
                {"source_id": "spacex", "coverage_complete": True},
            ],
        }
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {}, clear=True), \
                patch.object(publication, "git_prepare"), \
                patch.object(publication, "require_tracked_allowlist"), \
                patch.object(
                    publication, "validate_enabled_providers",
                    return_value=[sms, spacex],
                ), \
                patch.object(
                    publication, "collect_source", return_value=spacex_result,
                ) as collect, \
                patch.object(
                    publication, "publish_patrick_feed",
                    return_value=(3, feed_metadata),
                ), \
                patch.object(
                    publication, "commit_and_push", return_value=True,
                ) as commit:
            processed = self.bootstrap_sms(Path(directory))
            previous = {
                path.name: path.read_bytes()
                for path in processed.iterdir()
            }
            result = publication.collect_and_publish(
                Path(directory), Path(directory) / "runtime",
                Path(directory) / "profile", "main", "main",
            )
            status = json.loads(
                (Path(directory) / "data/source_status.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(previous, {
                path.name: path.read_bytes() for path in processed.iterdir()
            })

        self.assertTrue(result)
        self.assertEqual(["spacex"], [
            call.args[1]["id"] for call in collect.call_args_list
        ])
        sms_status = next(
            item for item in status["sources"]
            if item["source_id"] == "sms-group"
        )
        self.assertFalse(sms_status["attempted"])
        self.assertEqual("incomplete", sms_status["status"])
        self.assertEqual(0, sms_status["records_written"])
        self.assertEqual(
            "awaiting_first_verified_production_run",
            sms_status["publication_status"],
        )
        self.assertNotIn("sms-group", status["publication"]["attempted_sources"])
        self.assertIn(
            "sms-group", status["publication"]["failed_or_incomplete_sources"]
        )
        commit.assert_called_once()

    def test_first_success_replaces_pending_bootstrap_before_publication(self):
        source = self.sms_source()
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            processed = self.bootstrap_sms(repo)
            with self.assertRaisesRegex(
                publication.PublicationError, "Required output is empty"
            ):
                publication.validate_source_dataset(
                    repo, source, collection_started=0
                )
            data_root = repo / "data"
            feed_fetch = self.sms_fetch()
            commands = []

            def run_source_command(command, check=True):
                commands.append(command)
                self.assertEqual(
                    [
                        publication.sys.executable, "-m",
                        "jobtracker.pipeline", "--source", "sms-group",
                    ],
                    command,
                )
                run_source(source, data_root, fetch=feed_fetch)
                return completed(command)

            def publish_feed(_repo, _runtime, _profile, counts, results):
                self.assertEqual({"sms-group": 1}, counts)
                self.assertEqual("success", results["sms-group"]["status"])
                with (processed / "jobs_latest.csv").open(
                    newline="", encoding="utf-8"
                ) as stream:
                    current = list(csv.DictReader(stream))
                self.assertEqual(1, len(current))
                acquisition = json.loads(
                    (processed / "acquisition.json").read_text(encoding="utf-8")
                )
                self.assertEqual("success", acquisition["status"])
                self.assertTrue(acquisition["coverage_complete"])
                return 0, {"coverage_complete": True, "source_coverage": []}

            with patch.dict(
                os.environ, {"JOB_TRACKER_ENABLE_SMS_GROUP": "1"}
            ), patch.object(publication, "git_prepare"), \
                    patch.object(publication, "require_tracked_allowlist"), \
                    patch.object(
                        publication, "validate_enabled_providers",
                        return_value=[source],
                    ), patch.object(
                        publication, "run", side_effect=run_source_command
                    ), patch.object(
                        publication, "publish_patrick_feed",
                        side_effect=publish_feed,
                    ), patch.object(
                        publication, "commit_and_push", return_value=False,
                    ):
                result = publication.collect_and_publish(
                    repo, repo / "runtime", repo / "profile", "main", "main"
                )

            self.assertFalse(result)
            self.assertEqual(1, len(commands))
            metadata = json.loads(
                (processed / "acquisition.json").read_text(encoding="utf-8")
            )
            self.assertEqual("success", metadata["status"])
            self.assertEqual(1, metadata["records_written"])
            self.assertNotIn(
                "publication_status", metadata,
                "successful collection must replace the pending bootstrap metadata",
            )
            for filename in COMMON_OUTPUTS:
                with (processed / filename).open(
                    newline="", encoding="utf-8"
                ) as stream:
                    self.assertTrue(list(csv.DictReader(stream)), filename)
            with patch.object(publication, "sources", return_value=[source]):
                self.assertEqual([], publication.patrick_contributors(repo))

    def test_blocked_sms_collection_restores_all_last_good_outputs(self):
        source = self.sms_source()
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            processed = self.bootstrap_sms(repo)
            for filename in COMMON_OUTPUTS:
                (processed / filename).write_text(
                    f"last-good-{filename}\n", encoding="utf-8"
                )
            acquisition = processed / "acquisition.json"
            acquisition.write_text(
                '{"source_id":"sms-group","status":"success",'
                '"coverage_complete":true,"records_written":1}\n',
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo, check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=repo, check=True,
            )
            subprocess.run(["git", "add", "data"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "last good fixture"],
                cwd=repo, check=True,
            )
            previous = {
                path.name: path.read_bytes()
                for path in processed.iterdir()
            }
            real_run = publication.run

            def fail_collection(command, check=True):
                if command[:4] == [
                    publication.sys.executable, "-m",
                    "jobtracker.pipeline", "--source",
                ]:
                    for filename in COMMON_OUTPUTS:
                        (processed / filename).write_text(
                            f"partial-{filename}\n", encoding="utf-8"
                        )
                    acquisition.write_text(
                        '{"source_id":"sms-group","status":"failed",'
                        '"coverage_complete":false,"records_written":0,'
                        '"reason":"HTTP 403"}\n',
                        encoding="utf-8",
                    )
                    return completed(command, returncode=1)
                return real_run(command, check=check)

            with patch.object(publication, "run", side_effect=fail_collection):
                result = publication.collect_source(
                    repo, source, time.time() - 1
                )

            self.assertEqual("failed", result["status"])
            self.assertFalse(result["coverage_complete"])
            self.assertEqual("HTTP 403", result["reason"])
            for filename, content in previous.items():
                if filename != "acquisition.json":
                    self.assertEqual(content, (processed / filename).read_bytes())
            failure = json.loads(acquisition.read_text(encoding="utf-8"))
            self.assertEqual("failed", failure["status"])
            self.assertFalse(failure["coverage_complete"])


class SchedulerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir()
        self.state_file = self.root / "state" / "state.json"
        self.state_file.parent.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def initialize(self, last_success):
        scheduler.initialize_state(
            self.state_file,
            last_success_utc=scheduler.format_utc(last_success),
        )

    def run_with_scheduler(self):
        environment = {
            "JOB_TRACKER_RUNTIME_DIR": str(self.runtime),
            "JOB_TRACKER_SCHEDULER_STATE": str(self.state_file),
        }
        with patch.dict(os.environ, environment):
            os.environ.pop("INVOCATION_ID", None)
            return publication.main()

    @patch.object(publication, "collect_and_publish")
    def test_manual_publisher_is_rejected_before_six_hours(self, collect):
        self.initialize(datetime.now(timezone.utc) - timedelta(hours=5))

        with self.assertRaisesRegex(publication.PublicationError, "not eligible before"):
            self.run_with_scheduler()

        collect.assert_not_called()
        self.assertIsNone(scheduler.read_state(self.state_file)["last_attempt_utc"])

    @patch.object(publication.fcntl, "flock", side_effect=BlockingIOError)
    @patch.object(publication, "collect_and_publish")
    def test_existing_publication_lock_rejects_manual_overlap_before_state_change(
        self,
        collect,
        flock,
    ):
        self.initialize(datetime.now(timezone.utc) - timedelta(hours=7))

        with self.assertRaisesRegex(publication.PublicationError, "Another publication run"):
            self.run_with_scheduler()

        flock.assert_called_once()
        collect.assert_not_called()
        self.assertIsNone(scheduler.read_state(self.state_file)["last_attempt_utc"])

    @patch.object(publication, "collect_and_publish", return_value=False)
    def test_successful_manual_no_change_run_resets_scheduler_interval(self, collect):
        self.initialize(datetime.now(timezone.utc) - timedelta(hours=7))

        self.assertEqual(0, self.run_with_scheduler())

        collect.assert_called_once()
        state = scheduler.read_state(self.state_file)
        self.assertEqual("success", state["last_attempt_status"])
        self.assertTrue(state["last_attempt_invocation_id"].startswith("manual-"))
        self.assertGreaterEqual(
            scheduler.eligibility_deadline(self.state_file),
            datetime.now(timezone.utc) + timedelta(hours=5, minutes=59),
        )

    @patch.object(
        publication,
        "collect_and_publish",
        side_effect=publication.PublicationError("fixture publisher failure"),
    )
    def test_failed_manual_run_records_failure_and_applies_retry_backoff(self, collect):
        self.initialize(datetime.now(timezone.utc) - timedelta(hours=7))

        with self.assertRaisesRegex(publication.PublicationError, "fixture publisher failure"):
            self.run_with_scheduler()

        collect.assert_called_once()
        state = scheduler.read_state(self.state_file)
        self.assertEqual("failed", state["last_attempt_status"])
        self.assertIsNotNone(state["last_failure_utc"])
        self.assertGreater(
            scheduler.next_attempt_after(self.state_file),
            datetime.now(timezone.utc) + timedelta(hours=5, minutes=59),
        )

    @patch.object(publication, "collect_and_publish", return_value=False)
    def test_systemd_run_uses_matching_attempt_and_records_success_once(self, collect):
        now = datetime.now(timezone.utc)
        self.initialize(now - timedelta(hours=7))
        invocation_id = "test-systemd-invocation"
        scheduler.mark_attempt(self.state_file, invocation_id, now)
        environment = {
            "JOB_TRACKER_RUNTIME_DIR": str(self.runtime),
            "JOB_TRACKER_SCHEDULER_STATE": str(self.state_file),
            "INVOCATION_ID": invocation_id,
        }

        with patch.dict(os.environ, environment):
            self.assertEqual(0, publication.main())

        collect.assert_called_once()
        state = scheduler.read_state(self.state_file)
        self.assertEqual(invocation_id, state["last_attempt_invocation_id"])
        self.assertEqual("success", state["last_attempt_status"])


if __name__ == "__main__":
    unittest.main()
