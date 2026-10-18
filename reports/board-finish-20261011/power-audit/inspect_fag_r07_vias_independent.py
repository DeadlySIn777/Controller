"""Independent exact native via/stub identity check; no native invocation."""
import hashlib
import json
import math
import re
from pathlib import Path
import prepare_sbc_c05_proposal as p

def xy(chunk, key):
    match=re.search(rb'\('+key.encode()+rb'\s+([-+0-9.e]+)\s+([-+0-9.e]+)',chunk)
    return [float(x) for x in match.groups()]

def main():
    source=p.OUT.parent/"fag-r07-screen/screen.json"
    screen=json.loads(p.read(source))
    donor=p.OUT.parent/"fag-r06/candidate/board.kicad_pcb"
    live=p.EXT/"integrate/revs/r07-ripup-signals-1.kicad_pcb"
    donor_data,live_data=p.read(donor),p.read(live)
    p.require(hashlib.sha256(donor_data).hexdigest()==screen["donor_sha256"],"donor changed")
    p.require(hashlib.sha256(live_data).hexdigest()==screen["live_board_sha256"],"r07 changed")
    donor_items=p.base.inventory(donor_data)[3]
    live_items=p.base.inventory(live_data)[3]
    owners={row["uuid"] for row in screen["rows"]}
    rows=[]
    for failure in screen["rows"]:
        if failure["kind"]!="via" or not failure["failures"]:
            continue
        uid=failure["uuid"]
        chunk=donor_items[uid]
        at=xy(chunk,"at")
        net=p.norm(p.netname(chunk))
        stubs=[]
        for tid,t in donor_items.items():
            if tid not in owners or p.base.pcbtext.chunk_kind(t)!="segment" or p.norm(p.netname(t))!=net:
                continue
            aa,bb=xy(t,"start"),xy(t,"end")
            if min(math.dist(aa,at),math.dist(bb,at))<1e-5:
                stubs.append({"uuid":tid,"start":aa,"end":bb,"chunk_sha256":hashlib.sha256(t).hexdigest(),"is_exact_owned_endpoint":True})
        neighbors=[]
        for item in failure["failures"]:
            other=live_items[item["uuid"]]
            p.require(p.base.pcbtext.chunk_kind(other)=="via","neighbor not native via")
            other_at=xy(other,"at")
            distance=math.dist(at,other_at)
            p.require(abs(distance-item["centre_mm"])<1e-8,"spacing mismatch")
            neighbors.append({"uuid":item["uuid"],"net":p.norm(p.netname(other)),"at":other_at,"distance_mm":distance,"same_net":p.norm(p.netname(other))==net,
                "size_mm":float(re.search(rb'\(size ([-+0-9.e]+)',other).group(1)),"drill_mm":float(re.search(rb'\(drill ([-+0-9.e]+)',other).group(1)),"chunk_sha256":hashlib.sha256(other).hexdigest()})
        rows.append({"owned_via_uuid":uid,"at":at,"net":net,"chunk_sha256":hashlib.sha256(chunk).hexdigest(),"owned_stub_contacts":stubs,"retained_native_neighbors":neighbors,
            "reuse_existing_via_is_geometry_lead_only":all(row["same_net"] for row in neighbors)})
    p.read(Path(__file__))
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    receipt={"evidence_class":"Exact native identities and owned stub endpoints only","verdict":"PASS_IDENTITIES_AND_SPACING","rows":rows,"read_set_sha256":p.READS,
        "limits":["Reuse must reroute all owned donor stubs without moving protected r07 copper","Actual source-anchored field return continuity, full-domain .6mm clearance, .8mm ordinary via spacing and donor-vs-donor geometry still require screening/native proof","Existing neighbor same net alone does not prove same electrically rooted plane piece","Four withdrawals are not yet an implemented corrected donor"],"native_jobs":0,"board_emitted":False}
    out=p.OUT.parent/"fag-r07-repair-independent-vias.json"
    out.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(out),"rows":rows}),flush=True)

if __name__=="__main__":
    main()
