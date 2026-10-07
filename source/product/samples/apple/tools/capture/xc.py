# SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
# xc.py <Tool> '<json args>' [timeout]: one call to an Xcode MCP tool through devicehub.py; prints the text it returns.
import socket, json, sys, os
s = socket.socket(socket.AF_INET); s.connect(("127.0.0.1", 47123)); f = s.makefile("rw")
f.write(json.dumps({"tool": sys.argv[1], "args": json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}, "timeout": float(sys.argv[3]) if len(sys.argv) > 3 else 600}) + "\n"); f.flush()
r = json.loads(f.readline())
if "result" in r:
    for c in r["result"].get("content", []):
        print(c.get("text", c) if c.get("type") == "text" else f'[{c.get("type")}]')
    if r["result"].get("isError"): sys.exit(1)
else: print(json.dumps(r)[:3000]); sys.exit(1)
