# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# Keeps one connection to Xcode's MCP tools (`xcrun mcpbridge`) open, so Device Hub sessions live between calls, and serves
# one request per TCP connection on 127.0.0.1:47123: a JSON line {"tool", "args", "timeout"}, answered with the JSON-RPC
# result. Start it once, in the background: `python3 devicehub.py &`. xc.py and ds are its clients. (An editor's own
# Xcode tools do the same; this is for scripts, and for when that connection has dropped.)
import subprocess, json, socket, os, threading, sys, time, itertools
p = subprocess.Popen(["xcrun", "mcpbridge"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
pending, lock, ids = {}, threading.Lock(), itertools.count(10)
def reader():
    for line in p.stdout:
        try: m = json.loads(line)
        except Exception: continue
        if "id" in m and m["id"] in pending:
            pending[m["id"]][1] = m; pending[m["id"]][0].set()
threading.Thread(target=reader, daemon=True).start()
def call(method, params, timeout):
    i = next(ids); ev = threading.Event(); pending[i] = [ev, None]
    with lock: p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}) + "\n"); p.stdin.flush()
    ok = ev.wait(timeout); r = pending.pop(i)[1]
    return r if ok else {"error": "timeout"}
print(call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "fs", "version": "1"}}, 60), flush=True)
with lock: p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); p.stdin.flush()
s = socket.socket(socket.AF_INET); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", 47123)); s.listen(8)
def serve(c):
    f = c.makefile("rw")
    req = json.loads(f.readline())
    if req.get("tool") == "__list":
        r = call("tools/list", {}, 60)
    else:
        r = call("tools/call", {"name": req["tool"], "arguments": req.get("args", {})}, req.get("timeout", 600))
    f.write(json.dumps(r) + "\n"); f.flush(); c.close()
while True:
    c, _ = s.accept(); threading.Thread(target=serve, args=(c,), daemon=True).start()
