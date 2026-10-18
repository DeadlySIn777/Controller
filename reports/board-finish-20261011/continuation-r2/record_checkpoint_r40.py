"""Record the combined native run and exact retained/conditional scope."""
import json,hashlib,datetime,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r39.json';c=read(prior);c['previous_checkpoint_sha256']=sha(prior);c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256']
native=H/'combined-R753-one-full-native-fill-cached-DRC-r299';ns=read(native/'native-full/status.json');assert ns['phase']=='FULL_ALL_NET_CPP_FILL_RUNNING'
assert read(native/'native-full/before-native-Cu-errors.json')==[]
c['continuing_work'].update({
 'combined_native_active':'R753 exact R157 sparse known-failure diagnostic7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2 staged, manifest50016f4c. FIELD/R731 + ROOT/R271 + Q0/DIC/DI6/R588 only; original locked fullCORE5dc1a retained and SBC379/398/unqualifiedCORE353/371 excluded. All unlisted native chunks/header/tail exact;86432segments8016vias2723FP850zones. R297/R300 independent exact serialized integer Cu+locked ledger94448Cu/67changes/10newvias/13newordinaryall6; all8006baseline actual nativeviaUIDs retained, no retirement exemptions. R757 revised staticreview b05fdfa6 pins R298e7a76e47/R29970a4bafa. Existingmain1 all-net CPP Fill started00:00:37.698918UTC/PID70888, exactnative beforeCuerrors0. One sameboard allzone fill/native partitions/geometry/masks then only separate genuineCPP-filled diagnostic copy; saved reload Cu/pose/masks must match before CLI test-only1 without redundant refill. Original fullR157CLI PID54240 remains uninterrupted. All source/contact/oldrefs/current/SI/DRC/fab gatesOPEN/rawFAIL held.',
 'actual_current_native_header':'R753 sharedcf2a/e2fe/7ef negative scopes have zero gains, explicit integer boundary negative redesigns; raw R743/745/747/749/751 and attribution failures remain bound. R755 metadata supplement corrects six wrongly negated no-PASS flags, does not change board/ledger. No blanket remoteedge-preservation certificate; allnative/source/reference review required.',
 'CORE_current':'R290 actual fullR157 CORE16body In1shadow screen:11unfillable bypositiveonly, realFIELD_B0V d8d8 and FIELD_B24V93fd block; nofieldplane carving. R291 centre-axis representation blocked .95LGpair/full1.25cap; only exact ownedROOT host stoppedR293, graphs/rows retained. R295 actual SOURCE after originalmiddle withdrawal8180keys; side-annular/loadport onLGIn4, all field/currenthard/nativeLGIn3normalretreat-onlypending gate,21ROItargets0routes. This bounded screen is notglobalno-path. SBC R408 actual loadport is isolated37.81mm² reference-axis pocket35.632mm fromSOURCE In2; ONLY-NEWCMcounterfactual52.43mm² still28.774mm away. New loadport/Fspur topology at rightanchor under investigation, original fulltrunk retained incombinedcandidate.',
 'SBC_current_scope':'R296 fullnative IO3 census:22groups/R18001.2SOURCE3663layerkeys; olda20/3945/6007 allalready sameSOURCE/allobserved6layers. R404 necessity exclusion36c72493 supersedesR402: exclude saved35.56mmIO3bypass andR7035move fromfirstcurrentR157combinedcandidate, preserve asconditionalrepair ifeventualCOREreplacement splitsIO3. No historicalR371 source equivalence.',
 'Q0_DIC_latest':'R588 exactQ0/DIC/DI6native manifest1c7fba1a/receipt17fc47a1 freezes62discreteoperations andR10016onlypose. R582 DI6incrementalall84oldnet/direct/ten-source/strictoldref89geometry/fullnewbody/sourcepair.900998/targetpair.970824/r06fourpadjoinedPASS. R586 actualfullR157 target/native masks/sourceannuli and exact575000IU cap/localno-otherCu/nozones cause bindingPASS; actualAFTER native/source/SI remainsOPEN. DI15 actual originaltwo isolated bareF pads have no nativeports; R594 five physicalIn2paths but no commonJ1In1support. Saved8point path2.128386mm²missing reference; additive actualsource-supported In1 extension/blocker attribution isnext.',
 'resource_alarm':'R33 completed. R34activePID75020 from23:34:30.747094UTC→00:34:30.747080UTC, CPU70%/GPU80C350W unchanged. R35scheduled00:34:20.747080UTC with10sec overlap, session69419. No extra heavy slots.'})
paths=[
 'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/receipt.json',
 'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/final-stage-manifest.json',
 'field-power/R753-frozen-metadata-clarification-and-native-runner-static-review-r755/receipt.json',
 'field-power/revised-R298-R299-all-net-native-static-review-r757/receipt.json',
 'combined-R753-serialized-all-Cu-expected-r297/receipt.json',
 'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/receipt.json',
 'combined-R753-one-full-native-fill-cached-DRC-r299/launch-and-inputs.json',
 'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-Cu-errors.json',
 'CORE5-R390-actual-full-native-In1-source-shadow-blocker-screen-r290/receipt.json',
 'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r291/owned-host-centre-axis-stop-r293.json',
 'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295/receipt.json',
 'actual-full-R157-IO3-source-saved-bypass-necessity-r296/receipt.json',
 'sbc-power/R379-R398-actual-R157-necessity-exclusion-r404.json',
 'coupled-recovery/Q0-DIC-DI6-exact-R157-minimal-sparse-native-replay-manifest-r588/receipt.json',
 'resource-watch-arm-derivation-r35.json']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for label,pid,needle in [('R157_full_CLI',54240,'kicad-cli.exe'),('R299_full_native_CPP',70888,'native_combined_all_net_fill_and_real_saved_cache_r298.py')]:
 p=psutil.Process(pid);args=p.cmdline();assert needle in' '.join(args);c['native_scope_jobs'][label]={'PID':pid,'create_time':p.create_time(),'CPU_seconds':sum(p.cpu_times()[:2]),'affinity':p.cpu_affinity(),'cmdline':args,'running':p.is_running()}
for rev in ('r33','r34','r35'):
 folder=H/('resource-monitor-'+rev);p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else:c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
fresh(H/'checkpoint-r40.json',c);docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r40-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r40']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note='Continuation '+c['utc']+'\n\nSaved Claude work continues; liveR07 unchanged. ExactR753 combinedFIELD/ROOT/Q0/DIC/DI6 diagnostic7bddce00 is staged and its one all-net native CPP fill is RUNNING onexistingmain1/PID70888. Native before-fill all94448Cu integer/lock checks0errors; all8006baseline viaUIDs retained/13newordinary masks required. Source/contact/reference/current/DRC/thermal/SI remainOPEN; explicitownednegative/rawinherited failures held. OriginalfullCORE5trunk remains; fullnativeIO3 census provesboth savedbypass endpointsalreadySOURCE, soSBCbypass/resistor relocation remainconditional andexcluded. COREreplacement searchescontinue; DI6scopedrepair/nativeBEFOREtarget bindingspass, DI15referenceextensionunderconstruction. OriginalR157fullCLI PID54240 untouched. R34alarmsactive, R35scheduled00:34:20UTC. Noadoption/fabricationrelease. Seecontinuation-r2/checkpoint-r40.json.\n'
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r40.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False});print('R40_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
