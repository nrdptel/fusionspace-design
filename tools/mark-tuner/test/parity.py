"""Parity check: the tuner's geo.js must draw exactly what tools/build draws.

    python3 tools/mark-tuner/test/parity.py      # needs numpy scipy svgpathtools pillow, and node

Builds reference geometry with variants of geo.py/build.py (current values + 9 random sets, including
both lockup positions, leans up to 90 deg and DXF sizes/foot floors), then runs compare.js on tools/mark-tuner/src/geo.js."""
import json, re, sys, importlib, random, os, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BUILD = os.path.join(ROOT, "tools", "build")
TMP = tempfile.mkdtemp(prefix="fs-parity-")
src=open(f'{BUILD}/geo.py').read()
def variant(P, i):
    s=src
    s=re.sub(r'^TILT = .*$', f'TILT = {P["TILT"]!r}', s, flags=re.M)
    s=re.sub(r'^H_K, W_K, TIP_K = .*$', f'H_K, W_K, TIP_K = {P["H_K"]!r}, {P["W_K"]!r}, {P["TIP_K"]!r}', s, flags=re.M)
    s=re.sub(r'^SAG_K = .*$', f'SAG_K = {P["SAG_K"]!r}', s, flags=re.M)
    s=re.sub(r'^FOOT_K = [\d.]+', f'FOOT_K = {P["FOOT_K"]!r}', s, flags=re.M)
    s=re.sub(r'^KINDS = .*$', f'KINDS = {P["KINDS"]!r}', s, flags=re.M)
    s=re.sub(r'^SIZE = .*$', f'SIZE = {P["SIZE"]!r}', s, flags=re.M)
    s=re.sub(r'^WING_R = [-\d.]+', f'WING_R = {P["WING_R"]!r}', s, flags=re.M)
    s=re.sub(r'^GAP_W_R = [-\d.]+', f'GAP_W_R = {P["GAP_W_R"]!r}', s, flags=re.M)
    s=re.sub(r'^GAP_E_R = [-\d.]+', f'GAP_E_R = {P["GAP_E_R"]!r}', s, flags=re.M)
    s=re.sub(r'^TAIL_R = [-\d.]+', f'TAIL_R = {P["TAIL_R"]!r}', s, flags=re.M)
    d=os.path.join(TMP, f'v{i}'); os.makedirs(d, exist_ok=True)
    open(f'{d}/geo.py','w').write(s)
    for m in ('build.py','construction.py'): open(f'{d}/{m}','w').write(open(f'{BUILD}/{m}').read())
    return d
sys.path.insert(0, BUILD); import geo as _g, build as _b; sys.path.pop(0)
cases=[dict(TILT=_g.TILT,H_K=_g.H_K,W_K=_g.W_K,TIP_K=_g.TIP_K,SAG_K=_g.SAG_K,FOOT_K=_g.FOOT_K,KINDS=dict(_g.KINDS),SIZE=dict(_g.SIZE),GAP_W_R=_g.GAP_W_R,GAP_E_R=_g.GAP_E_R,WING_R=_g.WING_R,TAIL_R=_g.TAIL_R,
            STACK_POS=_b.STACK_POS,H_POS=_b.H_POS,STACK_H=_b.STACK_H,STACK_GAP_K=_b.STACK_GAP/_b.STACK_H,H_MARK=_b.H_MARK,H_GAP_K=_b.H_GAP_K,DXF_H_MM=_b.DXF_H_MM,DXF_MIN_WALL_MM=_b.DXF_MIN_WALL_MM)]
for m in ('geo','build','construction'): sys.modules.pop(m,None)
random.seed(4)
K=["vonkarman","conical","ogive","elliptical"]
for _ in range(9):
    cases.append(dict(TILT=round(random.choice([random.uniform(0,90),90.0]),1),H_K=round(0.4*random.uniform(2,5),4),W_K=0.40,TIP_K=0.58,SAG_K=round(random.uniform(0.2,1.0),2),FOOT_K=round(random.uniform(0,0.2),3),
      KINDS={n:random.choice(K) for n in ("main","west","east","south")},SIZE={"main":round(random.uniform(0.8,1.2),2),"west":round(random.uniform(0.2,0.7),2),"east":round(random.uniform(0.2,0.7),2),"south":round(random.uniform(0.2,0.7),2)},
      GAP_W_R=round(random.uniform(-0.2,1.0),2),GAP_E_R=round(random.uniform(-0.2,1.0),2),WING_R=round(random.uniform(-1,1.5),2),TAIL_R=round(random.uniform(-0.5,1),2),STACK_POS=random.choice(['above','below']),H_POS=random.choice(['before','after']),STACK_H=float(random.randint(120,200)),STACK_GAP_K=round(random.uniform(0.1,0.4),3),H_MARK=float(random.randint(70,130)),H_GAP_K=round(random.uniform(0.2,0.6),3),DXF_H_MM=float(random.randint(20,200)),DXF_MIN_WALL_MM=round(random.uniform(0,1.5),2)))
out=[]
for i,P in enumerate(cases):
    d=variant(P,i)
    for m in ('geo','build','construction'): sys.modules.pop(m,None)
    sys.path.insert(0,d)
    import geo, build
    build.SRC=os.path.join(ROOT, 'source')
    build.STACK_POS=P['STACK_POS']; build.H_POS=P['H_POS']; build.STACK_H=P['STACK_H']; build.STACK_GAP=P['STACK_GAP_K']*P['STACK_H']; build.H_MARK=P['H_MARK']; build.H_GAP_K=P['H_GAP_K']
    r={}
    cl,A,bb=geo.fit_cluster(height=200); r['mark']=[geo.seg_to_d(cl[n]) for n in geo.ORDER]; r['markbb']=list(bb)
    cl,bb,dd,t,H=build.stacked_geometry(); r['stdy']=re.search(r'-?[\d.]+ -?[\d.]+',dd).group(0); r['st']=[geo.seg_to_d(cl[n]) for n in geo.ORDER]; r['stH']=H; r['stbb']=list(bb)
    cl,bb,dd,t,W,H,m=build.horizontal_geometry(P['H_MARK']); r['ho']=[geo.seg_to_d(cl[n]) for n in geo.ORDER]; r['hoWH']=[W,H]; r['hobb']=list(bb)
    for k in ('favicon','icon','app'):
        s=build.icon_svg(k); r[k]=re.findall(r' d="([^"]+)"',s)
    r['dxf']=[]
    for hmm, mw in ((50.0, 0.5), (P['DXF_H_MM'], P['DXF_MIN_WALL_MM'])):
        cl,A,bb=build.dxf_geometry(hmm, mw); r['dxf'].append(dict(h=hmm, mw=mw, d=[geo.seg_to_d(cl[n]) for n in geo.ORDER], bb=list(bb)))
    out.append(dict(P=P,r=r))
    sys.path.pop(0)
ref = os.path.join(TMP, "ref.json"); json.dump(out, open(ref, "w"))
sys.exit(subprocess.run(["node", os.path.join(HERE, "compare.js"), ref]).returncode)
