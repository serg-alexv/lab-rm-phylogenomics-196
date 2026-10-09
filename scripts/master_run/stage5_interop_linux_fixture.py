"""Nonscientific Linux half of a real Windows/WSL lock-and-lease smoke test.

Only Python exit/sleep/escaped-child fixtures are available. No detector,
sequence, accession, model database or scientific output is accepted.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

import stage5_atomic_process as P

SCOPE = "NONSCIENTIFIC_INTEROP_ONLY_NOT_BIOLOGY_OR_ADOPTION"
FIXTURES = ("exit0", "lease_expiry", "escaped_descendant")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def child(role, identity_output):
    P.require(sys.platform == "linux", "Harmless fixture requires Linux")
    identity_output = Path(identity_output)
    record = P.proc_record(os.getpid())
    P.require(record is not None, "Harmless child identity missing")
    P.atomic_json(identity_output, {"scope": SCOPE, "role": role, "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(), **record})
    if role == "exit0":
        time.sleep(0.5)
        print("NONSCIENTIFIC_EXIT_ZERO", flush=True)
    elif role in ("sleep", "escaped_leaf"):
        time.sleep(20)
    elif role == "escaped_parent":
        leaf = identity_output.with_name("escaped_leaf_identity.json")
        subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--harmless-child", "escaped_leaf",
                          "--identity-output", str(leaf)], start_new_session=True)
        deadline = time.monotonic() + 2
        while not leaf.is_file() and time.monotonic() < deadline:
            time.sleep(0.025)
        P.require(leaf.is_file(), "Escaped harmless child did not record identity")
        # Give the real supervisor time to observe ancestry before root exit.
        time.sleep(0.7)
    return 0


def run(args):
    P.require(sys.platform == "linux", "Interop worker requires actual Linux")
    P.require(Path(sys.executable).resolve() == Path(args.expected_python).resolve(), "Unexpected actual Linux interpreter")
    P.require(sha(__file__) == args.worker_sha256 and sha(P.__file__) == args.supervisor_sha256,
              "Reviewed worker/supervisor bytes changed")
    out = args.output.resolve()
    P.require(not out.exists(), "Linux fixture output namespace must be new")
    P.require(out.parent == args.owner_lease.resolve().parent, "Keep worker files beside the scoped Windows lease")
    out.mkdir()
    policy = {"windows_reserve_bytes": 256 * 2**20, "incremental_windows_requirement_bytes": 64 * 2**20,
              "commit_requirement_bytes": 128 * 2**20, "linux_job_requirement_bytes": 64 * 2**20,
              "linux_reserve_bytes": 64 * 2**20, "minimum_disk_free_bytes": 32 * 2**20,
              "resource_wait_seconds": 0, "lease_max_age_seconds": 3, "command_timeout_seconds": 30,
              "sampled_rss_stop_bytes": 256 * 2**20, "termination_grace_seconds": 2, "drain_timeout_seconds": 4}
    supervisor = None
    error = None
    result = {"schema": "STAGE05_INTEROP_SYNTHETIC_TERMINAL_V1", "scope": SCOPE, "fixture": args.fixture,
              "owner_nonce": args.owner_nonce, "state": "FAILED_NONSCIENTIFIC_FIXTURE", "owned_closure_proven": False,
              "worker_sha256": sha(__file__), "supervisor_sha256": sha(P.__file__),
              "actual_python": sys.executable, "actual_python_sha256": sha(Path(sys.executable).resolve()),
              "scientific_adoption_authorized": False, "policy": policy, "files": {}}
    def deadline(signum, frame):
        raise P.Fatal("Nonscientific Linux fixture wall-clock deadline expired")
    previous = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 50)
    try:
        initial = P.check_lease(args.owner_lease, args.owner_nonce, policy)
        result["actual_windows_owner"] = {key: initial[key] for key in ("owner_pid", "owner_creation_filetime", "workflow_lock")}
        P.atomic_json(out / "initial_actual_windows_lease.json", initial)
        supervisor = P.Supervisor(args.owner_lease, args.owner_nonce, policy, out, sha)
        native_args = SimpleNamespace(output=out, environment=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                            OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", LC_ALL="C"))
        role = {"exit0": "exit0", "lease_expiry": "sleep", "escaped_descendant": "escaped_parent"}[args.fixture]
        argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--harmless-child", role,
                "--identity-output", str(out / "harmless_root_identity.json")]
        try:
            supervisor.execute(native_args, out / "attempt", "synthetic", argv, out,
                               {"scope": SCOPE, "fixture": args.fixture, "owner_nonce": args.owner_nonce})
        except (P.Fatal, P.Retryable, P.Deferred) as caught:
            error = caught
        launch = P.read_json(out / "attempt/synthetic.launch.json")
        closure = P.read_json(out / "attempt/synthetic.closure.json")
        command = P.read_json(out / "attempt/synthetic.command.json")
        supervisor.assert_intent_closed(out / "attempt/synthetic.launch_intent.json")
        supervisor.assert_closed(launch)
        P.require(supervisor.native_launch_count == 1 and not supervisor.closure_unproven,
                  "Actual harmless launch/owned closure is unproven")
        P.require(command["command_nonce"] == closure["command_nonce"] == launch["command_nonce"] and
                  command["group_closure_sha256"] == sha(out / "attempt/synthetic.closure.json"), "Actual closure/command receipts differ")
        P.require(closure["group_empty"] is True and closure["tracked_descendants_empty"] is True and
                  not closure["survivors"] and not closure["unexplained_pgid_members"], "Owned harmless group/descendants remain")
        for name in ("stdout", "stderr"):
            P.require(command[name + "_sha256"] == sha(out / f"attempt/synthetic.{name}.txt"), "Actual harmless log hash differs")
        if args.fixture == "exit0":
            P.require(error is None and command["exit_code"] == 0 and closure["termination_reason"] is None,
                      "Harmless exit0 did not finish normally")
        elif args.fixture == "lease_expiry":
            P.require(isinstance(error, P.Fatal) and "Owner lease stale or invalid" in str(error) and
                      "Owner lease stale or invalid" in (closure["termination_reason"] or "") and command["exit_code"] != 0,
                      "Expected actual Windows lease-expiry shutdown was not observed")
        else:
            escaped = P.read_json(out / "escaped_leaf_identity.json")
            P.require(isinstance(error, P.Retryable) and str(error) == "Root exited with surviving owned descendants" and
                      command["exit_code"] == closure["root_exit_code"] == 0 and
                      closure["termination_reason"] == command["termination_reason"] == "Root exited with surviving owned descendants" and
                      escaped["sid"] == escaped["pid"] and escaped["pgid"] != launch["pgid"] and
                      any(x["pid"] == escaped["pid"] and x["start_ticks"] == escaped["start_ticks"] for x in closure["tracked_descendants"]),
                      "Escaped harmless descendant was not retained and closed")
        result.update(state="PASS_NONSCIENTIFIC_INTEROP_FIXTURE", owned_closure_proven=True,
                      expected_exception=None if error is None else type(error).__name__ + ": " + str(error),
                      actual_native_exit_code=command["exit_code"], command_nonce=command["command_nonce"])
    except BaseException as caught:
        result["error"] = type(caught).__name__ + ": " + str(caught)
        result["owned_closure_proven"] = bool(supervisor and supervisor.native_launch_count == 1 and not supervisor.closure_unproven)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        result["files"] = {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}
        P.atomic_json(out / "terminal.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["state"] == "PASS_NONSCIENTIFIC_INTEROP_FIXTURE" else 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--harmless-child", choices=("exit0", "sleep", "escaped_parent", "escaped_leaf"))
    p.add_argument("--identity-output", type=Path)
    p.add_argument("--fixture", choices=FIXTURES)
    p.add_argument("--output", type=Path)
    p.add_argument("--owner-lease", type=Path)
    p.add_argument("--owner-nonce")
    p.add_argument("--expected-python")
    p.add_argument("--worker-sha256")
    p.add_argument("--supervisor-sha256")
    a = p.parse_args()
    if a.harmless_child:
        P.require(a.identity_output is not None, "Harmless identity output required")
        return child(a.harmless_child, a.identity_output)
    P.require(all(getattr(a, key) is not None for key in ("fixture", "output", "owner_lease", "owner_nonce", "expected_python", "worker_sha256", "supervisor_sha256")),
              "Explicit actual owner/fixture/source arguments required")
    return run(a)


if __name__ == "__main__":
    raise SystemExit(main())
