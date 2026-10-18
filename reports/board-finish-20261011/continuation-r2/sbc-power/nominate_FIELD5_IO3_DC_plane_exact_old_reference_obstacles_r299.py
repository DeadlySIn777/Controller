"""Preserve exact old supported reference body regions before DC routing."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_FIELD5_IO3_In1_In4_existing_annulus_DC_plane_r298.py').read_text()
needle="base=base.replace('R296','R298')"
change=r'''
base=base.replace('FIELD5-R393-IO3-In1-In4-existing-annulus-DC-plane-r298','FIELD5-R393-IO3-DC-exact-supported-old-reference-obstacles-r299')
base=base.replace("return clip.intersection(outline.buffer(-rad-.000003)).difference(unary_union(cuts))", "refouts=('F.Cu','In2.Cu')if layer=='In1.Cu'else('B.Cu','In3.Cu');oldref=refs[refouts[0]].intersection(clip.buffer(2));maxlocal=max((float(zz['clearance_mm'])for zz in c['zones']if zz['uuid']in nativeids and L.norm(zz['net'])=='/LOGIC_GND'and layer in zz['fills']),default=.15);protected=[]\n  for tt in c['tracks']:\n   if tt['layer']not in refouts or L.norm(tt['net'])=='/LOGIC_GND'or dom.get(L.norm(tt['net']))!=dom.get('/LOGIC_GND'):continue\n   sh=L.body(tt)if tt.get('m')is not None else A.shape({'kind':'segment',**tt})\n   if not sh.intersects(clip.buffer(2)):continue\n   supported=sh.intersection(oldref)\n   if not supported.is_empty:protected.append(buf(supported,rad+maxlocal+.025+.000203))\n  for zz in q:\n   if zz['layer']not in refouts or L.norm(zz['net'])=='/LOGIC_GND'or dom.get(L.norm(zz['net']))!=dom.get('/LOGIC_GND'):continue\n   supported=set_precision(zz['shape'],0).intersection(oldref)\n   if not supported.is_empty:protected.append(buf(supported,rad+maxlocal+.025+.000203))\n  cuts.extend(protected);return clip.intersection(outline.buffer(-rad-.000003)).difference(unary_union(cuts))")
base=base.replace("trial,fillledger,affected=project_native(nt,str(len(attempts)))", "put(O/(str(len(attempts))+'-attempt-exact-virtual-DC-plane-recipe.json'),{'layer':layer,'width_mm':width,'path':path,'virtual_construction_only_tracks':nt,'not_native_discrete_additions':True,'fresh_all_gates':'PENDING'});trial,fillledger,affected=project_native(nt,str(len(attempts)))")
base=base.replace("row['native_fill_retreat_old_contacts_lost']=len(contactbad)", "put(O/(str(len(attempts))+'-attempt-fresh-contact-source-facts.json'),{'old_relationship_losses':contactbad,'old_direct_contact_losses':directbad,'prior_source_key_losses':sourcebad,'expected_source_key_missing':[list(k)for k in lost],'exact_new_virtual_recipe_file':str((O/(str(len(attempts))+'-attempt-exact-virtual-DC-plane-recipe.json')).resolve())});row['native_fill_retreat_old_contacts_lost']=len(contactbad)")
base=base.replace("row['strict_three_bank_old_reference_losses']=len(refbad)", "put(O/(str(len(attempts))+'-attempt-strict-three-bank-old-reference-facts.json'),refbad);row['strict_three_bank_old_reference_losses']=len(refbad)")
base=base.replace('R298','R299')
'''
assert s.count(needle)==1;s=s.replace(needle,needle+'\n'+change)
exec(compile(s,str(__file__),'exec'))
