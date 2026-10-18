"""Explicit corrected raw-native net binding, preserving first host spelling proof."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy
from pathlib import Path
from inventory import sha
from contact_layout import norm
HERE=Path(__file__).resolve().parent;OUT=HERE/'field-contact-repair-r2-raw'
def main():
    assert not OUT.exists();OUT.mkdir();before=HERE/'field-contact-repair-r1';r=json.loads((before/'receipt.json').read_text());base=HERE/'logic-return-contact-audit-r1';br=json.loads((base/'receipt.json').read_text());assert sha(base/'geometry.pkl')==br['geometry_sha256'];h=pickle.loads((base/'geometry.pkl').read_bytes());raw={norm(q['net']):q['net'] for q in h['pads'] if q['ref'] in {'J11003','J11005'} and q['num']=='2'};assert set(raw)=={'/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V'}
    # A normalized lookup token is not a valid newly serialized KiCad net name.
    # Preserve its original host receipt and make the spelling failure explicit.
    diagnostic={'verdict':'REJECT_NEW_SERIALIZATION_RAW_NAME_MISMATCH','superseded_receipt_sha256':sha(before/'receipt.json'),'raw_native_tokens':raw,'explanation':'r1 used normalized slash tokens for lookup and recorded them in proposed serialized net fields. No native board/chunks were emitted. r2 replaces only those proposal net fields with the exact existing native raw tokens; it does not introduce aliases.','native_jobs':0,'board_written':False}
    (OUT/'superseded-spelling-failure.json').write_text(json.dumps(diagnostic,indent=1)+'\n');assert sha(before/'proposed-zones.pkl')==r['proposal_sha256'];zz=pickle.loads((before/'proposed-zones.pkl').read_bytes());new=[];corrections=[]
    for z in zz:
        token=raw[norm(z['net'])];new.append({**z,'net':token});corrections.append({'uuid':z['uuid'],'from_lookup_token':z['net'],'to_existing_raw_native_token':token,'geometry_wkb_sha256_unchanged':__import__('hashlib').sha256(z['shape'].wkb).hexdigest()})
    rr=copy.deepcopy(r)
    for q in rr['rows']:
        q['net_raw']=raw[norm(q['net_raw'])]
        if q['repair']:q['repair']['net_raw']=raw[norm(q['repair']['net_raw'])]
    (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(new,protocol=5));rr.update(schema='field-contact-repair-exact-raw-r2',proposal_sha256=sha(OUT/'proposed-zones.pkl'),superseded_r1_receipt_sha256=sha(before/'receipt.json'),explicit_spelling_failure_receipt_sha256=sha(OUT/'superseded-spelling-failure.json'),exact_existing_raw_tokens=sorted(set(raw.values())),raw_spelling_corrections=corrections,raw_aliases_introduced=False,native_jobs=0,board_written=False);(OUT/'receipt.json').write_text(json.dumps(rr,indent=1)+'\n');print(json.dumps({'corrections':len(corrections),'raw_tokens':raw,'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
