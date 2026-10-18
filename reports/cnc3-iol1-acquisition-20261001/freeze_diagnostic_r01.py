from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
B=P/'diagnostic-replay-candidate-r01'; R=P/'diagnostic-replay-full-r01/report.json'
r=json.loads(R.read_text()); assert r['status']=='PASS' and r['counts']=={'PASS':4,'FAIL':0,'BLOCKED':0,'NOT_RUN':0} and r['bundle_integrity'] and r['inputs_unchanged']
receipt={'status':'PASS','bundle':str(B),'bundle_manifest_sha256':sha(B/'bundle-manifest.json'),'fresh_replay_report':str(R),'fresh_replay_report_sha256':sha(R),'actual_SPI_checks':55,'compiled_rejected_mutations':7,'cycle_exact_optimization_checks':1287937,'composed_family_resources':{'EFX_LUT4':16154,'EFX_ADD':6806,'EFX_FF':11460,'EFX_GBUFCE':1},'scope':r['scope_flags'],'replay_command':'C:/Python314/python.exe -X utf8 '+str(B/'replay_acquisition.py')+' --out <fresh>','corrections':['response hardware-major upper nibble: this diagnostic profile expects0, not a globally reserved nibble','target prepares response after prior CS release; growing age includes measured response residency','transmitted sequence advances despite bad replies; accepted progress never advances on rejection'],'remaining_implementation':['factory record/host trust/IDENT_READ and configuration/ACTIVE transition','real ADC/DAC observations and actual ARM DMA/IRQ execution','actual full provider/topology CAP3/driver/HAL','vendor fit/STA/physical loaded timing']}
O=P/'diagnostic-handoff-r01';O.mkdir(exist_ok=False)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'path':str(O/'receipt.json'),'sha256':sha(O/'receipt.json')}))
