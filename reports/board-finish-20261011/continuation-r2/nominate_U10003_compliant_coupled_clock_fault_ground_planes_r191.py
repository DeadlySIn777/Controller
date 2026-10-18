"""Reference nominee for exact coupled wall repair and both compliant returns."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_two_signal_port_ground_reference_r172.py';code=source.read_text()
code=code.replace('source-seeded-ground-reference-nomination-r172','compliant-coupled-clock-fault-ground-reference-nomination-r191')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20')
start=code.index(" packet=H/'U10003-additional-signal-port-old-In3-preserved-nomination-r171'");end=code.index(" replace={'9fe010df",start)
replacement="""
 packet=H/'U10003-exact-clock-fault-coupled-ground-return-nomination-r187';assert sha(packet/'receipt.json')=='47aa48549ef51e3543d32caa2f2c045f155793c94488c27f1716f9ac16434ba0';joint=pickle.loads((packet/'proposed-sparse-delta.pkl').read_bytes())
 apr=H/'U10003-exact-actual-paired-old-A-return-after-coupled-clock-ground-faces-r190/receipt.json';assert sha(apr)=='5859a69aac986e19753bf40cb0ead48d41fccf4237706ba4a2a9c5acf796e903';nom=json.loads(apr.read_bytes())['nominees'];assert len(nom)==1
 sig=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');central=joint['replace_only_unadopted_ground_barrel'];raw=central['net'];ret={**next(v for v in h['vias']if v['uuid']=='73811c12-9f84-5491-bfee-0c5ee985a7a8'),'x':nom[0]['site_mm'][0],'y':nom[0]['site_mm'][1]}
 delete={t['uuid']for t in joint['delete_original_tracks']}|{joint['replace_only_unadopted_ground_stub']};moveids={central['uuid'],ret['uuid']}
 prior=pickle.loads((H/'U10003-additional-signal-port-old-In3-preserved-nomination-r171/proposed-sparse-delta.pkl').read_bytes());faulttracks=[next(t for t in h['tracks']if t['uuid']==n['uuid'])for n in prior['tracks']];assert len(faulttracks)==4
 d={'tracks':faulttracks+joint['new_tracks'],'new_tracks':joint['new_tracks'],'new_ordinary_signal_via':sig,'delete_tracks':[t for t in h['tracks']if t['uuid']in delete],'ground_owned_local_negative_withdrawal_UUIDs':['bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a'],'replace_only_unadopted_ground_vias':[central,ret],'exact_joint_packet':joint}
 hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in delete]+joint['new_tracks'],'vias':[v for v in h['vias']if v['uuid']not in moveids]+[central,ret]};records,trees=F.build({**hard,'zones':[]})
"""
code=code[:start]+replacement+code[end:]
code=code.replace("sourceview={**full,'zones':[q for q in full['zones']if q['uuid']not in replace]}","sourceview={**full,'tracks':hard['tracks'],'vias':hard['vias'],'zones':[q for q in full['zones']if q['uuid']not in replace]}")
needle="bodies=unary_union([C.body(t)for t in d['tracks']]+[C.body(t)for t in h['tracks']if C.norm(t['net'])==FG and t.get('prospective_not_native')and t['layer']=='B.Cu'])";assert code.count(needle)==1;code=code.replace(needle,"bodies=unary_union([C.body(t)for t in d['tracks']])")
needle="'new_signal_fullbody_raw_reference_gap_mm2':rawgap.area";assert code.count(needle)==1
code=code.replace(needle,needle+",'per_net_new_and_retained_nominee_body_raw_gap_mm2':{net:unary_union([C.body(t)for t in d['tracks']if C.norm(t['net'])==net]).difference(oldref[layer].union(physical)).area for net in sorted({C.norm(t['net'])for t in d['tracks']})}")
needle="'same_old_native_barrel_B_In3_geometry_untouched':True";assert code.count(needle)==1
code=code.replace(needle,needle+",'exact_native_clock_fault_four_track_replacements':sorted(delete-{joint['replace_only_unadopted_ground_stub']}),'signal_return_distances_mm':[Point(sig['x'],sig['y']).distance(Point(central['x'],central['y'])),Point(oldsignal['x'],oldsignal['y']).distance(Point(ret['x'],ret['y']))],'saved_operator_window_mm':[.90,1.0],'exact_R190_A_return_receipt_sha256':sha(apr)")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
