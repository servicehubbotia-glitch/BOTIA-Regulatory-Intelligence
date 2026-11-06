import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.demo_watch import EXAMPLES, replay


ROOT = EXAMPLES.parent
SCRIPT = ROOT / "scripts" / "demo_watch.py"
WATCHERS = EXAMPLES / "sample-watchers.json"
OBSERVATIONS = EXAMPLES / "sample-observations.json"
REPORT = EXAMPLES / "sample-report.json"


class ReplayTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.registry = json.loads(WATCHERS.read_bytes())
        self.capture = json.loads(OBSERVATIONS.read_bytes())

    def run_fixture(self):
        registry_path = self.folder / "watchers.json"
        capture_path = self.folder / "observations.json"
        registry_path.write_bytes(json.dumps(self.registry).encode())
        capture_path.write_bytes(json.dumps(self.capture).encode())
        return replay(registry_path, capture_path)

    def bulletin(self):
        return next(r for r in self.run_fixture()["results"] if r["watcher_id"] == "additives-bulletin")

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args], cwd=self.folder, capture_output=True
        )

    def test_three_outcomes_and_actions(self):
        report = self.run_fixture()
        rows = {r["watcher_id"]: (r["status"], r["next_action"]) for r in report["results"]}
        self.assertEqual(rows, {
            "additives-bulletin": ("SIN_CAMBIOS", "retain_last_observation"),
            "labelling-standard": ("VERSION_NUEVA", "request_editorial_review"),
            "packaging-guidance": ("CONSULTA_FALLIDA", "investigate_and_retry"),
        })
        self.assertEqual(report["counts"], {status: 1 for status, _ in rows.values()})

    def test_source_error_does_not_block_other_rows(self):
        self.capture["observations"]["additives-bulletin"] = {"error": "unavailable"}
        report = self.run_fixture()
        self.assertEqual(report["counts"]["CONSULTA_FALLIDA"], 2)
        self.assertEqual(report["counts"]["VERSION_NUEVA"], 1)
        self.assertIsNone(self.bulletin()["observed_release"])

    def test_missing_record_preserves_previous_observation(self):
        del self.capture["observations"]["additives-bulletin"]
        row = self.bulletin()
        self.assertEqual((row["status"], row["reason"]), ("CONSULTA_FALLIDA", "missing_or_invalid_observation"))
        self.assertEqual(row["last_seen"], "2026-09-01")

    def test_document_mismatch(self):
        self.capture["observations"]["additives-bulletin"]["document"] = "DEMO-OTHER"
        self.assertEqual(self.bulletin()["reason"], "document_mismatch")

    def test_malformed_regressive_and_future_releases(self):
        for value, reason in [
            ("2026-09-31", "invalid_release_date"), (20260901, "invalid_release_date"),
            ("20260901", "invalid_release_date"), (None, "invalid_release_date"),
            ("2026-08-31", "regressive_release"), ("2026-11-02", "future_release"),
        ]:
            with self.subTest(value=value):
                self.capture["observations"]["additives-bulletin"]["release"] = value
                row = self.bulletin()
                self.assertEqual((row["status"], row["reason"]), ("CONSULTA_FALLIDA", reason))

    def test_error_payload_does_not_echo_arbitrary_values(self):
        for row in [{"error": "some raw message"}, {"error": "timeout", "release": "2026-09-01"}]:
            with self.subTest(row=row):
                self.capture["observations"]["additives-bulletin"] = row
                self.assertEqual(self.bulletin()["reason"], "invalid_response")

    def test_unknown_watcher_rejected(self):
        self.capture["observations"]["unexpected"] = {"error": "timeout"}
        with self.assertRaisesRegex(ValueError, "unknown watcher"):
            self.run_fixture()

    def test_ambiguous_duplicate_json_keys_rejected(self):
        path = self.folder / "ambiguous.json"
        path.write_bytes(b'{"kind":"synthetic-watchers-v1","watchers":{},"watchers":{}}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            replay(path, OBSERVATIONS)

    def test_invalid_baseline_rejected(self):
        for value in ["2026-11-02", "not-a-date", None]:
            with self.subTest(value=value):
                self.registry["watchers"]["additives-bulletin"]["last_seen"] = value
                with self.assertRaises(ValueError):
                    self.run_fixture()

    def test_inputs_stay_unchanged_and_hashes_match(self):
        before = [p.read_bytes() for p in (WATCHERS, OBSERVATIONS)]
        with patch("socket.socket", side_effect=AssertionError("unexpected socket")):
            result = replay(WATCHERS, OBSERVATIONS)
        self.assertEqual(before, [p.read_bytes() for p in (WATCHERS, OBSERVATIONS)])
        self.assertEqual(result["input_sha256"], dict(zip(
            ["watchers", "observations"], [hashlib.sha256(raw).hexdigest() for raw in before]
        )))

    def test_cli_replays_identical_bytes_from_another_directory(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, REPORT.read_bytes())
        self.assertEqual(self.cli().stdout, result.stdout)
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_verify_checks_exact_bytes_and_detects_drift(self):
        self.assertEqual(self.cli("--verify", REPORT).returncode, 0)
        changed = self.folder / "changed.json"
        changed.write_bytes(REPORT.read_bytes() + b" ")
        self.assertEqual(self.cli("--verify", changed).returncode, 1)

    def test_cli_reports_unreadable_or_malformed_input_without_partial_report(self):
        broken = self.folder / "broken.json"
        for raw in (None, b"{", b"[]", b"{}", b"\xff"):
            with self.subTest(raw=raw):
                if raw is not None:
                    broken.write_bytes(raw)
                proc = self.cli("--observations", broken)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, b"")
                self.assertIn(b"Cannot replay", proc.stderr)


if __name__ == "__main__":
    unittest.main()
