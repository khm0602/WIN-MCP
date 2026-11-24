"""Watch a primary-monitor region via dxcam; NEW = changed then settled 1.2s, TYPING = changing >5s."""
import sys, time, hashlib
import dxcam
L, T, R, B = (int(v) for v in sys.argv[1:5])
cam = dxcam.create(output_color="RGB", processor_backend="numpy")
frame = None
def h():
    global frame
    f = cam.grab(region=(L, T, R, B))
    if f is not None: frame = f
    return hashlib.md5(frame.tobytes()[::7]).hexdigest() if frame is not None else ""
last = h(); last_change = None; burst_start = None; typing_sent = False
print("READY", flush=True)
while True:
    time.sleep(0.3)
    try: cur = h()
    except Exception as e: print("ERR", e, flush=True); time.sleep(2); continue
    now = time.time()
    if cur != last:
        last = cur; last_change = now
        if burst_start is None: burst_start = now; typing_sent = False
        if not typing_sent and now - burst_start > 5:
            print("TYPING", flush=True); typing_sent = True
    elif last_change and now - last_change > 1.2:
        print("NEW", flush=True); last_change = None; burst_start = None
