"""Small Linux process-group supervisor; no scientific methods or searches."""
from __future__ import annotations
from pathlib import Path
import ctypes, datetime, json, os, signal, subprocess, time, uuid


class Fatal(RuntimeError):
    pass


class Retryable(RuntimeError):
    pass


class Deferred(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise Fatal(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def proc_record(pid, proc_root=Path('/proc')):
    try:
        text = (proc_root / str(pid) / 'stat').read_text()
        rest = text.rsplit(')', 1)[1].split()
        return {'pid': int(pid), 'state': rest[0], 'ppid': int(rest[1]),
                'pgid': int(rest[2]), 'sid': int(rest[3]), 'start_ticks': rest[19]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def proc_table(proc_root=Path('/proc')):
    result = {}
    for directory in proc_root.iterdir():
        if directory.name.isdigit():
            record = proc_record(directory.name, proc_root)
            if record:
                result[record['pid']] = record
    return result


def group_members(pgid, table=None):
    table = proc_table() if table is None else table
    return [record for record in table.values() if record['pgid'] == pgid]


def verified_pidfd(record):
    """Retain a kernel process handle only across matching observed births."""
    before = proc_record(record['pid'])
    if not before or before['start_ticks'] != record['start_ticks']:
        return None
    try:
        fd = os.pidfd_open(record['pid'], 0)
    except ProcessLookupError:
        return None
    after = proc_record(record['pid'])
    if not after or after['start_ticks'] != record['start_ticks']:
        os.close(fd)
        return None
    return fd


def check_lease(path, nonce, policy, now=None):
    now = time.time() if now is None else now
    lease = read_json(path)
    require(lease.get('schema') == 'STAGE05_WINDOWS_OWNER_LEASE_V1', 'Unknown owner lease schema')
    require(lease.get('nonce') == nonce and lease.get('workflow_lock_held') is True,
            'Owner nonce/declared shared-lock ownership differs')
    require(isinstance(lease.get('owner_pid'), int) and lease['owner_pid'] > 0
            and isinstance(lease.get('owner_creation_filetime'), str)
            and lease['owner_creation_filetime'].isdigit(), 'Exact Windows owner identity missing')
    issued, expires = lease.get('measured_unix'), lease.get('expires_unix')
    require(type(issued) in (int, float) and type(expires) in (int, float)
            and issued <= now + 2 and 0 <= now - issued <= policy['lease_max_age_seconds']
            and now < expires <= issued + policy['lease_max_age_seconds'], 'Owner lease stale or invalid')
    for field in ['windows_available_bytes', 'windows_commit_headroom_bytes']:
        require(type(lease.get(field)) is int and lease[field] >= 0, 'Owner resource measurement absent')
    disks = lease.get('disk_available_bytes')
    require(isinstance(disks, dict) and disks
            and all(isinstance(volume, str) and volume.strip()
                    and type(free) is int and free >= 0 for volume, free in disks.items()),
            'Owner actual Windows volume disk measurements absent/invalid')
    return lease


def linux_available():
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name, value = line.split(':', 1)
        values[name] = int(value.strip().split()[0]) * 1024
    require('MemAvailable' in values, 'Linux MemAvailable is unavailable')
    return values['MemAvailable']


class Supervisor:
    def __init__(self, lease_path, nonce, policy, output, digest):
        self.lease_path, self.nonce, self.policy = Path(lease_path), nonce, policy
        self.output, self.digest = Path(output), digest
        self.boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        initial_owner = check_lease(self.lease_path, self.nonce, self.policy)
        self.owner_identity = (initial_owner['owner_pid'], initial_owner['owner_creation_filetime'])
        self.last_failure = None
        self.closure_unproven = False
        self.native_launch_count = 0
        self.prelaunch_check = None
        self.runner_pid = os.getpid()
        libc = ctypes.CDLL(None, use_errno=True)
        require(libc.prctl(36, 1, 0, 0, 0) == 0, 'Linux child-subreaper activation failed')
        require(hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'),
                'Kernel-backed pidfd process signalling is required')
        probe = os.pidfd_open(self.runner_pid, 0)
        try:
            signal.pidfd_send_signal(probe, 0, None, 0)
        finally:
            os.close(probe)

    def check_owner(self):
        lease = check_lease(self.lease_path, self.nonce, self.policy)
        require((lease['owner_pid'], lease['owner_creation_filetime']) == self.owner_identity,
                'Windows lock-owner birth identity changed across lease renewal')
        return lease

    def admission(self, directory):
        started = time.monotonic()
        while True:
            lease = self.check_owner()
            available = linux_available()
            free = __import__('shutil').disk_usage(directory).free
            windows_disks_sufficient = all(value >= self.policy['minimum_disk_free_bytes']
                                           for value in lease['disk_available_bytes'].values())
            enough = (lease['windows_available_bytes'] >= self.policy['windows_reserve_bytes']
                      + self.policy['incremental_windows_requirement_bytes']
                      and lease['windows_commit_headroom_bytes'] >= self.policy['commit_requirement_bytes']
                      and available >= self.policy['linux_job_requirement_bytes'] + self.policy['linux_reserve_bytes']
                      and free >= self.policy['minimum_disk_free_bytes']
                      and windows_disks_sufficient)
            value = {'utc': utc(), 'linux_available_bytes': available, 'disk_free_bytes': free,
                     'windows_disks_sufficient': windows_disks_sufficient,
                     'windows_owner_lease': lease, 'owner_lease_file_sha256': self.digest(self.lease_path),
                     'policy': self.policy, 'admitted': enough, 'wait_seconds': time.monotonic() - started}
            atomic_json(directory / 'latest_admission.json', value)
            if enough:
                atomic_json(directory / 'admission.json', value)
                return value
            if time.monotonic() - started >= self.policy['resource_wait_seconds']:
                raise Deferred('Bounded resource admission expired; no native child launched')
            time.sleep(min(2, max(0.01, self.policy['resource_wait_seconds'] - (time.monotonic() - started))))

    def assert_closed(self, launch):
        try:
            self._assert_closed(launch)
        except BaseException:
            self.closure_unproven = True
            raise

    def _assert_closed(self, launch):
        closure = Path(launch.get('closure_path', ''))
        require(closure.is_file(), 'Previous command lacks actual closure receipt; no duplicate launch')
        value = read_json(closure)
        require(value.get('command_nonce') == launch.get('command_nonce')
                and value.get('root_exit_code') is not None and value.get('group_empty') is True
                and value.get('tracked_descendants_empty') is True, 'Previous root/group closure unproven')
        if launch.get('boot_id') == self.boot_id:
            current = proc_record(launch['child_pid'])
            require(not current or current['start_ticks'] != launch['child_start_ticks'], 'Previous exact root is still alive')
            # Conservative on a reused PGID: never signal or infer ownership.
            require(not group_members(launch['pgid']), 'Previous PGID is populated; ownership must be reconciled')
            for old in value.get('tracked_descendants', []):
                current = proc_record(old['pid'])
                require(not current or current['start_ticks'] != old['start_ticks'], 'Previous exact descendant is still alive')

    def fresh_attempt(self, directory, label):
        previous = sorted(directory.glob(label + '_attempt_*'))
        for old in previous:
            for path in old.glob('*.launch_intent.json'):
                self.assert_intent_closed(path)
            for path in old.glob('*.launch.json'):
                self.assert_closed(read_json(path))
        numbers = [int(path.name.rsplit('_', 1)[1]) for path in previous]
        return directory / (label + '_attempt_' + str(max(numbers, default=0) + 1).zfill(4)), previous

    def assert_intent_closed(self, path):
        try:
            self._assert_intent_closed(path)
        except BaseException:
            self.closure_unproven = True
            raise

    def _assert_intent_closed(self, path):
        intent = read_json(path)
        launch_path = path.with_name(path.name.replace('.launch_intent.json','.launch.json'))
        require(launch_path.is_file(), 'Previous admitted command lacks retained launch/closure; reconcile before any child')
        launch = read_json(launch_path)
        require(launch.get('command_nonce') == intent.get('command_nonce'), 'Launch intent/actual command nonce differs')
        self.assert_closed(launch)

    def execute(self, args, attempt, label, argv, cwd, identity):
        import resource
        attempt.mkdir(parents=True, exist_ok=True)
        self.admission(attempt)
        configuration_binding = self.prelaunch_check(args,cwd,argv) if self.prelaunch_check else None
        require(not (attempt / (label + '.launch.json')).exists(), 'Fresh command attempt required')
        command_nonce = uuid.uuid4().hex
        child = None
        root_pidfd = None
        launch = None
        tracked = {}
        pidfds = {}
        ownership_anomaly = []
        termination = None
        original_error = None
        sampled_rss_peak = 0
        started = time.monotonic()
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        baseline_children = {(item['pid'], item['start_ticks']) for item in proc_table().values()
                             if item['ppid'] == self.runner_pid}

        def observed():
            nonlocal sampled_rss_peak, ownership_anomaly
            table = proc_table()
            members = group_members(child.pid, table)
            # A dedicated subreaper also sees orphaned descendants that changed
            # session/group between polls. Preserve pre-existing children.
            owned = {pid for pid, ticks in tracked if pid in table and table[pid]['start_ticks'] == ticks}
            owned |= {pid for pid, item in table.items()
                                     if item['ppid'] == self.runner_pid
                                     and (pid, item['start_ticks']) not in baseline_children}
            changed = True
            while changed:
                more = {pid for pid, item in table.items() if item['ppid'] in owned}
                changed = not more <= owned
                owned |= more
            # Numeric PGID is an observation, never authority to adopt or kill.
            # An unrelated group may reuse that number after its leader exits.
            ownership_anomaly = [item for item in members if item['pid'] not in owned]
            for item in [table[pid] for pid in owned if pid in table]:
                key = (item['pid'], item['start_ticks'])
                if key not in pidfds:
                    fd = verified_pidfd(item)
                    if fd is None:
                        continue
                    pidfds[key] = fd
                tracked[key] = item
            rss = 0
            for pid, ticks in tracked:
                item = table.get(pid)
                if item and item['start_ticks'] == ticks:
                    try:
                        for line in Path('/proc', str(pid), 'status').read_text().splitlines():
                            if line.startswith('VmRSS:'):
                                rss += int(line.split()[1]) * 1024
                    except FileNotFoundError:
                        pass
            sampled_rss_peak = max(sampled_rss_peak, rss)
            return table, members, rss

        def survivors():
            table, members, _ = observed()
            exact = [table[pid] for pid, ticks in tracked if pid in table and table[pid]['start_ticks'] == ticks]
            return {item['pid']: item for item in exact}

        def reap_descendants():
            for pid, ticks in list(tracked):
                if pid == child.pid:
                    continue
                item = proc_record(pid)
                if item and item['start_ticks'] == ticks:
                    try:
                        os.waitpid(pid, os.WNOHANG)
                    except ChildProcessError:
                        pass

        def signal_retained(signum):
            for fd in set(pidfds.values()) | ({root_pidfd} if root_pidfd is not None else set()):
                try:
                    signal.pidfd_send_signal(fd, signum, None, 0)
                except ProcessLookupError:
                    pass

        def signal_owned(signum):
            try:
                observed()
            finally:
                signal_retained(signum)

        try:
            with (attempt / (label + '.stdout.txt')).open('wb') as stdout, (attempt / (label + '.stderr.txt')).open('wb') as stderr:
                # Persist intent before spawning. A crash before actual launch
                # identity retention must block every later native admission.
                self.closure_unproven = True
                atomic_json(attempt/(label+'.launch_intent.json'), {'command_nonce':command_nonce,
                    'utc':utc(),'argv':list(map(str,argv)),'boot_id':self.boot_id,
                    'scope':'PRELAUNCH_INTENT_ONLY_NOT_EXECUTION_PROOF'})
                child = subprocess.Popen(argv, cwd=cwd, env=args.environment, stdout=stdout, stderr=stderr,
                                         start_new_session=True)
                self.native_launch_count += 1
                # Do this before polling/reaping or any /proc/filesystem read.
                # Popen's unreaped child cannot have its PID reused here.
                root_pidfd = os.pidfd_open(child.pid, 0)
                record = proc_record(child.pid)
                require(record and record['pgid'] == child.pid and record['sid'] == child.pid,
                        'Actual child session/group identity missing')
                key = (record['pid'], record['start_ticks'])
                after = proc_record(child.pid)
                require(after and after['start_ticks'] == record['start_ticks'], 'Actual child birth identity changed')
                pidfds[key], tracked[key] = root_pidfd, record
                launch = {'execution': 'ACTUAL_PROCESS_STARTED', 'utc': utc(), 'runner_pid': self.runner_pid,
                          'child_pid': child.pid, 'child_start_ticks': record['start_ticks'],
                          'pgid': child.pid, 'sid': child.pid, 'boot_id': self.boot_id,
                          'command_nonce': command_nonce, 'new_process_session': True,
                          'signalling': 'VERIFIED_KERNEL_PIDFDS_ONLY',
                          'closure_path': str(attempt / (label + '.closure.json')),
                          'argv': list(map(str, argv)), 'cwd': str(cwd), 'identity': identity}
                if configuration_binding is not None:
                    launch['configuration_binding'] = configuration_binding
                atomic_json(attempt / (label + '.launch.json'), launch)
                while child.poll() is None:
                    self.check_owner()
                    _, _, rss = observed()
                    require(not ownership_anomaly, 'Numeric PGID contains unexplained processes; never adopt or signal them')
                    if time.monotonic() - started >= self.policy['command_timeout_seconds']:
                        raise Retryable('Native command runtime deadline expired')
                    if rss > self.policy['sampled_rss_stop_bytes']:
                        raise Retryable('Sampled process-tree RSS stop threshold exceeded')
                    time.sleep(0.25)
        except BaseException as error:
            original_error = error
            termination = type(error).__name__ + ': ' + str(error)
        finally:
            if child is not None:
                try:
                    # Root exit with descendants is not successful completion.
                    if child.poll() is None or survivors():
                        termination = termination or 'Root exited with surviving owned descendants'
                        signal_owned(signal.SIGTERM)
                        deadline = time.monotonic() + self.policy['termination_grace_seconds']
                        while time.monotonic() < deadline:
                            child.poll()
                            reap_descendants()
                            if child.poll() is not None and not survivors():
                                break
                            time.sleep(0.1)
                        if child.poll() is None or survivors():
                            signal_owned(signal.SIGKILL)
                    code = child.wait(timeout=self.policy['drain_timeout_seconds'])
                    deadline = time.monotonic() + self.policy['drain_timeout_seconds']
                    while time.monotonic() < deadline:
                        reap_descendants()
                        if not survivors():
                            break
                        time.sleep(0.1)
                    remaining = survivors()
                    closed = not remaining
                    closure = {'utc': utc(), 'command_nonce': command_nonce, 'boot_id': self.boot_id,
                               'root_exit_code': code, 'group_empty': not group_members(child.pid),
                               'tracked_descendants_empty': closed, 'survivors': list(remaining.values()),
                               'tracked_descendants': list(tracked.values()), 'termination_reason': termination,
                               'unexplained_pgid_members': ownership_anomaly,
                               'signalling': 'VERIFIED_KERNEL_PIDFDS_ONLY',
                               'scope_limit': 'dedicated subreaper, setsid group, exact descendants and pidfds; no cgroup isolation'}
                    atomic_json(attempt / (label + '.closure.json'), closure)
                    require(closed and closure['group_empty'] and not ownership_anomaly,
                            'Owned process group/descendant drain failed or unexplained PGID member')
                    require(launch is not None, 'Child started but launch identity could not be retained')
                    after = resource.getrusage(resource.RUSAGE_CHILDREN)
                    result = dict(launch, execution='PROCESS_EXITED', exit_code=code,
                                  elapsed_seconds=time.monotonic() - started,
                                  child_cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                                  sampled_tree_peak_rss_bytes=sampled_rss_peak,
                                  memory_measurement='sampled tree RSS; per-process RLIMIT_AS inherited; no aggregate kernel cap',
                                  termination_reason=termination, group_closure_sha256=self.digest(attempt / (label + '.closure.json')),
                                  stdout_sha256=self.digest(attempt / (label + '.stdout.txt')),
                                  stderr_sha256=self.digest(attempt / (label + '.stderr.txt')))
                    atomic_json(attempt / (label + '.command.json'), result)
                    with (args.output / 'commands.jsonl').open('a', encoding='utf-8') as stream:
                        stream.write(json.dumps(result, sort_keys=True) + '\n')
                    if code != 0 or termination:
                        self.last_failure = result
                    self.closure_unproven = False
                except BaseException as closure_error:
                    # A receipt/read/observer failure cannot grant success or
                    # leave an already retained process intentionally running.
                    signal_retained(signal.SIGKILL)
                    try:
                        child.wait(timeout=self.policy['drain_timeout_seconds'])
                    except subprocess.TimeoutExpired:
                        pass
                    self.last_failure = {'closure_failed': True, 'error': str(closure_error)}
                    self.closure_unproven = True
                    raise Fatal('Command closure/receipt failure: ' + str(closure_error)) from closure_error
                finally:
                    for fd in set(pidfds.values()) | ({root_pidfd} if root_pidfd is not None else set()):
                        os.close(fd)
        if original_error:
            if isinstance(original_error, Deferred):
                raise original_error
            if isinstance(original_error, Fatal):
                raise original_error
            if isinstance(original_error, Retryable):
                raise original_error
            raise Fatal('Unexpected execution/source/receipt failure: ' + str(original_error)) from original_error
        if termination:
            raise Retryable(termination)
        if result['exit_code'] != 0:
            raise Retryable('Native command exited nonzero after proved closure: ' + str(result['exit_code']))
        return result
