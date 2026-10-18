"""Create separate four-owned-track constructor, preserving all prior attempts."""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'construct_DIC_four_track_reference_coupled_r178.py';assert not p.exists()
s=(H/'construct_DIC_old_reference_safe_r174.py').read_text()
s=s.replace('DIC only from separately frozen strict-neighbour-safe sites.','DIC with one exact CMD blocker added after strict additive locus failure.')
s=s.replace('Exact original three deletes and fixed CS/RSP replacements are retained;','Exact original four deletes and fixed CS/RSP replacements are retained;')
s=s.replace("C=A.C;NET=B.NET;GND=B.GND;CS=B.CS;RSP=B.RSP;LAYERS=B.LAYERS","C=A.C;NET=B.NET;GND=B.GND;CS=B.CS;RSP=B.RSP;CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER';LAYERS=B.LAYERS")
s=s.replace('DIC-old-reference-safe-construction-r174','DIC-four-track-reference-coupled-r178')
s=s.replace("rp=H/'DIC-expanded-real-return-site-nomination-r172.json';r=json.loads(A.read(rp));assert r['R170_receipt_sha256']=='94bd456d0c2849dfd3a7bf0df56f9949826c1a8b651da1d3095cc6a51301d769';assert all(q['options'] for q in r['nominations']);", "rp=H/'DIC-neighbour-safe-site-nomination-r170.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='94bd456d0c2849dfd3a7bf0df56f9949826c1a8b651da1d3095cc6a51301d769';assert next(q['options'] for q in r['nominations'] if q['kind']=='target');r176p=H/'DIC-source-reachable-paired-locus-r176.json';assert C.sha(A.read(r176p))=='b612ab99c8dbe5bb58b4a5c33a9b2f5b88ef88382aaad1eaf768a96c5073658c';")
s=s.replace("removed=set(prior['removed_UUIDs']);deletes=prior['exact_deleted_chunks'];", "removed=set(prior['removed_UUIDs'])|{'811a28fc-3124-4526-b8b8-287522e6a219'};deletes={**prior['exact_deleted_chunks'],'811a28fc-3124-4526-b8b8-287522e6a219':inv[3]['811a28fc-3124-4526-b8b8-287522e6a219']};assert b'(locked yes)' in deletes['811a28fc-3124-4526-b8b8-287522e6a219'];")
s=s.replace('for n in(NET,CS,RSP)','for n in(NET,CS,RSP,CMD)')
s=s.replace("sourceopts=next(q['options'] for q in r['nominations'] if q['kind']=='source');targetopts=next(q['options'] for q in r['nominations'] if q['kind']=='target');", "sourceopts=[{'signal':[127.057072,98.292323],'pairs':[{'return':[126.466153,97.716620],'return_new':True,'old_return_UUID':None,'distance_mm':.824996490156163}]}];targetopts=next(q['options'] for q in r['nominations'] if q['kind']=='target');targetopts=[{**q,'pairs':[{**p,'return_new':True,'old_return_UUID':None} for p in q['pairs']]} for q in targetopts];policy={L.norm(n):q for n,q in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};assert policy.get(CMD,{}).get('class') in(None,'NONE');")
s=s.replace("requested=[('F.Cu',attach[0],so['signal']),('B.Cu',so['signal'],to['signal']),('F.Cu',to['signal'],attach[1])]", "requested=[(CMD,'B.Cu',[123.05,95.05],[128.549999,100.55]),(NET,'F.Cu',attach[0],so['signal']),(NET,'B.Cu',so['signal'],to['signal']),(NET,'F.Cu',to['signal'],attach[1])]")
s=s.replace('for layer,a,b in requested:', 'for route_net,layer,a,b in requested:')
s=s.replace("plane='In1.Cu' if layer=='F.Cu' else'In4.Cu';free=B.physical_centres(h,cur,NET,layer,win).intersection(refs[plane].union(own).intersection(win.buffer(1)).buffer(-.105,quad_segs=128));", "plane='In1.Cu' if layer=='F.Cu' else'In4.Cu';scope=own if route_net==NET else Point();free=B.physical_centres(h,cur,route_net,layer,win).intersection(refs[plane].union(scope).intersection(win.buffer(1)).buffer(-.105,quad_segs=128));")
s=s.replace("q={'raw_net':identity.raw(NET),'layer':layer", "q={'raw_net':identity.raw(route_net),'layer':layer")
s=s.replace('DIC_R174_EXACT_ROUTE','DIC_R178_EXACT_ROUTE')
s=s.replace("body.difference(refs[plane].union(own)).area", "body.difference(refs[plane].union(scope)).area")
s=s.replace("uid,ch=identity.serial_segment(NET,layer,pa,pb,.2);assert uid not in inv[3] and uid not in chunks;t={'uuid':uid,'net':identity.raw(NET),'layer':layer", "uid,ch=identity.serial_segment(route_net,layer,pa,pb,.2);ch=ch.replace(b'(width 0.2)',b'(width 0.2) (locked yes)') if route_net==CMD else ch;assert uid not in inv[3] and uid not in chunks;t={'uuid':uid,'net':identity.raw(route_net),'layer':layer")
s=s.replace("'R172_receipt_sha256':C.sha(A.read(rp))", "'R170_receipt_sha256':C.sha(A.read(rp)),'R176_source_reachable_paired_locus_failure_sha256':C.sha(A.read(r176p)),'new_CMD_segments_preserve_locked_yes':True")
s=s.replace("'DIC_OLD_REFERENCE_SAFE_EXACT_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN'", "'DIC_FOUR_EXACT_TRACK_REFERENCE_COUPLED_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN'")
s=s.replace("'DIC_OLD_REFERENCE_SAFE_EXACT_CONSTRUCTION_INCOMPLETE'", "'DIC_FOUR_EXACT_TRACK_REFERENCE_COUPLED_CONSTRUCTION_INCOMPLETE'")
assert 'construct_DIC_old_reference_safe_r174.py' not in s
assert 'for route_net,layer,a,b in requested' in s and "beforegroups={n:Q.physical(cur['after'],n)[1] for n in(NET,CS,RSP,CMD)}" in s
compile(s,str(p),'exec');p.write_text(s);print(p)
