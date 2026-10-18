"""Move only the penultimate planned connector vertex; no hole-rule relaxation."""
import json
import hashlib
from pathlib import Path
import whole_group as W
P=W.P

def main():
 destination=P.HERE/'terminal-fix.json'
 if destination.exists():raise ValueError('distinct immutable result required')
 first=json.loads(P.S.read(P.HERE/'repair-plan.json'));alt=json.loads(P.S.read(P.HERE/'alternate-lower.json'))
 P.S.read(Path(__file__));P.S.read(Path(W.__file__))
 rows,_=P.I.own_additions();g,_,_=P.R.overlay_and_targets()
 target=W.TARGET;raw=P.S.read(target)
 if W.sha(raw)!=W.TARGET_SHA:raise ValueError('combined target differs')
 base=P.R.composition.inventory(P.S.read(P.R.R07));after=P.R.composition.inventory(raw)
 for uid,ch in after[4].items():
  if uid in base[4]:continue
  r=W.parse_copper(uid,ch)
  if r['kind']=='via':g['vias'].append({'uuid':uid,'net':r['net'],'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill'],'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
  else:g['tracks'].append({'uuid':uid,'net':r['net'],'a':r['a'],'b':r['b'],'w':r['width'],'layer':r['layer']})
 r,e=P.exemptions();model=P.S.Model(g,r,e)
 removed=set(P.REMOVED_VIAS)|{u for n in P.NETWORKS for u in n['remove']}
 kept={u:r for u,r in rows.items() if u not in removed}
 replacement=first['new_segments']+[alt['selected']['new_via']]
 own={r['uuid']:{'uuid':r['uuid'],'net':P.NET,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill']} for r in list(kept.values())+replacement if r['kind']=='via'}
 vias={v['uuid']:v for v in g['vias']}
 barriers={r['refdes'] for r in json.loads(P.S.read(Path('Z:/pcb-runs/domains/barriers.json')))['barriers']}
 path=alt['selected']['segments'][1];points=path['points_mm'];attempts=[];selected=None
 # Exact former point353.4,201.9 is only.502mm fromtarget; the stricthole
 # mask requires a nonterminal segment endpoint outside.575mm. Move it up
 # inside the original local free connector window, never change any old item.
 for x,y in [(353.4,201.8),(353.4,201.75),(353.4,201.7),(353.35,201.8),(353.45,201.8),(353.3,201.8),(353.5,201.8)]:
  variant=[*points[:-2],[x,y],points[-1]]
  new=[{'uuid':'PLAN:terminal-fix:'+str(i),'kind':'segment','net':P.NET,'a':a,'b':b,'width':.3,'layer':'F.Cu'} for i,(a,b) in enumerate(zip(variant,variant[1:]))]
  audits=[P.audit_row(row,model,vias,own,barriers) for row in new]
  failures=[a for a in audits if a['failures']]
  attempts.append({'penultimate_point':[x,y],'failures':failures})
  if not failures:selected={**path,'points_mm':variant};break
 for p,s in P.S.READS.items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=s:raise ValueError('changed input:'+p)
 out={'verdict':'LOCAL_CONNECTOR_PASS_WHOLE_GROUP_REAUDIT_REQUIRED' if selected else 'WITHHELD_CONNECTOR',
      'original_path':path,'selected':selected,'attempts':attempts,'source_files_sha256':P.S.READS,
      'all_new_copper_clearance_exceptions':False,'board_emitted':False,'native_jobs':0}
 destination.write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(out,indent=1),flush=True)

if __name__=='__main__':main()
