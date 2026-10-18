"""Independent current-contact/reference check for the smaller exact recipe.

Existing SENSE SAME_PLANE support is a separately declared proposal, not an
unreported relaxation of the frozen blanket return predicate.
"""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'audit_Q0_R436_optimized_raw_reference_r442.py'
setup=base.read_text().rsplit("exec(compile(code,str(base),'exec'))",1)[0];ns={'__file__':str(base)};exec(compile(setup,str(base),'exec'),ns);code=ns['code']
code=code.replace('Q0-R436-optimized-raw-reference-r442','Q0-R454-independent-actual-reference-r456').replace('Q0_R442_','Q0_R456_').replace('Q0-exact-R428-current-filled-only-r436','Q0-exact-R452-current-filled-only-r454').replace('0f4c4442ad12c21844ebb34f38176547601eb99a79a18abd179dfdc8f76c96b6','57de8393410dfa149f02777ca4d5d97fb123a3ca305061adbdab98267803b22e').replace('b80087827ba1f1d6e7f21948faa9b960eaf20e6c07c6443e5a31219b0ba956ae','aa580499d3bfb057b7047ba124d2813d0af3905315c82871e49baf612ee7d728').replace('Q0-R426-exact-native-owned-operation-r428','Q0-R450-exact-native-owned-operation-r452').replace('f0b31e152b7f13c0a00401149176fb5dff69c4743121654439ca39a82dfeb27c','ed12eb485bd83caef6632d6d7aaf35bbddf18b06b4dbe277c34447b76bee030e').replace('six-exact-paired-source-return-nominations.json','two-exact-paired-source-return-nominations.json')
old="[{'uuid':op['original_SENSE_via_UUID'],'net':'/motherboard_do/DOA_Q0_ISNS','x':228.96,'y':160.412,'d':.5,'drill':.2,'added_layer_only':'In2.Cu'}]"
new="[{**v,'added_layer_only':'In2.Cu'}for v in op['existing_SENSE_vias']]"
assert old in code;code=code.replace(old,new,1)
old="for rule in reserve['keepouts']:\n  if net not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in K.L.poly(rule['outline'])):errors.append({'kind':'frozen_reserve','UUID':item['uuid'],'name':rule['name']})"
new="""for rule in reserve['keepouts']:
  if net not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(body.distance(s)<.025 for s in K.L.poly(rule['outline'])):
   subset=None
   if not via:
    for uid in removed:
     old=oldtracks[uid]
     if(K.L.norm(old['net']),old['layer'],old['w'])!=(net,item['layer'],item['w']):continue
     aa=[int(round(x*1e6))for x in old['a']];bb=[int(round(x*1e6))for x in old['b']];xx=[[int(round(x*1e6))for x in p]for p in(item['a'],item['b'])];dx,dy=bb[0]-aa[0],bb[1]-aa[1];length2=dx*dx+dy*dy
     if all((p[0]-aa[0])*dy==(p[1]-aa[1])*dx and 0<=(p[0]-aa[0])*dx+(p[1]-aa[1])*dy<=length2 for p in xx):subset={'old_UUID':uid,'old_axis_IU':[aa,bb],'new_axis_IU':xx,'same_native_width_IU':int(round(item['w']*1e6)),'analytic_capsule_subset_of_original_Cu':True};break
   rawrow={'kind':'frozen_reserve_whole_new_chunk_raw','UUID':item['uuid'],'name':rule['name'],'exact_original_body_subset':subset,'novel_Cu_reserve_overlap':subset is None};reserveRaw.append(rawrow)
   if subset is None:errors.append(rawrow)"""
assert old in code;code=code.replace(old,new,1).replace('checks=[];errors=[];apertures=[];','checks=[];errors=[];apertures=[];reserveRaw=[];').replace("put(out/'true-new-copper-analytic-ledger.json',checks);","put(out/'raw-whole-chunk-reserve-and-exact-original-subset-ledger.json',reserveRaw);put(out/'true-new-copper-analytic-ledger.json',checks);",1)
old="put(out/'actual-paired-return-and-strong-own-scope-ledger.json',{'pairs':pairproof,'support':supportrows});newref=[]"
new="""for sig0 in op['existing_SENSE_vias']:
 sig=hvia[sig0['uuid']];assert oldvia[sig['uuid']]['flashed']==['F.Cu','B.Cu']and sig['flashed']==['F.Cu','In2.Cu','B.Cu'];rad=sig['drill']/2+.25+.025
 template=(H/'Q0_retained_FLT_source_supported_aperture_r384.py').read_text().replace('support_FLT','support_SENSE').replace('a01ff36f-ac32-4648-88fe-29a54c58570b',sig['uuid']).replace('(228.25,157.65,.6,.3)',repr((sig['x'],sig['y'],sig['d'],sig['drill']))).replace('.575',repr(rad));sns={};exec(compile(template,str(H/'Q0_retained_FLT_source_supported_aperture_r384.py'),'exec'),sns);sh,sr=sns['support_SENSE'](K,before,h,oldbanks[GND],iv,sig,GND,K.L.norm(sig['net']),'In1.Cu');support[(sig['uuid'],'F.Cu')]=sh;sr.update(actual_reference_layer_old_flash=False,actual_reference_layer_old_width_mm=sig['drill'],same_plane_used_signal_layers=['F.Cu','In2.Cu'],same_plane_finite_continuity_source_NATIVE_SI_validation='OPEN; inherited no-paired-return FAIL preserved',exact_own_radius_mm=rad);supportrows.append(sr);(out/(sig['uuid']+'-exact-source-supported-In1-own-aperture.wkb')).write_bytes(sh.wkb)
put(out/'actual-paired-return-and-strong-own-scope-ledger.json',{'pairs':pairproof,'support':supportrows});newref=[]"""
assert old in code;code=code.replace(old,new,1)
code=code.replace('INDEPENDENT_ACTUAL_FILL_GEOMETRY_SOURCE_CONTACT_STRONG_TRACK_REFERENCE_INCREMENTAL_PASS_Q_NATIVE_PAD_CURRENT_OPEN','INDEPENDENT_GEOMETRY_CONTACT_SOURCE_REFERENCE_INCREMENTAL_PASS_SAME_PLANE_Q_NATIVE_PAD_CURRENT_OPEN').replace("'new_SMD_whole_body_reference_rows':newpad,","'new_SMD_whole_body_reference_rows':newpad,'SENSE_inherited_blanket_no_paired_return_checker':'FAIL retained; SAME_PLANE finite actual source-conductor proposal separate and OPEN',")
(H/'Q0-R454-independent-actual-reference-r456-derived-auditor.py').write_text(code)
exec(compile(code,str(base),'exec'))
