import ctypes, json
from ctypes import wintypes
k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=wintypes.HANDLE
k.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
a,b=ctypes.c_size_t(),ctypes.c_size_t()
assert k.GetProcessAffinityMask(k.GetCurrentProcess(),ctypes.byref(a),ctypes.byref(b))
assert a.value.bit_count()==2
try:
 x=bytearray(512*1024**2)
except MemoryError:
 print(json.dumps({"actual_affinity_mask":a.value,"denied_allocation_bytes":512*1024**2}));raise SystemExit(0)
raise SystemExit(99)
