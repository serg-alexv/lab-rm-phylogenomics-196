"""Source/receipt negative contracts only; never launches Windows or Linux jobs."""
import json
from pathlib import Path
import tempfile
import unittest
import stage5_interop_smoke_windows as W


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        (self.path / "linux").mkdir()
        self.terminal = {"schema": "STAGE05_INTEROP_SYNTHETIC_TERMINAL_V1", "scope": W.SCOPE,
                         "fixture": "exit0", "owner_nonce": "CURRENT_SYNTHETIC_CONTRACT_ONLY", "state": "PASS_NONSCIENTIFIC_INTEROP_FIXTURE",
                         "owned_closure_proven": True, "scientific_adoption_authorized": False}

    def tearDown(self):
        self.temp.cleanup()

    def check(self, nonce="CURRENT_SYNTHETIC_CONTRACT_ONLY", code=0):
        (self.path / "linux/terminal.json").write_text(json.dumps(self.terminal))
        return W.verify_terminal(self.path, "exit0", nonce, code, "worker", "supervisor", {"pid": 1, "creation_filetime": 1}, {})

    def fake_contract_files(self):
        # Explicit fake receipts exercise rejection logic, never OS behavior.
        directory = self.path / "linux/attempt"
        directory.mkdir()
        launch = {"command_nonce": "FAKE_CONTRACT_NONCE", "child_pid": 10, "child_start_ticks": "20", "pgid": 10,
                  "sid": 10, "boot_id": "FAKE_CONTRACT_BOOT", "argv": ["CONTRACT_ONLY_NO_PROCESS"],
                  "identity": {"scope": W.SCOPE, "fixture": "exit0", "owner_nonce": self.terminal["owner_nonce"]}}
        closure = {"command_nonce": launch["command_nonce"], "root_exit_code": 0, "boot_id": launch["boot_id"],
                   "group_empty": True, "tracked_descendants_empty": True, "survivors": [], "unexplained_pgid_members": [],
                   "tracked_descendants": [{"pid": 10, "start_ticks": "20"}], "termination_reason": None}
        for name, value in (("launch_intent", {"scope": "FAKE_CONTRACT_NO_PROCESS"}), ("launch", launch), ("closure", closure)):
            (directory / ("synthetic." + name + ".json")).write_text(json.dumps(value))
        for name in ("stdout", "stderr"):
            (directory / ("synthetic." + name + ".txt")).write_text("FAKE_CONTRACT_NO_PROCESS")
        command = {**launch, "exit_code": 0, "termination_reason": None,
                   "group_closure_sha256": W.A.sha256(directory / "synthetic.closure.json"),
                   "stdout_sha256": W.A.sha256(directory / "synthetic.stdout.txt"),
                   "stderr_sha256": W.A.sha256(directory / "synthetic.stderr.txt")}
        self.terminal.update(worker_sha256="worker", supervisor_sha256="supervisor", command_nonce=launch["command_nonce"],
            actual_native_exit_code=0, actual_windows_owner={"owner_pid": 1, "owner_creation_filetime": "1", "workflow_lock": {}})
        return command

    def persist_command(self, command):
        (self.path / "linux/attempt/synthetic.command.json").write_text(json.dumps(command))
        self.terminal["files"] = {p.relative_to(self.path / "linux").as_posix(): W.A.sha256(p)
                                  for p in (self.path / "linux").rglob("*") if p.is_file()}

    def test_reject_stale_invocation(self):
        with self.assertRaisesRegex(Exception, "terminal/exit/closure"):
            self.check(nonce="OTHER")

    def test_reject_nonzero_client_even_if_receipt_claims_pass(self):
        with self.assertRaisesRegex(Exception, "terminal/exit/closure"):
            self.check(code=2)

    def test_reject_unproven_native_closure(self):
        self.terminal["owned_closure_proven"] = False
        with self.assertRaisesRegex(Exception, "terminal/exit/closure"):
            self.check()

    def test_reject_scientific_adoption_claim(self):
        self.terminal["scientific_adoption_authorized"] = True
        with self.assertRaisesRegex(Exception, "terminal/exit/closure"):
            self.check()

    def test_reject_source_pin_mismatch(self):
        self.terminal.update(worker_sha256="different", supervisor_sha256="supervisor")
        with self.assertRaisesRegex(Exception, "different source"):
            self.check()

    def test_reject_native_birth_mismatch_despite_self_consistent_file_hashes(self):
        command = self.fake_contract_files()
        command["child_start_ticks"] = "REUSED_FAKE_PID"
        self.persist_command(command)
        with self.assertRaisesRegex(Exception, "birth/exit semantic"):
            self.check()

    def test_reject_native_exit_mismatch_despite_client_exit0(self):
        command = self.fake_contract_files()
        command["exit_code"] = 1
        self.persist_command(command)
        with self.assertRaisesRegex(Exception, "birth/exit semantic"):
            self.check()

    def test_reject_command_log_pin_mismatch(self):
        command = self.fake_contract_files()
        command["stdout_sha256"] = "0" * 64
        self.persist_command(command)
        with self.assertRaisesRegex(Exception, "identity/log receipts"):
            self.check()

    def test_explicit_mounted_python_path(self):
        self.assertEqual(W.safe_python("/mnt/c/example/bin/python"), "/mnt/c/example/bin/python")
        for path in ("python", "/mnt/c/../python", "/mnt/c/python\nother", "/mnt/c//python"):
            with self.subTest(path=path), self.assertRaises(Exception):
                W.safe_python(path)


if __name__ == "__main__":
    unittest.main()
