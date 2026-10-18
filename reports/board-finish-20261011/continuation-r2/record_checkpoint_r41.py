"""Save continuing native run, source-bound recovery work, and alarm renewal."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r40.json';c=read(prior);c['previous_checkpoint_sha256']=sha(prior)
c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256']
native=H/'combined-R753-one-full-native-fill-cached-DRC-r299'
c['combined_native_observed_status']=read(native/'status.json')
c['combined_CPP_observed_status']=read(native/'native-full/status.json')
c['full_state_host_supervisor_status']=read(H/'field-power/combined-full-native-postfill-serial-host-supervisor-r771/status.json')
c['continuing_work'].update({
 'actual_full_before_allnet_audit':'R763 independently binds ALL2389 physical nets,9971 native padUUIDs and8535 holes; cached native BEFORE source graph modeldbeba666/groupsd808a9bb. R773 all nine SOURCE pad selectors exactly match nativeCPP source pad membership. Existing R771 serial confined host supervisor automatically runs R763-after andR767 after the genuine same-instance full R299 receipt; no substituted selected-layer caches or forced flashes.',
 'original_r07_loss_recovery':'R287 actual fullnative original17losses:6 recovered,11remain before current candidate. DI6/Q0 are in R753, not yet counted as AFTER recovered. R301 exact current pad ranking frozen. DI15 repeated physical passes fail actual reference support; XF endpoint LG shadows blocked protectedFA24; OBS/DOB ordinary return escapes remain blocked. Recoveryr2 stream-failed twice; saved jobs inventoried/reused by recoveryr3 rather than restarted. R622 exactAO1_COM sourceU14619.7 has353 nonfill layer keys; R624 CS andR626 ENABLE no lawful ordinary escape; R630 attributes real endpoint Cu cages/reference gaps. R632 binds all sixactualAO1COM pad groups. Minimal same-domain COM joins are being constructed without foreign-plane cuts.',
 'AO1_VREF_current':'Saved R616 four-add VREF stencil4263f3b0 independently requalified against exact current Cu and full native BEFORE; it collides with oldSDIvia/MON, so not replayed. AO1r8 binds fresh070444 VREF/MON/SDI source contracts. AO1r11 constructs12 ONLY_NEW .20 tracks/twoordinary .5/.2 vias while replacing only three lockedMON segments; .906684170mm SG/COMpair, actualCOM SOURCE root, SDI/5V unchanged. Normal-antipad/all-drill/source-oldgroups/body-reference/new-new audit remains running; matching nativeAFTER/current/SI open. No native board adoption.',
 'SBC_CM_ground_current':'R416 actual fullR157 confirms CM79/CM73 andall30J15002 groundpads outside actualJ1SOURCE, unlike unnecessary oldIO3bypass. R417/R418 bounded fast-shadow routing had no candidate. Operator392e2155 D4 is SIGNAL-specific; R420 keeps rawshadow failures separate while routing actualDCground with true beforeSOURCE annuli/nativeclearance. Still0physicalroutes with dc1a retained. R421 attributes sealed cell to original MIPIpads77/81, originaldc1atrunk below and originalCDONEb1e550d5 barrel above; removing ONLY_NEW CM holes does not open it. A minimal ownedCDONEbarrel/stub relocation is being constructed, preserving originalCORE trunk/allotherCu/functions and SOURCE returns; no large unqualifiedCORE withdrawal.',
 'short_surface_progress':'RootR304 native-dump reader lackedUUID field; failure preserved, R305 uniquely resolves exact current native padUUID byref/number/rawnet/integerpose with geometry policy unchanged. Screens45 bounded shortDOM_LOGIC pairs excluding computeconnector-owned and controlled differential pairs. Six physicalnominees/seven .20 surface tracks/no newvias/no oldCu edits survive actualfullBEFORE foreignfills+exactcurrentCu/pads/allotherdrills/rules/new-newclearance. Includespower/ground branches andduplicatefuselands: electricalcurrent/width/source/reference/actualfullAFTER/nativeDRC qualification remains OPEN; geometry alone is not progress credit or adoption.',
 'resource_alarm':'R34 completed00:34:40UTC. R35activePID50780 from00:34:20.781115UTC to01:34:20.781104UTC. R36 unchangedCPU70%/GPU80C350W alarms scheduled01:34:10.781104UTC with10sec overlap, session22293. Four existing KiCad slots/no newheavy slots; originalR157CLI and combinedR299 native run uninterrupted.'})
paths=[
 'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/prepare-receipt.json',
 'field-power/combined-full-native-postfill-serial-host-supervisor-r771/status.json',
 'original-r07-residual-joins-current-R753-native-pad-ranking-r301/receipt.json',
 'current-R753-DOA-SDO-field-no-hole-B-transport-nomination-r302/receipt.json',
 'coupled-recovery/AO1-R19-VREF-only-four-chunk-current-requalification-handoff-r616/receipt.json',
 'coupled-recovery/AO1-current-F-cage-fresh-source-contract-r8/receipt.json',
 'coupled-recovery/AO1-joint-VREF-ports-and-MON3-locked-source-supported-detour-r11/receipt.json',
 'coupled-recovery/AO1-two-residual-current-physical-escape-versus-source-reference-attribution-r630/receipt.json',
 'sbc-power/CORE5-retained-trunk-CM79-full-R157-actual-source-necessity-r416/receipt.json',
 'current-R753-short-logic-no-hole-surface-construction-r305/receipt.json',
 'short-current-logic-surface-reader-derivation-r305.json',
 'resource-watch-arm-derivation-r36.json']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for label,pid,needle in [('R157_full_CLI',54240,'kicad-cli.exe'),('R299_full_native_CPP',70888,'native_combined_all_net_fill_and_real_saved_cache_r298.py')]:
 p=psutil.Process(pid);args=p.cmdline();assert needle in ' '.join(args)
 c['native_scope_jobs'][label]={'PID':pid,'create_time':p.create_time(),'CPU_seconds':sum(p.cpu_times()[:2]),'affinity':p.cpu_affinity(),'cmdline':args,'running':p.is_running()}
for rev in ('r34','r35','r36'):
 folder=H/('resource-monitor-'+rev);p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else:c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
fresh(H/'checkpoint-r41.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r41-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r41']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note=('Continuation '+c['utc']+'\n\n'
 'Saved Claude work continues. Live r07 remains unchanged and unfinished. The exact combined R753 candidate retains the original CORE5 trunk; its one full native KiCad refill and the original R157 full DRC remain active. R763/R773 bind all-net native baseline source contacts, and R771 will audit the genuine full AFTER state automatically. AO1 now has a constructive three-segment monitor reroute and new VREF connection under audit; AO1 COM joins and a minimal CDONE relocation for compute ground are being constructed. Six short surface connections are physical nominees only; source, current, width, reference and native checks remain open. R35 resource alarms are active and R36 is scheduled with overlap. No adoption or fabrication release. See continuation-r2/checkpoint-r41.json.\n')
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r41.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print('R41_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
