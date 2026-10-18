"""Keep R172 overbroad proposal frozen; use only the exact owned U10003 stub."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_two_signal_port_ground_reference_r172.py';code=source.read_text()
code=code.replace('source-seeded-ground-reference-nomination-r172','exact-stub-source-seeded-ground-reference-nomination-r173')
needle="bodies=unary_union([C.body(t)for t in d['tracks']]+[C.body(t)for t in h['tracks']if C.norm(t['net'])==FG and t.get('prospective_not_native')and t['layer']=='B.Cu'])"
replace="""stubauthority=H/'U10003-fault-ground-source-barrel-reference-bridge-nominee-r150/receipt.json';assert sha(stubauthority)=='7f3538a6d8abad28ed6a468a27d2629df5647e98c641e3e2157e7b2ba5f23698'
 oldstub=json.loads(stubauthority.read_bytes())['B_ground_stub'];actualstub=next(t for t in h['tracks']if t['uuid']==oldstub['uuid']);assert actualstub==oldstub
 bodies=unary_union([C.body(t)for t in d['tracks']]+[C.body(actualstub)])"""
assert code.count(needle)==1;code=code.replace(needle,replace)
needle="'old_proposed_ground_roles_withdrawn_before_source_seed':True"
assert code.count(needle)==1;code=code.replace(needle,needle+",'only_exact_owned_U10003_ground_stub_included':True,'ground_stub_UUID':oldstub['uuid'],'ground_stub_authority_sha256':sha(stubauthority)")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
