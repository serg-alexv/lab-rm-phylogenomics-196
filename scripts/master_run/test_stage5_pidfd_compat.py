"""Pure compatibility fixtures; no real pidfd, Linux, WSL or native launch."""
from pathlib import Path
import ast, ctypes, errno, types, unittest
from unittest import mock
import stage5_atomic_process as P


class Export:
    def __init__(self, result=0, error=0):
        self.result, self.error, self.calls = result, error, []

    def __call__(self, *arguments):
        self.calls.append(arguments)
        ctypes.set_errno(self.error)
        return self.result


class Compatibility(unittest.TestCase):
    def setUp(self):
        P._libc_pidfd.cache_clear()

    def tearDown(self):
        P._libc_pidfd.cache_clear()

    def test_present_stdlib_does_not_load_libc(self):
        with mock.patch.object(P.os, 'pidfd_open', return_value=41, create=True) as opened, \
             mock.patch.object(P.signal, 'pidfd_send_signal', return_value=None, create=True) as sent, \
             mock.patch.object(P.ctypes, 'CDLL') as library:
            self.assertEqual(P.open_pidfd(123), 41)
            self.assertIsNone(P.send_pidfd_signal(41, 0))
            opened.assert_called_once_with(123, 0)
            sent.assert_called_once_with(41, 0, None, 0)
            library.assert_not_called()

    def test_absent_stdlib_uses_exact_libc_abi_and_retains_export(self):
        opened, sent = Export(43), Export()
        library = types.SimpleNamespace(pidfd_open=opened, pidfd_send_signal=sent)
        with mock.patch.object(P.os, 'pidfd_open', None, create=True), \
             mock.patch.object(P.signal, 'pidfd_send_signal', None, create=True), \
             mock.patch.object(P.sys, 'platform', 'linux'), \
             mock.patch.object(P.ctypes, 'CDLL', return_value=library) as load:
            self.assertEqual(P.open_pidfd(123), 43)
            self.assertEqual(P.open_pidfd(124), 43)
            self.assertEqual(P.send_pidfd_signal(43, 0), 0)
            self.assertEqual(load.call_count, 2)
            self.assertEqual(opened.calls, [(123, 0), (124, 0)])
            self.assertEqual(sent.calls, [(43, 0, None, 0)])
            self.assertEqual(opened.argtypes, [ctypes.c_int, ctypes.c_uint])
            self.assertEqual(sent.argtypes, [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint])
            self.assertIs(sent.restype, ctypes.c_int)
            load.assert_called_with(None, use_errno=True)

    def test_mixed_python_apis_fall_back_only_for_missing_function(self):
        sent = Export()
        with mock.patch.object(P.os, 'pidfd_open', return_value=44, create=True), \
             mock.patch.object(P.signal, 'pidfd_send_signal', None, create=True), \
             mock.patch.object(P.sys, 'platform', 'linux'), \
             mock.patch.object(P.ctypes, 'CDLL', return_value=types.SimpleNamespace(pidfd_send_signal=sent)):
            self.assertEqual(P.open_pidfd(123), 44)
            P.send_pidfd_signal(44, 15)
            self.assertEqual(sent.calls, [(44, 15, None, 0)])

    def test_existing_stdlib_failure_is_not_bypassed(self):
        with mock.patch.object(P.os, 'pidfd_open', side_effect=PermissionError(errno.EPERM, 'denied'), create=True), \
             mock.patch.object(P.ctypes, 'CDLL') as library:
            with self.assertRaises(PermissionError): P.open_pidfd(123)
            library.assert_not_called()

    def test_missing_libc_or_export_fails_closed(self):
        for outcome in (OSError('unavailable'), types.SimpleNamespace()):
            P._libc_pidfd.cache_clear()
            with self.subTest(outcome=type(outcome).__name__), \
                 mock.patch.object(P.os, 'pidfd_open', None, create=True), \
                 mock.patch.object(P.sys, 'platform', 'linux'), \
                 mock.patch.object(P.ctypes, 'CDLL', side_effect=outcome if isinstance(outcome, Exception) else None,
                                   return_value=outcome):
                with self.assertRaises(P.Fatal): P.open_pidfd(123)

    def test_kernel_errno_keeps_processlookup_and_permission_semantics(self):
        for error, expected in ((errno.ESRCH, ProcessLookupError), (errno.EPERM, PermissionError),
                                (errno.ENOSYS, OSError), (0, OSError)):
            P._libc_pidfd.cache_clear()
            library = types.SimpleNamespace(pidfd_open=Export(-1, error), pidfd_send_signal=Export(-1, error))
            with self.subTest(errno=error), mock.patch.object(P.os, 'pidfd_open', None, create=True), \
                 mock.patch.object(P.signal, 'pidfd_send_signal', None, create=True), \
                 mock.patch.object(P.sys, 'platform', 'linux'), mock.patch.object(P.ctypes, 'CDLL', return_value=library):
                with self.assertRaises(expected) as opened: P.open_pidfd(123)
                self.assertEqual(opened.exception.errno, error or errno.EIO)
                with self.assertRaises(expected): P.send_pidfd_signal(43, 0)

    def test_supervisor_own_handle_probe_failure_closes_handle_and_prevents_use(self):
        lease={'owner_pid':1,'owner_creation_filetime':'2'}
        with mock.patch.object(P.Path, 'read_text', return_value='synthetic-boot'), \
             mock.patch.object(P, 'check_lease', return_value=lease), \
             mock.patch.object(P.ctypes, 'CDLL', return_value=types.SimpleNamespace(prctl=lambda *a: 0)), \
             mock.patch.object(P, 'open_pidfd', return_value=45), \
             mock.patch.object(P, 'send_pidfd_signal', side_effect=OSError(errno.ENOSYS, 'unsupported')) as sent, \
             mock.patch.object(P.os, 'close') as close, mock.patch.object(P.subprocess, 'Popen') as child:
            with self.assertRaises(OSError): P.Supervisor('lease','nonce',{},'output',lambda p:'sha')
            sent.assert_called_once_with(45, 0)
            close.assert_called_once_with(45)
            child.assert_not_called()

    def test_no_syscall_number_or_numeric_process_signalling_fallback(self):
        tree=ast.parse(Path(P.__file__).read_text())
        forbidden=[n for n in ast.walk(tree) if isinstance(n,ast.Attribute)
                   and n.attr in {'kill','killpg','syscall'}]
        self.assertEqual(forbidden, [])


if __name__=='__main__': unittest.main()
