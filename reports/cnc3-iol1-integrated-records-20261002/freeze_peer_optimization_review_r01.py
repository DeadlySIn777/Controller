"""Read-only source/evidence review; no HDL execution, promotion or board writes."""
from pathlib import Path
import hashlib, json, re, difflib
ROOT=Path.cwd()
R=ROOT/'reports/cnc3-iol1-integrated-records-20261002'
C=R/'prefix-record-candidate-r01'
OUT=R/'peer-prefix-optimization-review-r01'
OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def normalized(s):return re.sub(r'\s+','',s)
manifest=read(C/'bundle-manifest.json')
assert sha(C/'bundle-manifest.json')=='40d985aa68b61d8c4994cc9631a21a09657be834bddd4c50b5d53daf032485e7'
verified={name:sha(C/name) for name in manifest['files']}
assert verified==manifest['files']

receipts=[R/'timer-share-formal-r01/receipt.json',R/'timing-width-formal-r02/receipt.json',R/'crc-share-combinational-formal-r03/receipt.json',R/'prefix-arithmetic-stage-r01/receipt.json',R/'record-compare-stage-r01/receipt.json',R/'prefix-record-full-r01/report.json',R/'prefix-record-full-r01/composed_family_mapping/receipt.json']
evidence=[]
for p in receipts:
    row=read(p)
    assert row['status']=='PASS'
    field='original_inputs' if 'original_inputs' in row else 'exact_inputs' if 'exact_inputs' in row else 'input_hashes'
    source=row.get(field,{})
    for name,digest in source.items():
        path=Path(name) if Path(name).is_absolute() else C/name
        assert sha(path)==digest,(p,name)
    evidence.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),verified_input_hashes=len(source),evidence_reused_not_rerun=True))

# Independently invert each of the 15 documented source rewrites. Other source
# tokens must match the immutable parents after removing only the two helpers.
ledger=read(R/'record-compare-stage-r01/receipt.json')['exact_transform_ledger']
helper=r'function u_ge32;.*?endfunction\s*function u_le32;.*?endfunction\s*'
transform_checks=[]
for module in ['cnc_iol1_record_master.v','cnc_mbr2_stream_checker.v']:
    stage=R/'record-compare-stage-r01'/module
    prior=Path(str(stage)+'.prior')
    old=prior.read_text(encoding='utf-8')
    new=stage.read_text(encoding='utf-8')
    assert (C/module).read_bytes()==stage.read_bytes()
    restored,n=re.subn(helper,'',new,count=1,flags=re.S)
    assert n==1
    selected=[row for row in ledger if row['module']==module]
    for row in selected:
        assert restored.count(row['new'])==row['occurrences'],row
        restored=restored.replace(row['new'],row['old'])
    assert normalized(restored)==normalized(old),module
    (OUT/(module+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(prior.relative_to(ROOT)),tofile=str(stage.relative_to(ROOT)))),encoding='utf-8')
    transform_checks.append(dict(module=module,old_sha256=sha(prior),new_sha256=sha(stage),ledger_rows=len(selected),all_other_source_tokens_unchanged=True))

# CRC selection is combinational, and only the original three update scopes
# change. Final PREP uses the same octet because prep_index must equal 35.
crc_old=R/'crc-share-stage-r01/cnc_iol1_record_master_original.v'
crc_new=R/'crc-share-stage-r01/cnc_iol1_record_master.v'
old=crc_old.read_text(encoding='utf-8');new=crc_new.read_text(encoding='utf-8')
shared=r'    // PREP and SHIFT are mutually exclusive\..*?\{rx_shift\[6:0\],miso\}\);\n'
restored,n=re.subn(shared,'',new,count=1,flags=re.S);assert n==1
for before,after in [
('tx_crc <= crc_byte(tx_crc,octet(tx_frame,{26\'b0,prep_index}));','tx_crc <= shared_crc;'),
('tx_frame[31:0] <= crc_byte(tx_crc,octet(tx_frame,35)) ^ 32\'hffffffff;','tx_frame[31:0] <= shared_crc ^ 32\'hffffffff;'),
('rx_crc <= crc_byte(rx_crc,{rx_shift[6:0],miso});','rx_crc <= shared_crc;')]:
    assert restored.count(after)==1
    restored=restored.replace(after,before)
assert normalized(restored)==normalized(old)
(OUT/'crc-master-delta.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(crc_old.relative_to(ROOT)),tofile=str(crc_new.relative_to(ROOT)))),encoding='utf-8')

runtime=(C/'inputs/motion/cnc3_stepgen_runtime.v').read_text(encoding='utf-8')
top=(C/'inputs/motion/cnc3_motion_spi.v').read_text(encoding='utf-8')
state=(C/'inputs/motion/cnc3_motion_state.v').read_text(encoding='utf-8')
validator=(C/'inputs/motion/inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v').read_text(encoding='utf-8')
assert 'parameter integer TIMER_BITS=16' in runtime
assert '#(.TIMER_BITS(10))' in top
assert runtime==(R/'prefix-arithmetic-stage-r01/cnc3_stepgen_runtime.v').read_text(encoding='utf-8')
assert 'pulse_ticks[191-16*i -:16]<=100;space_ticks[191-16*i -:16]<=100;' in state
assert 'setup_ticks[191-16*i -:16]<=100;hold_ticks[191-16*i -:16]<=100;' in state
assert validator.count("32'd100) && u_le32(")>=48 and validator.count("32'd1023)")>=48

report=read(R/'prefix-record-full-r01/report.json')
assert report['counts']==dict(PASS=4,FAIL=0,BLOCKED=0,NOT_RUN=0)
for stage in report['stages']:
    assert sha(Path(stage['receipt']))==stage['receipt_sha256']
mapping=read(R/'prefix-record-full-r01/composed_family_mapping/receipt.json')
assert mapping['mapped_resources']['EFX_LUT4']+mapping['mapped_resources']['EFX_ADD']==19477
assert mapping['vendor_T20_fit_timing_bitstream'] is False
assert verified=={name:sha(C/name) for name in manifest['files']}
receipt=dict(status='PASS',scope='Bounded read-only source review of timer sharing, actual ten-bit timer composition, selected byte CRC sharing, count/magnitude prefix arithmetic and exact unsigned record comparisons in frozen prefix-record-candidate-r01.',manifest_sha256=sha(C/'bundle-manifest.json'),all_manifest_files_verified=len(verified),source_files=verified,evidence=evidence,exact_record_transform_checks=transform_checks,exact_CRC_update_scopes=3,actionable_semantic_findings=[],review_notes=[
'HIGH/LOW/SETUP are mutually exclusive in reset-reachable original state. One delay preserves the aliases; DIR hold remains independent. Stop continues to drain STEP, LOW and DIR hold. Quiescent intentionally retains the original setup omission.',
'Standalone default TIMER_BITS stays 16. Only the actual motion top selects 10 after the original 100..1023 static admission; cold timing is 100. The 0..1023 formal premise is a constraint, not validity of larger values on the ten-bit instance.',
'CRC selector uses TX only during PREP; final prep_index==35 selects the same last TX octet. SHIFT complete-byte updates use the RX value with the same sample phase/index predicate. Reset/CS/sequence/response metadata and authority logic are otherwise token-identical.',
'count_next is modulo-2^32 increment/decrement. magnitude_next preserves two-complement unsigned magnitude including INT_MIN; this does not change the independently enforced rate admission.',
'All 15 comparison transforms retain explicit unsigned zero extensions and constants. Inversion reproduces every other parent token. Current queue-fault/final record-failure priority and hard-false signature/factory/commercial authority remain retained.',
'Primary equivalence/formal/replay evidence was hash-checked and inspected, not newly executed by this review.'
],limits=[
'Proofs are two-state/reset-reachable logic evidence, not physical CDC/metastability or four-state equivalence.',
'The CRC formal result proves selected next-CRC math only; the aborted full three-class temporal run is not accepted.',
'Current 19477 LUT4+ADD leaves 251 LEs against the coarse 19728 budget for this incomplete composition only. It excludes CAP3, complete providers and output authority; no vendor fit, placement, timing or bitstream claim.',
'No source, PCB, frozen bundle, runtime authority, waveform rating or architecture was changed or promoted.'
],source_inputs_unchanged=True,new_tests_run=False,public_adoption=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(path=str((OUT/'receipt.json').relative_to(ROOT)),sha256=sha(OUT/'receipt.json'),verified_files=len(verified),status='PASS',new_tests_run=False),indent=2))
