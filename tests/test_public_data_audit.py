import csv
import tempfile
import unittest
from pathlib import Path

from scripts.audit_public_data import summarize_neura_auxiliary


class NeuraAuxiliaryAuditTest(unittest.TestCase):
    def test_legacy_snapshot_does_not_require_count_parity(self):
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        ) as directory:
            auxiliary_path = Path(directory) / "jobs_structured.csv"
            current_path = Path(directory) / "jobs_latest.csv"
            with auxiliary_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(("title", "location", "company", "department"))
                writer.writerow(("Legacy role", "Metzingen", "Neura Robotics", "AI"))
            with current_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(("title", "link"))
                writer.writerow(("Current role 1", "https://example.test/1"))
                writer.writerow(("Current role 2", "https://example.test/2"))

            message = summarize_neura_auxiliary(auxiliary_path, current_path)

        self.assertIn("1 entries", message)
        self.assertIn("2 current entries", message)
        self.assertIn("Count parity is not expected", message)

    def test_legacy_snapshot_requires_its_display_fields(self):
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        ) as directory:
            auxiliary_path = Path(directory) / "jobs_structured.csv"
            current_path = Path(directory) / "jobs_latest.csv"
            auxiliary_path.write_text("title,location\nRole,Metzingen\n", encoding="utf-8")
            current_path.write_text(
                "title,link\nCurrent role,https://example.test/1\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "unexpected CSV columns"):
                summarize_neura_auxiliary(auxiliary_path, current_path)


if __name__ == "__main__":
    unittest.main()
