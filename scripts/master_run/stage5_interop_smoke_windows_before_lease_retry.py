"""Opt-in real Windows-to-WSL nonscientific lease/lock lifecycle smoke.

PREPARED_NOT_RUN without --run. Never executes a detector or adopts scientific
work. Uses the actual stable Windows byte lock, actual Windows owner birth and
GetPerformanceInfo measurements; Linux is limited to harmless Python fixtures.
"""
from pathlib import Path, PurePosixPath
import argparse
import json
import os
import subprocess
import time
import uuid

import atomic_iqtree_windows as A

SCOPE = "NONSCIENTIFIC_INTEROP_ONLY_NOT_BIOLOGY_OR_ADOPTION"
FIXTURES = ("exit0", "lease_expiry", "escaped_descendant")
WORK = Path(__file__).resolve().parent
WORKER = WORK / "stage5_interop_linux_fixture.py"
SUPERVISOR = WORK / "stage5_atomic_process.py"
WSL = r"C:\Windows\System32\wsl.exe"


def linux_path(path):
    path = Path(path).resolve()
    A.require(path.drive and len(path.drive) == 2 and WORK in path.parents, "Bridge files must stay beneath this chat work directory")
    return "/mnt/" + path.drive[0].lower() + "/" + "/".join(path.parts[1:])


def safe_python(value):
    pure = PurePosixPath(value)
    A.require(value.startswith("/") and pure.as_posix() == value and ".." not in pure.parts and
              not any(c in value for c in ("\x00", "\n", "\r")), "Explicit mounted Linux Python path required")
    return value


def verify_terminal(directory, fixture, nonce, code, worker_hash, supervisor_hash, owner, lock):
    terminal_path = directory / "linux/terminal.json"
    terminal = A.read_json(terminal_path)
    A.require(terminal.get("schema") == "STAGE05_INTEROP_SYNTHETIC_TERMINAL_V1" and terminal.get("scope") == SCOPE and
              terminal.get("fixture") == fixture and terminal.get("owner_nonce") == nonce and
              terminal.get("state") == "PASS_NONSCIENTIFIC_INTEROP_FIXTURE" and code == 0 and
              terminal.get("owned_closure_proven") is True and terminal.get("scientific_adoption_authorized") is False,
              "Actual nonscientific terminal/exit/closure binding failed")
    A.require(terminal.get("worker_sha256") == worker_hash and terminal.get("supervisor_sha256") == supervisor_hash,
              "Linux fixture executed different source bytes")
    actual_owner = terminal["actual_windows_owner"]
    A.require(actual_owner["owner_pid"] == owner["pid"] and actual_owner["owner_creation_filetime"] == str(owner["creation_filetime"])
              and actual_owner["workflow_lock"] == lock, "Actual cross-OS owner birth/lock identity differs")
    required = {"attempt/synthetic.launch_intent.json", "attempt/synthetic.launch.json", "attempt/synthetic.closure.json",
                "attempt/synthetic.command.json", "attempt/synthetic.stdout.txt", "attempt/synthetic.stderr.txt"}
    files = terminal.get("files", {})
    A.require(required <= set(files), "Actual native lifecycle receipts missing")
    for relative, expected in files.items():
        pure = PurePosixPath(relative)
        A.require(pure.as_posix() == relative and not pure.is_absolute() and ".." not in pure.parts and "\\" not in relative,
                  "Unsafe fixture receipt member")
        path = (directory / "linux").joinpath(*pure.parts).resolve()
        A.require((directory / "linux").resolve() in path.parents and A.sha256(path) == expected,
                  "Actual receipt/log readback hash differs")
    launch = A.read_json(directory / "linux/attempt/synthetic.launch.json")
    closure = A.read_json(directory / "linux/attempt/synthetic.closure.json")
    command = A.read_json(directory / "linux/attempt/synthetic.command.json")
    A.require(launch["command_nonce"] == closure["command_nonce"] == command["command_nonce"] == terminal["command_nonce"] and
              command["group_closure_sha256"] == A.sha256(directory / "linux/attempt/synthetic.closure.json") and
              closure["group_empty"] is True and closure["tracked_descendants_empty"] is True and
              not closure["survivors"] and not closure["unexplained_pgid_members"], "Reopened actual native closure is unproven")
    A.require(all(launch[key] == command[key] for key in ("child_pid", "child_start_ticks", "pgid", "sid", "boot_id", "argv", "identity")) and
              launch["pgid"] == launch["sid"] == launch["child_pid"] and launch["boot_id"] == closure["boot_id"] and
              closure["root_exit_code"] == command["exit_code"] == terminal["actual_native_exit_code"] and
              any(row["pid"] == launch["child_pid"] and row["start_ticks"] == launch["child_start_ticks"] for row in closure["tracked_descendants"]),
              "Actual native birth/exit semantic binding differs")
    A.require(launch["identity"] == {"scope": SCOPE, "fixture": fixture, "owner_nonce": nonce} and
              command["stdout_sha256"] == A.sha256(directory / "linux/attempt/synthetic.stdout.txt") and
              command["stderr_sha256"] == A.sha256(directory / "linux/attempt/synthetic.stderr.txt"),
              "Actual native fixture identity/log receipts differ")
    A.require(closure["termination_reason"] == command["termination_reason"], "Native termination reason differs")
    if fixture == "exit0":
        A.require(command["exit_code"] == 0 and command["termination_reason"] is None, "Harmless exit0 predicate failed")
    elif fixture == "lease_expiry":
        A.require(command["exit_code"] != 0 and "Owner lease stale or invalid" in (command["termination_reason"] or ""),
                  "Actual lease-expiry termination predicate failed")
    else:
        escaped = A.read_json(directory / "linux/escaped_leaf_identity.json")
        A.require(command["exit_code"] == 0 and command["termination_reason"] == "Root exited with surviving owned descendants" and
                  escaped["sid"] == escaped["pid"] and escaped["pgid"] != launch["pgid"] and
                  any(row["pid"] == escaped["pid"] and row["start_ticks"] == escaped["start_ticks"] for row in closure["tracked_descendants"]),
                  "Actual escaped-descendant fixture predicate failed")
    return terminal


def fixture(args, api, lock, owner, name, worker_hash, supervisor_hash):
    directory = args.output / name
    directory.mkdir()
    nonce, lease_path = uuid.uuid4().hex, directory / "owner_lease.json"
    last_resources = None
    child = None
    birth = None
    closed = False
    result = {"scope": SCOPE, "fixture": name, "state": "FAILED_NONSCIENTIFIC_FIXTURE", "owner_nonce": nonce,
              "scientific_adoption_authorized": False, "owned_closure_proven": False}
    started = time.monotonic()
    def lease(active=True):
        nonlocal last_resources
        if active:
            last_resources = api.resources([directory])
        r = last_resources or {"physical_available_bytes": 0, "commit_headroom_bytes": 0, "disk_available_bytes": {}}
        now = time.time()
        value = {"schema": "STAGE05_WINDOWS_OWNER_LEASE_V1", "nonce": nonce, "workflow_lock_held": active,
                 "workflow_lock": lock.identity, "owner_pid": owner["pid"], "owner_creation_filetime": str(owner["creation_filetime"]),
                 "measured_unix": now, "expires_unix": now + 3 if active else now,
                 "windows_available_bytes": r["physical_available_bytes"], "windows_commit_headroom_bytes": r["commit_headroom_bytes"],
                 "disk_available_bytes": r["disk_available_bytes"], "scope": SCOPE, "utc": A.utc()}
        A.atomic(lease_path, value)
        return value
    try:
        lease()
        argv = [WSL, "-d", args.distribution, "-u", "root", "--exec", args.linux_python, "-B", linux_path(WORKER),
                "--fixture", name, "--output", linux_path(directory / "linux"), "--owner-lease", linux_path(lease_path),
                "--owner-nonce", nonce, "--expected-python", args.linux_python, "--worker-sha256", worker_hash,
                "--supervisor-sha256", supervisor_hash]
        with (directory / "wsl.stdout.txt").open("wb") as out, (directory / "wsl.stderr.txt").open("wb") as err:
            child = subprocess.Popen(argv, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
            birth = api.identity(int(child._handle), child.pid, retained_image=WSL, retained_session=owner["session_id"])
            A.require(Path(birth["executable"]).resolve() == Path(WSL).resolve(), "Unexpected actual WSL client executable")
            A.atomic(directory / "wsl.launch.json", {"scope": SCOPE, "owner_nonce": nonce, "actual_client": birth, "argv": argv,
                       "worker_sha256": worker_hash, "supervisor_sha256": supervisor_hash})
            renewed = time.monotonic()
            expiry_started = False
            while child.poll() is None:
                A.require(time.monotonic() - started < 45, "Nonscientific WSL fixture exceeded45-second execution bound")
                if name == "lease_expiry" and not expiry_started and (directory / "linux/attempt/synthetic.launch.json").is_file():
                    value = A.read_json(lease_path)
                    A.atomic(directory / "deliberate_renewal_stop.json", {"scope": SCOPE, "last_active_lease": value,
                        "last_active_lease_sha256": A.sha256(lease_path), "utc": A.utc(),
                        "reason": "Deliberately stop real Windows renewal after observed actual harmless child launch"})
                    expiry_started = True
                if not expiry_started and time.monotonic() - renewed >= 0.5:
                    lease()
                    renewed = time.monotonic()
                time.sleep(0.1)
            actual_exit = api.identity(int(child._handle), child.pid, retained_image=birth["executable"], retained_session=birth["session_id"])
            A.require(actual_exit["creation_filetime"] == birth["creation_filetime"] and actual_exit["exited"] and
                      actual_exit["exit_filetime"] > actual_exit["creation_filetime"], "Actual retained WSL client exit identity differs")
        terminal = verify_terminal(directory, name, nonce, actual_exit["exit_code"], worker_hash, supervisor_hash, owner, lock.identity)
        if name == "lease_expiry":
            A.require(expiry_started and (directory / "deliberate_renewal_stop.json").is_file(), "Actual Windows expiry was not induced")
            stopped = A.read_json(directory / "deliberate_renewal_stop.json")
            A.require(stopped["last_active_lease_sha256"] == A.sha256(lease_path) and
                      stopped["last_active_lease"]["expires_unix"] <= time.time(), "Real last Windows lease did not expire unchanged")
        closed = True
        result.update(state="PASS_NONSCIENTIFIC_INTEROP_FIXTURE", owned_closure_proven=True, actual_wsl_client_exit=actual_exit,
                      terminal_sha256=A.sha256(directory / "linux/terminal.json"), actual_native_exit_code=terminal["actual_native_exit_code"])
    except BaseException as error:
        result["error"] = type(error).__name__ + ": " + str(error)
        try:
            lease(False)
        except BaseException as failure:
            result["lease_invalidation_error"] = str(failure)
        if child is not None and child.poll() is None:
            try:
                child.wait(timeout=12)
            except subprocess.TimeoutExpired:
                result["closure"] = "UNPROVEN_STOP_NO_FURTHER_FIXTURE_OR_BIOLOGY"
        if not closed:
            A.atomic(args.output / "INTEROP_UNPROVEN_STOP.json", {**result,
                "action": "Root must reconcile exact WSL/native closure before any further scientific launch; no process-wide kill was attempted."})
    finally:
        try:
            lease(False)
        except BaseException as failure:
            result["final_lease_invalidation_error"] = str(failure)
        result["elapsed_seconds"] = time.monotonic() - started
        for name in ("stdout", "stderr"):
            path = directory / ("wsl." + name + ".txt")
            if path.is_file():
                result["wsl_" + name + "_sha256"] = A.sha256(path)
        A.atomic(directory / "result.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--linux-python", required=True, type=safe_python)
    p.add_argument("--distribution", default="Ubuntu")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--supervisor-sha256")
    p.add_argument("--windows-api-sha256")
    p.add_argument("--run", action="store_true")
    args = p.parse_args()
    A.require(WORKER.is_file() and SUPERVISOR.is_file(), "Prepared fixture/supervisor source missing")
    args.output = args.output.resolve()
    A.require(WORK in args.output.parents and not args.output.exists(), "New output spool beneath this chat work directory required")
    worker_hash, supervisor_hash, windows_hash = A.sha256(WORKER), A.sha256(SUPERVISOR), A.sha256(Path(A.__file__))
    plan = {"scope": SCOPE, "state": "PREPARED_NOT_RUN", "fixtures": FIXTURES, "worker_sha256": worker_hash,
            "supervisor_sha256": supervisor_hash, "windows_api_sha256": windows_hash, "lease_ttl_seconds": 3,
            "maximum_per_fixture_seconds": 60, "scientific_adoption_authorized": False}
    if not args.run:
        print(json.dumps(plan, indent=2))
        return 0
    A.require(os.name == "nt" and args.supervisor_sha256 == supervisor_hash and args.windows_api_sha256 == windows_hash,
              "Explicit reviewed Windows API/supervisor hash pins required before actual smoke")
    args.output.mkdir(parents=True)
    api = A.Win()
    owner = api.identity(api.current(), os.getpid())
    results = []
    batch = {**plan, "state": "FAILED_NONSCIENTIFIC_INTEROP", "actual_windows_owner": owner, "results": results}
    lock = A.WorkflowLock(api)
    with lock:
        A.atomic(args.output / "actual_owner_lock.json", {"scope": SCOPE, "owner": owner, "workflow_lock": lock.identity,
                   "instruction": "No detector/model/sequence/genome task is permitted by this fixture."})
        for name in FIXTURES:
            A.require(A.sha256(SUPERVISOR) == supervisor_hash and A.sha256(Path(A.__file__)) == windows_hash and
                      A.sha256(WORKER) == worker_hash, "Reviewed fixture/supervisor/API bytes changed")
            result = fixture(args, api, lock, owner, name, worker_hash, supervisor_hash)
            results.append(result)
            if result["state"] != "PASS_NONSCIENTIFIC_INTEROP_FIXTURE":
                break
        else:
            batch["state"] = "PASS_NONSCIENTIFIC_INTEROP_ONLY"
        A.atomic(args.output / "result.json", batch)
    A.atomic(args.output / "lock_released.json", {"scope": SCOPE, "state": "EXPLICIT_OS_BYTE_UNLOCK_COMPLETED", "released": lock.released,
               "scientific_adoption_authorized": False})
    print(json.dumps(batch, indent=2))
    return 0 if batch["state"] == "PASS_NONSCIENTIFIC_INTEROP_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
