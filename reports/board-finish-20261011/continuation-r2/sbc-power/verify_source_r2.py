import json,re,hashlib,math
from pathlib import Path
import source_correction_r2 as S
def main():
    root=S.SRC.read_bytes();dest=S.HERE/'source-proposal-r2/motherboard_power_entry.kicad_sch';candidate=dest.read_bytes()
    # Match the complete newly inserted five top-level source records, then undo
    # only the explicitly declared inductor values to recover the original bytes.
    lines=candidate.splitlines(keepends=True)
    capref=candidate.index(b'(property "Reference" "C11094"');start=candidate.rfind(b'  (symbol ',0,capref)
    last_uuid=b'f683ae53-17dc-5595-b94a-6d0c7e296c29';end=candidate.index(b'\n',candidate.index(last_uuid))+1
    block=candidate[start:end];rest=candidate[:start]+candidate[end:]
    restored=rest.replace(b'"6.8uH 20%"',b'"4.7uH 20%"').replace(b'"XAL1010-682MED"',b'"XAL1010-472MED"')
    assert restored==root
    positions=[]
    for line in lines:
        m=re.search(rb'^  \(symbol .*?\(at ([\d.-]+) ([\d.-]+).*?\(property "Reference" "([^"]+)"',line)
        if m:positions.append((m[3].decode(),float(m[1]),float(m[2])))
    distances=sorted((math.hypot(x-762,y-3329.88),ref,x,y) for ref,x,y in positions if ref!='C11094')
    uuids=re.findall(rb'\(uuid "([^"]+)"\)',candidate);assert len(uuids)==len(set(uuids))
    manifest=json.loads((S.HERE/'source-proposal-r2/integrated-power-source.json').read_text())
    c=manifest['power_entry_components'];assert c['C11094']['pins']==c['C11088']['pins']
    receipt={'verdict':'HOST_SOURCE_STRUCTURE_PASS_NATIVE_EXPORT_ERC_OPEN','source_original_recovered_bytes_exact':True,'unique_uuid_count':len(uuids),'new_capacitor_to_nearest_source_symbol_mm':distances[:5],'new_block_records':5,'all_shutdown_capacitor_parts_preserved':all(r in c for r in ('C11089','C11090','C11091')),'new_cap_pin_binding':c['C11094']['pins'],'new_reference_unique_full_ROOT106':manifest['new_reference'] not in manifest['all_existing_component_refs'],'source_sha256':hashlib.sha256(root).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest(),'native_jobs':0}
    (S.HERE/'source-proposal-r2/host-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
