from pathlib import Path
import hashlib, json, shutil
P=Path(__file__).resolve().parent
S=P/'stage-r03'
O=P/'record-config-replay-candidate-r03'
ROOT=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=P/'record-config-replay-candidate-r02'
assert sha(prior/'bundle-manifest.json')=='d7646cf88030d5a266465beaa95fe56c6f6cc914a52d8f9eacef0951bc5d74f4'
originals=json.loads((S/'original-source-retention.json').read_text())
for name,hash_value in originals['files'].items():
 assert sha(ROOT/'firmware/motherboard_iol1_readonly'/name)==hash_value,name
assert sha(ROOT/'hardware/motherboard/design.json')==originals['electrical_source_design_sha256']
delta=json.loads((S/'stage-r03-delta.json').read_text())
delta['changes']+=['SPI continues1050 accepted polls while sampling stalled beyond65ms; actual same-C helper keeps ageFFFF untilresample',
 'torn page prefix control now uses actualgeneration2successor, notpriorgeneration1prefix; priorr02retained',
 'CRC-valid samegeneration descriptor conflict andhighergeneration source-lineage mismatch failclosed; noauthenticationclaim']
(S/'stage-r03-delta.json').write_text(json.dumps(delta,indent=2)+'\n')
readme=(S/'README.md').read_text()+'''
Peer review found a retained DIC sample-age wrap in r02. Successor r03 uses one
actual shared C age helper in the real DIC/DO target paths: FFFF is unavailable,
65534 remains representable, and both65535/65536 saturate. Cold DIC data is
unavailable until an actual sampled tuple commits. Once stale, the validity
latch remains invalid until a fresh sample, so a full32-bit timestamp wrap cannot
revive old data. Same-C boundary/rollover tests and a compiled truncation mutation
cover it. The SPI fixture also services1050 real accepted polls with sampling
explicitly disabled, retains old samples withFFFF age, then requires a resample.
This is not execution of the target GPIO/DMA/IRQ or proof of hardware poll jitter.

The final actual C interrupted-page control uses generation2 successor prefixes,
and conflicting same-generation/foreign-source diagnostic records fail closed.
Those C records are integrity-valid only; target signature authentication remains
absent and the separately supplied host trust registry cannot grant production.
'''
(S/'README.md').write_text(readme,newline='\n')
if O.exists():raise RuntimeError('fresh frozen bundle required')
shutil.copytree(S,O,ignore=shutil.ignore_patterns('__pycache__'))
files={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file()}
(O/'bundle-manifest.json').write_text(json.dumps({'files':files,'frozen':True,'proposal_not_live_adoption':True},indent=2)+'\n')
r={'bundle':str(O),'manifest_sha256':sha(O/'bundle-manifest.json'),'file_count':len(files),
 'prior_r02_manifest_sha256':sha(prior/'bundle-manifest.json'),'original_shared_firmware_and_Source26_unchanged':True,
 'real_factory_provisioning_or_output_authority':False}
(P/'record-config-r03-freeze.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
