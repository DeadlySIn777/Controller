"""Freeze independent five-via/four-delete auditor only after R186 positive."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;rp=H/'DIC-In3-actual-paired-CMD-construction-r190.json';r=json.loads(rp.read_text());assert r['verdict']=='DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN';pin=hashlib.sha256(rp.read_bytes()).hexdigest();mpin=r['selected']['model_sha256'];p=H/'audit_DIC_In3_CMD_independent_r196.py';assert not p.exists();s=(H/'audit_DIC_three_track_independent_r168.py').read_text();s=s.replace('DIC-three-track-independent-r168','DIC-In3-CMD-independent-r196').replace('DIC_R168','DIC_R196')
s=s.replace("RSP='/motherboard_io_control/DIC_IOL1_RSP_BUFFER';GND", "RSP='/motherboard_io_control/DIC_IOL1_RSP_BUFFER';CMD='/motherboard_io_control/DIC_IOL1_CMD_BUFFER';GND")
s=s.replace("rp=H/'DIC-three-track-coupled-r164.json'", "rp=H/'DIC-In3-actual-paired-CMD-construction-r190.json'")
s=s.replace("=='cdb152ede9fbb637191668297405e07af5be24f7e984dc23687dd37d5209ca4b'", "=='"+pin+"'")
s=s.replace("=='7e11621fb23ee9fdabdbed66ca3edf51841848d231c50f02370305e5fc5e16b5'", "=='"+mpin+"'")
s=s.replace('assert len(removed)==3','assert len(removed)==4')
s=s.replace("q['net'] in(NET,CS,RSP)","q['net'] in(NET,CS,RSP,CMD)")
s=s.replace("assert len(nt)==15 and len(nv)==4", "assert len(nt)==sel['new_track_count'] and len(nv)==sel['new_via_count']==5;assert all(b'(locked yes)' in added[t['uuid']] for t in nt if L.norm(t['net'])==CMD)")
s=s.replace('for n in(NET,CS,RSP)','for n in(NET,CS,RSP,CMD)').replace('affected={NET,CS,RSP,GND}','affected={NET,CS,RSP,CMD,GND}')
s=s.replace('for net in(NET,CS,RSP):','for net in(NET,CS,RSP,CMD):')
old="""pairproof=[];own=[];nvby={q['uuid']:q for q in nv}
 for q in sel['paired_returns_after_all_four_holes']:
  sig=nvby[q['signal_UUID']];ret=nvby[q['return_UUID']];p=Point(ret['x'],ret['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={plane:ann.intersection(newrefs[outer].buffer(-.075,quad_segs=128)).area for plane,outer in(('In1.Cu','F.Cu'),('In4.Cu','B.Cu'))};distance=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);proof={'signal_UUID':sig['uuid'],'return_UUID':ret['uuid'],'distance_mm':distance,'actual_J11001_2_return_rooted':('via',ret['uuid'],'In1.Cu') in layerkeys(newroot) and('via',ret['uuid'],'In4.Cu') in layerkeys(newroot),'finite_actual_annular_interior_mm2':areas,'unchanged_exact_own_radius_mm':.525,'radius_expansion_mm':0,'new_actual_native_all6_annuli_gate':'OPEN'};pairproof.append(proof)
  if proof['actual_J11001_2_return_rooted'] and .815<=distance<=1 and all(a>.004 for a in areas.values()):own.append((sig['uuid'],Z.bounded_disk(sig,.525)))
 ownshape=unary_union([shape for uid,shape in own]);reference=[];referrors=[]
 for t in nt:
  body=A.shape({'kind':'segment',**t});allowed=newrefs[t['layer']].union(ownshape if L.norm(t['net'])==NET else Point());missing=body.difference(allowed);q={'UUID':t['uuid'],'raw_net':t['net'],'signal_layer':t['layer'],'actual_source_reference_layer':'In1.Cu' if t['layer']=='F.Cu' else'In4.Cu','full_body_reference_gap_mm2':missing.area,'exact_same_net_qualified_own_aperture_UUIDs':[uid for uid,shape in own] if L.norm(t['net'])==NET else[],'radius_expansion_mm':0};reference.append(q)
  if not missing.is_empty:referrors.append(q)"""
new="""pairproof=[];own=[];nvby={q['uuid']:q for q in nv};allvia={q['uuid']:q for q in h['vias']};oldvia={q['uuid']:q for q in h0['vias']};insets={outer:shape.buffer(-.075,quad_segs=128) for outer,shape in newrefs.items()};expected_new_signal={q['uuid'] for q in nv if L.norm(q['net'])==NET}
 assert len(expected_new_signal)==2
 for q in sel['paired_returns_after_all_holes']:
  sig=allvia[q['signal_UUID']];ret=nvby[q['return_UUID']];net=L.norm(sig['net']);assert L.norm(ret['net'])==GND and(ret['d'],ret['drill'])==(.5,.2)
  if net==CMD:
   assert sig['uuid']=='1f815e33-e973-46e2-833e-96fee8d37fcf' and sig==oldvia[sig['uuid']] and(sig['x'],sig['y'],sig['d'],sig['drill'])==(128.549999,100.55,.6,.3) and all(l in sig['flashed'] for l in LAYERS);radius=.575;assert sig['uuid'] in inv[3]
  else:assert net==NET and sig['uuid'] in expected_new_signal and(sig['d'],sig['drill'])==(.5,.2);radius=.525
  p=Point(ret['x'],ret['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={plane:ann.intersection(insets[outer]).area for plane,outer in(('In1.Cu','F.Cu'),('In4.Cu','B.Cu'))};distance=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);proof={'signal_UUID':sig['uuid'],'signal_raw_net':sig['net'],'signal_new':sig['uuid'] in nvby,'signal_exact_at_mm':[sig['x'],sig['y']],'signal_exact_diameter_drill_mm':[sig['d'],sig['drill']],'signal_original_native_chunk_sha256':C.sha(inv[3][sig['uuid']]) if net==CMD else None,'return_UUID':ret['uuid'],'distance_mm':distance,'actual_J11001_2_return_rooted':('via',ret['uuid'],'In1.Cu') in layerkeys(newroot) and('via',ret['uuid'],'In4.Cu') in layerkeys(newroot),'finite_actual_annular_interior_mm2':areas,'unchanged_exact_own_radius_mm':radius,'radius_expansion_mm':0,'new_actual_native_all6_annuli_gate':'OPEN'};pairproof.append(proof)
  if proof['actual_J11001_2_return_rooted'] and .815<=distance<=1 and all(a>.004 for a in areas.values()):own.append((sig['uuid'],net,Z.bounded_disk(sig,radius)))
 own_by_net={net:unary_union([shape for uid,n,shape in own if n==net]) for net in(NET,CMD)};reference=[];referrors=[]
 for t in nt:
  net=L.norm(t['net']);body=A.shape({'kind':'segment',**t});allowed=newrefs[t['layer']].union(own_by_net.get(net,Point()));missing=body.difference(allowed);q={'UUID':t['uuid'],'raw_net':t['net'],'signal_layer':t['layer'],'actual_source_reference_layer':'In1.Cu' if t['layer']=='F.Cu' else'In4.Cu','full_body_reference_gap_mm2':missing.area,'exact_same_net_qualified_own_aperture_UUIDs':[uid for uid,n,shape in own if n==net],'radius_expansion_mm':0};reference.append(q)
  if not missing.is_empty:referrors.append(q)"""
assert old in s;s=s.replace(old,new)
s=s.replace("neighbors,neighborproof=RF.audit(before,oldrefs,newrefs,GND,removed=removed);passed=not(errors or lostsource or lostcontacts or padloss or referrors or neighbors or mutualerrors) and len(own)==2;", "neighbors,neighborproof=RF.audit(before,oldrefs,newrefs,GND,removed=removed);import DIC_latest_mutual_exact_r180 as LM;A.read(LM.__file__);latest=LM.audit(nt,nv,removed,dom);directloss=[q for q in localcontacts if not q['direct_contact_retained']];passed=not(errors or lostsource or lostcontacts or directloss or padloss or referrors or neighbors or mutualerrors or latest['errors']) and len(own)==3;")
s=s.replace("'R164_receipt_sha256':", "'R190_receipt_sha256':").replace("'exact3_deleted_chunks_sha256':", "'exact4_deleted_chunks_sha256':").replace("'exact19_added_chunks_sha256':", "'all_exact_added_chunks_sha256':")
s=s.replace("'latest_R183_ROOT55_U10017_R195_all_power_source_current_and_combined_DIC_native_r06_r07_DRC_SI':'OPEN'", "'latest_R73_ROOT55_U10017_R195_IO3_R201_exact_mutual':latest,'full_latest_all_power_source_current_and_combined_DIC_native_r06_r07_DRC_SI':'OPEN'")
s=s.replace("'DIC_INDEPENDENT_EXACT_FROZEN_HOST_GATES_PASS_NATIVE_LATEST_COMPOSITION_OPEN'", "'DIC_PAIRED_CMD_INDEPENDENT_EXACT_HOST_AND_LATEST_MUTUAL_PASS_COMBINED_NATIVE_OPEN'").replace("'DIC_INDEPENDENT_EXACT_FROZEN_HOST_GATES_INCOMPLETE'", "'DIC_PAIRED_CMD_INDEPENDENT_EXACT_FROZEN_HOST_GATES_INCOMPLETE'")
s=s.replace("'IO3_mutual':len(mutualerrors)", "'IO3_mutual':len(mutualerrors),'latest_mutual':len(latest['errors']),'direct_old_contacts':len(directloss)")
assert 'paired_returns_after_all_four_holes' not in s and 'len(own)==3' in s
s=s.replace("q['layer'] in('F.Cu','B.Cu')","q['layer'] in('F.Cu','B.Cu','In3.Cu')")
compile(s,str(p),'exec');p.write_text(s);print(p)
