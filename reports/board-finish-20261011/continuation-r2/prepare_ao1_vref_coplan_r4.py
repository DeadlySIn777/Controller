"""Preserve failed r3 and correct the frozen A* endpoint-record API."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=HERE/'probe_ao1_vref_coplan_r3.py'
text=prior.read_text()
changes=[("OUT = HERE / 'ao1-vref-coplan-r3'","OUT = HERE / 'ao1-vref-coplan-r4'"),
 ("parent=HERE / 'combined-power-source-native-r1/combined-power-source-host-only.kicad_pcb'","parent=HERE / 'combined-power-source-native-r3-c92/combined-power-source-c92-corrected.kicad_pcb'"),
 ("65065e41b8243fe150a2231c17bbe8203dd0c4bb3fdbb2b1e0554ff9e14fbd41","45c85ce62a624b3dc31127534a7fd434bf5bedac560da046538542d10395c603"),
 ("smd.query(hole.buffer(.125)","smd.query(hole.buffer(.275)"),
 ("path,details=S.astar(free,[start],[goal],time.monotonic()+12,node_cap=120000)","path,details=S.astar(free,[(start,{'uuid':pad_id,'kind':'pad'})],[(goal,{'uuid':'prospective_analog_via','kind':'via'})],time.monotonic()+12,node_cap=120000)")]
for old,new in changes:
    if text.count(old)!=1:raise ValueError('Derivation marker not unique: '+old)
    text=text.replace(old,new,1)
marker="    attempts=[]\n"
if text.count(marker)!=1:raise ValueError('Cache marker differs')
text=text.replace(marker,"    (OUT/'site-screen.json').write_text(json.dumps({'rows':rows,'SMD_drill_margin_mm':.275,'input_hashes':A.READS},indent=1)+'\\n',encoding='utf-8')\n"+marker,1)
out=HERE/'probe_ao1_vref_coplan_r4.py'
if out.exists():raise ValueError('Fresh derived probe required')
out.write_text(text,encoding='utf-8')
record={'prior_script_sha256':sha(prior),'new_script_sha256':sha(out),'exact_replacements':changes,'failed_r3_preserved':True,'failure':'TypeError in endpoint-record A* API; no board was emitted','SMD_hole_clearance_strengthened_mm':.275,'no_other_geometry_threshold_change':True}
(HERE/'ao1-vref-coplan-r4-derivation.json').write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8')
print(json.dumps(record))
