#!/bin/bash
# Set up the build on a Linux VM without root (Ubuntu): rsvg-convert from the Ubuntu package, Python packages for this
# user, the brand fonts, and the npm packages. Takes a minute or two; run once per VM:  bash tools/build/setup-linux-vm.sh
#
# Written for a VM whose home disk is small and shared, and whose ~/.cache can be emptied under you, so rsvg-convert is unpacked into the
# repo's git-ignored _build/vm/ (on your own disk) and cadquery-ocp goes in without the full VTK wheel (it only needs a few of
# VTK's libraries; the whole wheel is about 500 MB and filled the disk). Build with the line printed at the end: it also
# points TMPDIR at _build/tmp, so scratch renders don't land on the VM's disk either.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VM="$ROOT/_build/vm"; mkdir -p "$VM" "$ROOT/_build/tmp"
if [ ! -x "$VM/rsvg/usr/bin/rsvg-convert" ]; then
  mkdir -p "$VM/deb" "$VM/rsvg" && (cd "$VM/deb" && apt-get download librsvg2-bin >/dev/null)
  dpkg-deb --fsys-tarfile "$VM"/deb/librsvg2-bin_*.deb | tar -x -C "$VM/rsvg" ./usr/bin/rsvg-convert
fi
python3 -m pip install --user -q --no-cache-dir numpy scipy pillow svgpathtools ezdxf shapely matplotlib 2>&1 | grep -v "^WARNING" || true
if ! python3 -c "import OCP.BRepPrimAPI" 2>/dev/null; then
  OCPV=7.9.3.1.1; VTKV=9.6.2                          # cadquery-ocp 7.9.3.1.1 is built against vtk 9.6.2
  mkdir -p "$HOME/tmp" && export TMPDIR="$HOME/tmp"
  python3 -m pip install --user -q --no-cache-dir --no-deps cadquery-ocp==$OCPV cadquery-ocp-proxy==$OCPV 2>&1 | grep -v "^WARNING" || true
  python3 -m pip download -q --no-deps --no-cache-dir -d "$VM" vtk==$VTKV
  python3 - "$VM"/vtk-$VTKV-*.whl <<'PY'
import os, re, subprocess, sys, zipfile, site
sp = site.getusersitepackages(); z = zipfile.ZipFile(sys.argv[1])
names = {os.path.basename(n): n for n in z.namelist() if n.startswith(("vtkmodules/", "vtk.libs/")) and ".so" in n}
def needed(p):
    out = subprocess.run(["readelf", "-d", p], capture_output=True, text=True).stdout
    return re.findall(r"\[(.+?)\]", " ".join(l for l in out.splitlines() if "NEEDED" in l))
todo = set()
for d in ("OCP", "cadquery_ocp.libs"):
    for f in os.listdir(os.path.join(sp, d)):
        if ".so" in f: todo |= set(needed(os.path.join(sp, d, f)))
done = set()
while todo:                                     # extract just the VTK libraries OCP links to, and theirs
    n = todo.pop()
    if n in done or n not in names: continue
    done.add(n); z.extract(names[n], sp); todo |= set(needed(os.path.join(sp, names[n])))
print(f"cadquery-ocp: {len(done)} VTK libraries extracted")
PY
  rm -f "$VM"/vtk-*.whl
fi
mkdir -p "$HOME/.fonts" && cp "$ROOT"/type/fonts/*.ttf "$HOME/.fonts/" && (fc-cache -f >/dev/null 2>&1 || true)
[ -d "$ROOT/tools/build/node_modules" ] || (cd "$ROOT/tools/build" && npm ci --silent)
python3 -c "import OCP.BRepPrimAPI; print('OCP ok')" 2>/dev/null || echo "WARN: OCP (cadquery-ocp) not importable: STEP, 3MF and some 3D prints will be skipped"
echo "ready. Build with:  export PATH=\"$VM/rsvg/usr/bin:\$HOME/.local/bin:\$PATH\" TMPDIR=\"$ROOT/_build/tmp\" MPLCONFIGDIR=\"$ROOT/_build/tmp/mpl\"; python3 tools/build/build.py"
