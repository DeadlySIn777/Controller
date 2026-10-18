"""Preserve R154 completed proofs; correct its quadratic track-ID lookup."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'audit_U10003_sparse_drilled_source_contacts_r154.py';old=H/'U10003-sparse-drilled-source-contact-independent-r154'
proofs=[old/'two-net-retained-drilled-contact-proof.json',old/'actual-drilled-source-rooted-new-ground.json'];assert all(p.exists()for p in proofs)
stop=old/'deliberate-owned-host-stop-receipt.json';assert not stop.exists();stop.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Only root-owned host audit35088 stopped after completed physical source/contact checks; faulty list comprehension rebuilt86k originaltrackUUIDs once for every86k currenttrack. Native mainCLI78520 untouched.','completed_proofs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in proofs},'electrical_failure_inferred':False,'replacement_has_identical_geometry_and_check_thresholds':True,'native_jobs_stopped':0},indent=1)+'\n')
code=source.read_text();code=code.replace('independent-r154','independent-r156')
needle="faults=[t for t in h['tracks']if t['uuid']not in{t['uuid']for t in h0['tracks']}and C.norm(t['net'])==FAULT]";assert code.count(needle)==1
code=code.replace(needle,"old_track_UUIDs={t['uuid']for t in h0['tracks']};faults=[t for t in h['tracks']if t['uuid']not in old_track_UUIDs and C.norm(t['net'])==FAULT]")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
