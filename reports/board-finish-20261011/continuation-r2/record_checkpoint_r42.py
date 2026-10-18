"""Preserve the frozen AO1 repair and current native diagnostic work."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r41.json';c=read(prior);c['previous_checkpoint_sha256']=sha(prior);c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256']
native=H/'combined-R753-one-full-native-fill-cached-DRC-r299'
c['combined_native_observed_status']=read(native/'status.json');c['combined_CPP_observed_status']=read(native/'native-full/status.json')
c['full_state_host_supervisor_status']=read(H/'field-power/combined-full-native-postfill-serial-host-supervisor-r771/status.json')
c['continuing_work'].update({
 'AO1_VREF_current':'R20 independently passes scoped exact-current AO1 MON3/VREF/b1775V replacement: four old locked segments retired, fourteen tracks/two ordinaryvias added, .906684mm return, all old groups/source keys/direct contacts/retained reference bodies and all14newbody references/geometry preserved. Exact locked .30power endpoints and genuine U14620.1 OUT / U14619.6→U14620.8 converter path retained. Added conditional resistance .00382111ohm/A under25umCu125C assumptions, actualcurrent/totalIR open. R22 exactnative manifest88806b5e; R28 supplementb719c7dc combines repaired seven COMgroundtracks:21tracks/twovias/fouroldretirements, allothernative chunks/FP/pads/profile/header/tail exact. R25 new-new36checks pass; no nativePCB emitted/adopted. AO1agent continues genuine producer U1001.R1 CDONE ordinary Bfirst escape; any additionalVIPPO location/process is explicit openqualification, no blanket extension of291intentional locations.',
 'AO1_ground_recovery_current':'R650/R652 constructive COM B/F source joins repaired underR656: six Btracks widths .30/.20/.20/.20/.20/.50 and one .20Ftrack, no newholes/olddeletes. R658 joint withR20 passes oldgroups/sourcekeys/directcontacts/strictretainedSOURCEbody references/newbody trueguards; actual padislands6→4 prospectively, SOURCEkeys359→411. R668 exactactiveR753+AO1peers+RootR310 additional rawtrack/via/drill checks138/0errors. ConditionalR664 newBtraceR .113480ohm/F .003688ohm at25umCu125C; actualisolator3.3V/5V ICC andADC5V table bounds/fullloop/grounderrorbudget remainOPEN, referencecases not currentPASS. Recoverycontinues remainingU14624.3ground island/DACCS withexactb177detour hardpeer.',
 'short_surface_progress':'R305 sixphysicalonlynominees triagedR306: twofuse/MOTION powerpaths .20width belowhistorical conservativebounds, severalmissingactualSOURCEreference; held. R307 uses conservative tablewidths and2mm continuousdetours, fivephysicalnominees/seventracks. R308 actualbeforeSource triage: onlyESDgroundU15016.3/8 andWD_M_CWD C3001/U3001 have fullbeforeLGsupport (ground finiteSOURCEcontact .072215mm²); remainingpoweredpathsheld. R310 freezes onlythese two connections/three .20surface nativeaddchunks; all98030unlistedchunks/header/tail byteexact, novias/deletes/PCB. Current/ESDpulse/watchdogtiming/nativeactualAFTER gatesopen. R309 broader97-ish common-surface sample up to15mm yieldsno additionalnominees (readreceipt actualcount), notglobalimpossibility. R311 identifies11nets/34unchangedactualIn3portpairs<=60mm acrossfullnative splitgroups; no newvias or paths claimed, possibleexistingportroute next.',
 'current_native_intended_profiles':'R312 readonlynative export bindsall850boardzone definitions plus2embeddedFP RULEareas atnative1nm coordinates, fulloutlines/priority/clearance/minthickness/islandsettings. Receipt4bc4161a/export80452bcf. EmbeddedJ1002/J15003zones bothno-fill rules, sooriginalall850boardzonefill omitsno embeddedcopperzone. No Fill/Save calls andfrozeninputs unchanged; intendedprofiles notactualSOURCEfill evidence. SBC R431 bindsallprofiles; currentactiveCM79 regionoriginalLG.25/IO3.15/FB0V profiles, nooldfour-roleoverlay.',
 'SBC_CM_ground_current':'ExactnativecurrentCu R300 excludes all49prospectiveCMitems includingde03/31a0. R421 actualclosedCM79cell dueoldMIPIpads77/81 +fullCOREdc1abelow +oldCDONEb1e550d5above. R422 ledgeroldCDONE .6/.3locked via andexacttwo .20lockedincidentF/Bstubs; R424 distinguishesproducerU1001.R1 isolatedgroup from139key barrelgroup, fiveactualnetgroups total. Minimal +.250/-.025oldCDONE relocation +oneordinaryLGreturn/directCM79ground isbeingconstructedagainstexactR753/all850intents/fullbeforeforeignfill without all49CM additions orCOREwithdrawal. de03 pitchdeficit isprospectiveonly. OldC06 ESC_J15002_F conditionalhelperreserve prohibitsCDONE butisabsentactualR157 PCB/DRU andoriginalbarrelalreadyinside; rawhelperfailure retained separately, noglobalwaiver/edit/nativefalsePASS.',
 'resource_alarm':'R35complete01:34:21UTC. R36activePID57164 from01:34:10.819643UTC to02:34:10.819631UTC. R37unchangedCPU70%/GPU80C350W alarm scheduled02:34:00.819631UTC with10sec overlap, session57143. Existing4KiCadslots/12eligibleCPUreservation; noextraheavy slots. NativeR312 readonly existing shared2 jobcompleted, originalR157CLI54240 andfullcombinedR299CPP70888 remainuninterrupted.'})
paths=[
 'coupled-recovery/AO1-R20-exact-MON3-VREF-b177-minimal-current-native-replay-r22/minimal-exact-AO1-current-native-replay-manifest.json',
 'coupled-recovery/AO1-R22-with-R656-seven-ground-joint-sparse-native-supplement-r28/minimal-exact-AO1-with-seven-ground-joint-native-replay-supplement.json',
 'current-R753-short-logic-no-hole-surface-construction-r307/receipt.json',
 'R307-short-surface-actual-native-BEFORE-source-and-width-triage-r308/receipt.json',
 'current-R753-short-logic-no-hole-surface-construction-r309/receipt.json',
 'short-ESD-ground-and-watchdog-exact-current-native-add-only-r310/receipt.json',
 'actual-native-existing-In3-ports-across-current-logic-groups-r311/receipt.json',
 'current-R753-all-native-zone-intents-read-only-r312/receipt.json',
 'resource-watch-arm-derivation-r37.json']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for label,pid,needle in [('R157_full_CLI',54240,'kicad-cli.exe'),('R299_full_native_CPP',70888,'native_combined_all_net_fill_and_real_saved_cache_r298.py')]:
 p=psutil.Process(pid);args=p.cmdline();assert needle in ' '.join(args);c['native_scope_jobs'][label]={'PID':pid,'create_time':p.create_time(),'CPU_seconds':sum(p.cpu_times()[:2]),'affinity':p.cpu_affinity(),'cmdline':args,'running':p.is_running()}
for rev in ('r35','r36','r37'):
 folder=H/('resource-monitor-'+rev);p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else:c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
fresh(H/'checkpoint-r42.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r42-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r42']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note=('Continuation '+c['utc']+'\n\nSaved Claude work continues; the live board remains unchanged and unfinished. The combined R753 full KiCad refill and original R157 DRC are still running. The AO1 joint repair is frozen: 21 new tracks/two vias replace four exact old segments, with host source/contact/reference/geometry checks passing and all other native items preserved. Two short ground/watchdog connections have a separate three-track add-only manifest. Current/thermal/ESD/timing and native AFTER validation remain open. All 850 native zone definitions plus two embedded no-fill rules have been read without refilling or saving, and the minimal CDONE/compute-ground repair uses exact current copper rather than the 49 unqualified prospective additions. R36 alarms are active and R37 renewal scheduled. No adoption or fabrication release. See continuation-r2/checkpoint-r42.json.\n')
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r42.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False});print('R42_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
