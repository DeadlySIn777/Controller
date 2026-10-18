from pathlib import Path
import shutil,json,hashlib
P=Path(__file__).resolve().parent;S=P/'record-config-replay-candidate-r01';O=P/'stage-r02'
shutil.copytree(S,O,ignore=shutil.ignore_patterns('bundle-manifest.json','__pycache__'))
t=(O/'target.c').read_text()
old='inspect_factory_flash();\n    slot_valid=fitted_slot()==NODE_SLOT;'
assert t.count(old)==1 and t.count('    watchdog_start();')==1
t=t.replace(old,'''/* Start the real independent watchdog before reading factoryflash.
     * A corrupt ECC read/NMI must not hang forever without this watchdog.
     * Hardware reset/timing/options still require physical qualification. */
    watchdog_start();
    inspect_factory_flash();
    slot_valid=fitted_slot()==NODE_SLOT;''').replace('    watchdog_start();\n    /* DS12992','    /* DS12992')
(O/'target.c').write_text(t,newline='\n')
c=(O/'test_record_config.c').read_text().replace('uint8_t record[4][512],uid[4][12];','uint8_t record[4][512],new_record[4][512],uid[4][12];').replace('"exact4 records");fclose(file);','"exact4 records");CK(fread(new_record,1,sizeof(new_record),file)==sizeof(new_record),"exact4 successor records");fclose(file);')
c=c.replace('"identicalduplicate coherent");','''"identicalduplicate coherent");
  CK(mb_record_select(record[s],new_record[s],cls[s],s,uid[s])==1,"newersignedgeneration selected");
  CK(mb_record_select(new_record[s],record[s],cls[s],s,uid[s])==0,"newersignedgeneration independent ofslotorder");''')
c=c.replace('"torn doubleword prefix rejected including missing commit");','''"torn doubleword prefix rejected including missing commit");
   CK(mb_record_select(record[s],torn,cls[s],s,uid[s])==0,"every torn successor prefix preserves priorpage");''')
(O/'test_record_config.c').write_text(c,newline='\n')
r=(O/'run_record_config.py').read_text().replace("(out/'fixtures.bin').write_bytes(b''.join(records));", "successors=[fixture_record(s,uids[s],generation=2)[0] for s in range(4)]\n (out/'fixtures.bin').write_bytes(b''.join(records+successors));")
(O/'run_record_config.py').write_text(r,newline='\n')
r=(O/'run_mutations.py').read_text()
r=r.replace("b''.join(record_host.fixture_record(s,bytes(s*16+i+1 for i in range(12)))[0] for s in range(4))", "b''.join(record_host.fixture_record(s,bytes(s*16+i+1 for i in range(12)),generation=g)[0] for g in [1,2] for s in range(4))")
(O/'run_mutations.py').write_text(r,newline='\n')
# This prototype never writes runtime flash. Preserve exact prior candidate and
# record the cold-order/two-page test changes without promoting shared sources.
(O/'stage-r02-delta.json').write_text(json.dumps({'prior_bundle_sha256':hashlib.sha256((S/'bundle-manifest.json').read_bytes()).hexdigest(),'changes':['software IWDG start before actual factoryflashread','actual C olderpage survival at all64 torn successor prefixes','actual C two signed generation selection, both slotorders'],'authority_or_hardware_proof':False},indent=2)+'\n')
print(O)
