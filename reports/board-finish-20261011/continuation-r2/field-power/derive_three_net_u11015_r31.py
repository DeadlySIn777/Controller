from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'repair_u11015_ilim_barrel_r26.py').read_text()
s=s.replace("OUT=HERE/'u11015-ilim-barrel-repair-r26'", "OUT=HERE/'u11015-three-net-outer-repair-r31'")
s=s.replace("owned=pr['owned_original_track_removals'];removed={q['uuid'] for q in owned};assert len(removed)==4", "dvscope=json.loads((HERE/'u11015-dvdt-scope-r30/receipt.json').read_text());dvold=dvscope['tracks'];assert len(dvold)==2;owned=pr['owned_original_track_removals']+dvold;removed={q['uuid'] for q in owned};assert len(removed)==6;outside=pr['exact_outside_contact_ledger'][:];dr0,_=F.build(g,nets={'/motherboard_power_entry/AUX24_A_DVDT'})\n for t in dvold:\n  sh=C.body(t);outside.append({'removed_original_track':t,'retained_same_raw_net_outside_contacts':[C.identity(q)|{'contact_Cu_area_mm2':sh.intersection(q['shape']).area} for q in dr0['B.Cu'] if q['uuid'] not in removed and sh.intersection(q['shape']).area>1e-9]})\n assert {q['uuid'] for row in outside[4:] for q in row['retained_same_raw_net_outside_contacts']}=={'71b4e700-5181-4c1e-87f6-5cb0b5998511','53303a9a-a99f-4da1-a500-5af3783fa537'}")
s=s.replace(" smd=[", " dnet='/motherboard_power_entry/AUX24_A_DVDT';dp0=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','8'));dp1=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('C11068','1'));draw=dp0['net'];assert draw==dp1['net'];do=[q['shape'].buffer(igap(q['net'])+.025) for q in rec['B.Cu'] if C.norm(q['net'])!=dnet]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']=='B.Cu' and C.norm(q['net'])!=dnet]\n for rule in g['rule_areas']:\n  if rule.get('no_tracks') and 'B.Cu' in rule['layers']:do.extend([s.buffer(.025) for s in C.poly(rule['outline'])])\n for rule in res['keepouts']:\n  if dnet not in exceptions.get(rule['name'],set()) and 'B.Cu' in rule['layers']:do.extend([s.buffer(.025) for s in C.poly(rule['outline'])])\n dt=STRtree(do)\n smd=[")
a=s.index(" def restore_ilim(");b=s.index(" dnet=",a)
ds=s[a:b].replace("def restore_ilim(groundbody,disk)","def restore_dvdt(groundbody,disk,ilimbody)").replace("ip0[","dp0[").replace("ip1[","dp1[").replace("it.query(","dt.query(").replace("io[int(j)]","do[int(j)]").replace("disk.buffer(.175)]", "disk.buffer(.175),ilimbody.buffer(.175)]")
b=s.index(" smd=[")
s=s[:b]+ds+s[b:]
s=s.replace("for radius in(.6,.9,1.2", "for radius in(.6,.75,.8,.9,1.2")
s=s.replace("if ir is None:continue\n         inner,", "if ir is None:continue\n         dr=restore_dvdt(rr['body'],disk,ir['body'])\n         if dr is None:continue\n         inner,")
s=s.replace("controller-U11015-ILIM-barrel-r26/", "controller-U11015-three-net-r31/")
needle="         (OUT/(uid+'.via-chunk')).write_text";i=s.index(needle)
s=s[:i]+'''         drids=[]
         for j,(aa,bb) in enumerate(zip(dr['points'],dr['points'][1:])):
          if aa==bb:continue
          sid=str(uuid.uuid5(uuid.UUID(uid),'DVDT-companion'+str(j)));tt={'uuid':sid,'net':draw,'layer':'B.Cu','a':aa,'b':bb,'w':.2,'prospective_not_native':True};newtracks.append(tt);drids.append(sid);newcu.append({'uuid':sid,'net':draw,'layer':'B.Cu','shape':C.body(tt)})
          (OUT/(sid+'.segment-chunk')).write_text('\\t(segment\\n\\t\\t(start %.6f %.6f)\\n\\t\\t(end %.6f %.6f)\\n\\t\\t(width %.2f)\\n\\t\\t(layer "B.Cu")\\n\\t\\t(net "%s")\\n\\t\\t(uuid "%s")\\n\\t)\\n'%(*aa,*bb,.2,draw,sid),encoding='utf-8',newline='')
''' +s[i:]
s=s.replace("'ILIM_restore_segment_UUIDs':irids};break", "'ILIM_restore_segment_UUIDs':irids,'DVDT_restore_route':{k:v for k,v in dr.items() if k!='body'},'DVDT_restore_segment_UUIDs':drids};break")
s=s.replace("'exact_outside_contact_ledger':pr['exact_outside_contact_ledger']", "'exact_outside_contact_ledger':outside,'C11068_timing_cap_value_pose_and_U11015_DVDT_pin_role_unchanged':True")
(P/'repair_u11015_three_net_outer_r31.py').write_text(s,encoding='utf-8');compile(s,'repair_u11015_three_net_outer_r31.py','exec');print('derived',len(s))
