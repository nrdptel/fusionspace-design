const path=require('path');
const g=require(path.join(__dirname,'..','src','geo.js'));
const ref=require(path.resolve(process.argv[2])); let bad=0, tot=0, maxd=0;
function cmpD(a,b,tag){tot++; if(a===b) return; const na=a.match(/-?\d+(\.\d+)?/g).map(Number), nb=b.match(/-?\d+(\.\d+)?/g).map(Number);
  let m=0; if(na.length!==nb.length){console.log('LEN',tag);bad++;return} na.forEach((v,i)=>m=Math.max(m,Math.abs(v-nb[i]))); maxd=Math.max(maxd,m); if(m>0.0011){bad++;console.log('DIFF',tag,m)}}
for (const [i,{P,r}] of ref.entries()){
  const G=g.makeGeo(P);
  const f=G.fitCluster({height:200}); g.ORDER.forEach((n,j)=>cmpD(g.segToD(f.cl[n]),r.mark[j],`c${i} mark ${n}`));
  const st=g.stackedGeometry(G,P); g.ORDER.forEach((n,j)=>cmpD(g.segToD(st.cl[n]),r.st[j],`c${i} st ${n}`));
  if(Math.abs(st.H-r.stH)>1e-9) {bad++;console.log('stH',st.H,r.stH)}
  const ho=g.horizontalGeometry(G,P); g.ORDER.forEach((n,j)=>cmpD(g.segToD(ho.cl[n]),r.ho[j],`c${i} ho ${n}`));
  if(Math.abs(ho.W-r.hoWH[0])>1e-9||Math.abs(ho.H-r.hoWH[1])>1e-9){bad++;console.log('hoWH',ho.W,ho.H,r.hoWH)}
  [...ho.bb.map((v,k)=>v-r.hobb[k]),...st.bb.map((v,k)=>v-r.stbb[k])].forEach(d=>{if(Math.abs(d)>1e-9){bad++;console.log('bb',i,d)}});
  for(const k of ['favicon','icon','app']){const ig=g.iconGeometry(G,k); ig.paths.forEach((d,j)=>cmpD(d,r[k][j],`c${i} ${k} ${j}`))}
  for(const [m,x] of r.dxf.entries()){const dg=g.dxfGeometry(G,x.h,x.mw); g.ORDER.forEach((n,j)=>cmpD(g.segToD(dg.cl[n]),x.d[j],`c${i} dxf${m} ${n}`)); dg.bb.forEach((v,k)=>{if(Math.abs(v-x.bb[k])>1e-6){bad++;console.log('dxf bb',i,m,v,x.bb[k])}})}
}
console.log('compared',tot,'paths; mismatches',bad,'max rounding diff',maxd);
process.exit(bad?1:0);
