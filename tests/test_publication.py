import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import publish_public_data as publication


def completed(command, returncode=0, stdout=""):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout)


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
    def test_noncontributing_tesla_failure_does_not_block_healthy_patrick_feed(self):
        tesla = {"id": "tesla", "company": "Tesla", "acquisition_mode": "existing_provider"}
        spacex = {"id": "spacex", "company": "SpaceX", "acquisition_mode": "existing_provider"}
        results = [
            publication.source_result(tesla, "failed", False, reason="fixture failure"),
            publication.source_result(spacex, "success", True, records_written=3),
        ]
        feed_metadata = {
            "coverage_complete": True,
            "source_coverage": [{"source_id": "spacex", "coverage_complete": True}],
        }
        with patch.object(publication, "git_prepare") as git, \
                patch.object(publication, "require_tracked_allowlist") as tracked, \
                patch.object(publication, "validate_enabled_providers", return_value=[tesla, spacex]), \
                patch.object(publication, "collect_source", side_effect=results), \
                patch.object(publication, "publish_patrick_feed", return_value=(3, feed_metadata)) as feed, \
                patch.object(publication, "write_publication_status", return_value={"patrick_feed_coverage_complete": True}) as status, \
                patch.object(publication, "commit_and_push", return_value=True) as commit:
            self.assertTrue(publication.collect_and_publish(
                Path("."), Path("runtime"), Path("profile"), "main", "main"
            ))
        git.assert_called_once_with("main")
        tracked.assert_called_once()
        published_results = feed.call_args.args[4]
        self.assertEqual("failed", published_results["tesla"]["status"])
        self.assertFalse(published_results["tesla"]["coverage_complete"])
        commit.assert_called_once_with({"spacex": 3}, 3, "main")
        status.assert_called_once()

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


if __name__ == "__main__":
    unittest.main()
