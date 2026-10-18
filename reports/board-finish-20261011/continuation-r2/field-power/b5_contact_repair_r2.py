"""Corrected normalized lookup / exact raw serialization split, preserving r1 rejection."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
text=(HERE/'b5_contact_repair_r1.py').read_text().replace("OUT=HERE/'b5-contact-repair-r1'","OUT=HERE/'b5-contact-repair-r2'")
needle="exec(compile(text,str(path),'exec'))"
inject="""text=text.replace('exec(compile(text,str(path),\\'exec\\'))', '''text=text.replace("C.norm(t['net'])!=NET", "C.norm(t['net'])!=lookupNET").replace("C.norm(v['net'])==NET", "C.norm(v['net'])==lookupNET").replace("C.norm(p['net'])!=NET", "C.norm(p['net'])!=lookupNET").replace("C.norm(z['net'])!=NET", "C.norm(z['net'])!=lookupNET")
text=text.replace("'native_jobs':0};adds.append", "'native_jobs':0,'normal_complete_B5PRE_load_A':0.132585384615,'proposed_routing_target_A':0.14};adds.append")
exec(compile(text,str(path),'exec'))''')
exec(compile(text,str(path),'exec'))"""
assert text.endswith(needle+'\n')
text=text[:-len(needle+'\n')]+inject+'\n'
exec(compile(text,str(HERE/'b5_contact_repair_r1.py'),'exec'))
