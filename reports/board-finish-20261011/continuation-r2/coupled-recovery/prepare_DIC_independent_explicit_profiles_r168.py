"""Bind missing old proposal clearance to its frozen explicit filled header."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'audit_DIC_three_track_independent_r166.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r166','r168').replace('R166','R168')
s=s.replace("float(z['clearance_mm']))+.025","float(zone_local[z['uuid']]))+.025",1)
needle="ioitems=ioobjects.values() if isinstance(ioobjects,dict) else ioobjects;ioitems=list(ioitems);mutual=[];mutualerrors=[]"
replacement="""ioitems=ioobjects.values() if isinstance(ioobjects,dict) else ioobjects;ioitems=list(ioitems);assert len(ioitems)==2 and {z['uuid'] for z in ioitems}=={q['new_UUID'] for q in ior['only_two_owned_host_group_replacements']};fullraw=A.read(ior['frozen_full_model_file']);assert C.sha(fullraw)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5';fg,fh,fb,fz,ff=pickle.loads(fullraw);import restore_SAFE_generated_precision_states_r168 as PS;A.read(PS.__file__);precisionproof=PS.restore_bound_generated_precision_states(fb,fz);canonical={q['uuid']:q for q in fz};profilekeys=('net','layer','clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
 for z in ioitems:
  exact=canonical[z['uuid']];assert all(k in z and k in exact and z[k]==exact[k] for k in profilekeys);assert z['net']=='/IO_3V3' and z['layer'] in('In2.Cu','In3.Cu');assert tuple(z[k] for k in profilekeys[2:])==(.15,.15,'FULL_SOLID',124,1,.15,.3);assert all(z[role].wkb==exact[role].wkb for role in('shape','zone_outline_shape'))
 ioitems=[canonical[z['uuid']] for z in ioitems];mutual=[];mutualerrors=[]"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("'accepted_IO3_R190_receipt_sha256':","'accepted_IO3_all72_lossless_generated_precision_role_restorations':precisionproof,'accepted_IO3_nine_native_settings_direct_fields_required':True,'legacy_R118_held_proposal_clearance_bound_to_exact_frozen_after_header':True,'accepted_IO3_R190_receipt_sha256':")
dst=H/'audit_DIC_three_track_independent_r168.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DIC-independent-explicit-profiles-r168.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R166 stopped when an older R118 held shape omitted clearance_mm. R168 uses only that same UUID explicit frozen after-zone header, already checked against native source or declared proposal, with no invented fallback. R190 mutual reads full accepted R183 and restores exactly72 bound generated role precision states with unchangedWKB through PS168; all9 IO3 native settings direct-equal packet. No geometric threshold/proposal/original change.'},indent=1)+'\n');print(sha(dst.read_bytes()))
