"""One-shot, exact-handle cleanup of idle optional MCP services on WD."""
import ctypes as c
from ctypes import wintypes as w
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent / 'bootstrap'
HERE.mkdir(exist_ok=True)
PS = r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
K = c.WinDLL('kernel32', use_last_error=True)
K.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
K.OpenProcess.restype = w.HANDLE
K.CloseHandle.argtypes = [w.HANDLE]
K.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
K.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
K.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
K.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
K.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]

class Memory(c.Structure):
    _fields_ = [('length', w.DWORD), ('load', w.DWORD)] + [(n, c.c_ulonglong) for n in (
        'total_physical', 'available_physical', 'process_commit_limit', 'process_commit_headroom',
        'total_virtual', 'available_virtual', 'extended_virtual')]

class Performance(c.Structure):
    _fields_ = [('cb', w.DWORD)] + [(n, c.c_size_t) for n in (
        'CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable',
        'SystemCache', 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')]
    _fields_ += [(n, w.DWORD) for n in ('HandleCount', 'ProcessCount', 'ThreadCount')]

P = c.WinDLL('psapi', use_last_error=True)
P.GetPerformanceInfo.argtypes = [c.POINTER(Performance), w.DWORD]

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def memory():
    m = Memory(); m.length = c.sizeof(m)
    if not K.GlobalMemoryStatusEx(c.byref(m)):
        raise c.WinError(c.get_last_error())
    p = Performance(); p.cb = c.sizeof(p)
    if not P.GetPerformanceInfo(c.byref(p), c.sizeof(p)):
        raise c.WinError(c.get_last_error())
    return {'utc': now(), **{n: int(getattr(m, n)) for n, _ in m._fields_},
        'system_commit_limit': p.CommitLimit * p.PageSize,
        'system_committed': p.CommitTotal * p.PageSize,
        'system_commit_headroom': (p.CommitLimit - p.CommitTotal) * p.PageSize}

def inventory():
    script = '''$all=Get-CimInstance Win32_Process; @($all | ForEach-Object {
    [pscustomobject]@{pid=$_.ProcessId;ppid=$_.ParentProcessId;name=$_.Name;
    image=$_.ExecutablePath;argv=$_.CommandLine;
    born=if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToFileTimeUtc()}else{0};
    cpu=([long]$_.UserModeTime+[long]$_.KernelModeTime);ws=[long]$_.WorkingSetSize}
    }) | ConvertTo-Json -Compress'''
    return json.loads(subprocess.check_output([PS, '-NoProfile', '-Command', script], encoding='utf-8', timeout=30))

def times(handle):
    vals = [w.FILETIME() for _ in range(4)]
    if not K.GetProcessTimes(handle, *(c.byref(v) for v in vals)):
        raise c.WinError(c.get_last_error())
    return [v.dwLowDateTime | (v.dwHighDateTime << 32) for v in vals]

def image(handle):
    buf = c.create_unicode_buffer(32768); size = w.DWORD(len(buf))
    if not K.QueryFullProcessImageNameW(handle, 0, buf, c.byref(size)):
        raise c.WinError(c.get_last_error())
    return buf.value

def category(row, rows):
    argv = row.get('argv') or ''; exe = (row.get('image') or '').lower()
    parent = next((r for r in rows if r['pid'] == row['ppid']), {})
    parent_argv = parent.get('argv') or ''
    if row['name'] == 'python.exe' and exe in {
        r'C:\Users\wheel\.codex\cache\ngs-analysis-workbench\venvs\0.2.10\Scripts\python.exe'.lower(),
        r'C:\Users\wheel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'.lower(),
    } and any(argv.rstrip().endswith('-m ' + m) for m in ('ngs_app_mcp', 'ngs_compute_mcp', 'ngs_workbench_mcp')):
        return 'optional_ngs_mcp'
    if row['name'] == 'node.exe' and exe == r'C:\Program Files\nodejs\node.exe'.lower() and 'xcodebuildmcp\\build\\cli.js' in argv and argv.rstrip().endswith(' mcp'):
        return 'unused_xcode_mcp_on_windows'
    if row['name'] == 'node.exe' and exe.startswith((r'C:\Users\wheel\AppData\Local\OpenAI\Codex\runtimes\cua_node' + '\\').lower()):
        if '\\sequence-viewer\\0.1.51\\launch_node.cmd' in parent_argv and './dist/server.mjs' in argv:
            return 'unused_sequence_viewer_mcp'
        if '\\rosalind\\0.2.10-research-preview\\' in parent_argv and './mcp/server.cjs --stdio' in argv:
            return 'unused_rosalind_mcp'
        if 'scripts\\launch_code_review_mcp.cmd' in parent_argv and './server.mjs' in argv:
            return 'unused_code_review_mcp'
    return None

def main():
    receipt = {'utc': now(), 'authority': 'Direct human resource cleanup authorization in current chat',
        'policy': 'Allowlisted optional idle MCP leaf services only; retained exact OS handles and fresh child/CPU checks',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'before': memory(), 'rows': []}
    first = inventory(); handles = []
    try:
        for row in first:
            kind = category(row, first)
            if not kind or any(r['ppid'] == row['pid'] for r in first):
                continue
            handle = K.OpenProcess(0x1000 | 0x100000 | 1, False, row['pid'])
            if not handle:
                continue
            birth, _, kernel, user = times(handle)
            if abs(birth - row['born']) >= 10 or image(handle).lower() != row['image'].lower():
                K.CloseHandle(handle); continue
            handles.append((row, kind, handle, birth, kernel + user))
        time.sleep(10)
        fresh = inventory()
        for original, kind, handle, birth, cpu in handles:
            result = {'pid': original['pid'], 'creation_filetime': birth, 'category': kind, 'stopped': False}
            current = next((r for r in fresh if r['pid'] == original['pid']), None)
            exact = current and all(current[k] == original[k] for k in ('born', 'image', 'argv', 'cpu'))
            children = any(r['ppid'] == original['pid'] for r in fresh)
            measured = times(handle)
            if not exact or children or measured[0] != birth or measured[2] + measured[3] != cpu or K.WaitForSingleObject(handle, 0) != 258:
                result['skip'] = 'Identity, activity, exit, or child state changed'
            else:
                final = inventory()
                current = next((r for r in final if r['pid'] == original['pid']), None)
                if not current or any(current[k] != original[k] for k in ('born', 'image', 'argv', 'cpu')) or any(r['ppid'] == original['pid'] for r in final):
                    result['skip'] = 'Final exact identity/activity/child check changed'
                elif not K.TerminateProcess(handle, 0xe0440012):
                    result['skip'] = 'Termination denied'; result['winerror'] = c.get_last_error()
                else:
                    wait = K.WaitForSingleObject(handle, 5000); code = w.DWORD()
                    if wait != 0 or not K.GetExitCodeProcess(handle, c.byref(code)):
                        raise RuntimeError('Exact process exit receipt unavailable')
                    result.update(stopped=True, exit_code=code.value, observed_exit_filetime=times(handle)[1])
            receipt['rows'].append(result)
    finally:
        for _, _, handle, _, _ in handles:
            K.CloseHandle(handle)
        receipt['after'] = memory()
        receipt['stopped_count'] = sum(r['stopped'] for r in receipt['rows'])
        receipt['scientific_processes_stopped'] = 0
        receipt['files_deleted'] = 0
        target = HERE / ('resource_cleanup_' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
        target.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'receipt': str(target), 'stopped_count': receipt['stopped_count'], 'before': receipt['before'], 'after': receipt['after']}))

if __name__ == '__main__':
    main()
