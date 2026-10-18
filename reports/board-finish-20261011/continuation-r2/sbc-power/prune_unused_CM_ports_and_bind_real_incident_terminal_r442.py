"""Keep R441 raw; an on-drill endpoint has real incident-tail annulus contact."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'select_CM_source_before_safe_subset_owned_terminals_r441.py').read_text(encoding='utf-8')
s=s.replace('CM51-actual-source-before-finite-safe-subset-owned-terminal-handoffs-r441','CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442')
s=s.replace("passV={r['via_UUID']for r in vr if not r['deficits']};prospective=","r441=P/'CM51-actual-source-before-finite-safe-subset-owned-terminal-handoffs-r441';p441=r441/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl';assert sha(p441)=='f88507f06651daeeaa5ca904b4cd04f0c710cea427d59a599588f3b75c0331ab';prior=pickle.loads(p441.read_bytes());passV={v['uuid']for v in prior['vias']};assert passV<={r['via_UUID']for r in vr if not r['deficits']};prospective=")
old="ends=[j for j,xy in enumerate((t['a'],t['b']))if Point(*xy).buffer(.1,quad_segs=128).intersection(ann).area>0]"
new="ends=[j for j,xy in enumerate((t['a'],t['b']))if Point(*xy).distance(p)<=.25 and body.intersection(ann).area>0]"
assert old in s;s=s.replace(old,new)
s=s.replace("assert outside.distance(p.buffer(.1,quad_segs=128))>=.28","assert outside.is_empty or outside.distance(p.buffer(.1,quad_segs=128))>=.28")
s=s.replace("'finite_track_endpoint_annulus_contact_mm2':[Point(*(t['a']if j==0 else t['b'])).buffer(.1,quad_segs=128).intersection(ann).area for j in ends]","'finite_incident_track_annulus_contact_mm2':body.intersection(ann).area,'endpoint_centres_within_exact_own_barrel_Cu':True")
s=s.replace("'outside_owncap_physical_drill_clearance_mm':outside.distance(p.buffer(.1,quad_segs=128))","'outside_owncap_physical_drill_clearance_mm':None if outside.is_empty else outside.distance(p.buffer(.1,quad_segs=128))")
s=s.replace("'R440_receipt_SHA256':sha(screen/'receipt.json')","'R440_receipt_SHA256':sha(screen/'receipt.json'),'R441_raw_no_annulus_contact_in_endpoint_disc_result':'RETAINED; endpoint disc of radius .1 lies inside own .1 drill, while incident .2 track tail has positive true annulus contact','R441_initial_subset_SHA256':sha(p441),'withdrawn_unused_prospective_ground_port_count':22-len(prospective)")
s=s.replace("print('R441_COMPLETE'","print('R442_COMPLETE'")
E=P/'exact-expanded-CM-source-before-safe-incident-terminals-r442.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
