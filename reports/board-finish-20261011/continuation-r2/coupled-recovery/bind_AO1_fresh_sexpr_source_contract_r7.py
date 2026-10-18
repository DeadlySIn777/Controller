"""Reuse saved R6 cage result and bind the real S-expression netlist."""
from pathlib import Path
import sys,json,hashlib,time
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path.insert(0,str(ROOT/'field-power'))
from verify_source import parse,children,child,atom
OUT=H/'AO1-current-F-cage-fresh-source-contract-r7'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT.mkdir(exist_ok=False);st=time.monotonic();pins={}
def pin(p,s=None):
 p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
old=H/'AO1-F-endpoint-current-cage-and-fresh-source-contract-r6';assert not(old/'receipt.json').exists()
(old/'reader-failure.json').write_text(json.dumps({'reason':'fresh.net is the native KiCad S-expression format, not XML; cage geometry already completed and preserved','native_jobs':0,'adopted':False},indent=1)+'\n')
cf=pin(old/'literal-F-endpoint-cage-summary.json');ports=json.loads(cf.read_bytes());near=pin(old/'exact-nearby-retained-original-F-tracks.json')
nf=pin(ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net','070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2');doc=parse(nf.read_text());names={'/motherboard_analog_output/AO1_VREF','/motherboard_analog_output/AO1_COM','/motherboard_analog_output/AO1_MON_12V','/motherboard_analog_output/AO1_DAC_SDI'};nets=[];refs=set()
for n in children(child(doc,'nets'),'net'):
 if atom(n,'name')in names:
  ns=[{x[0]:x[1]for x in q[1:]}for q in children(n,'node')];refs.update(q['ref']for q in ns);nets.append({'raw_name':atom(n,'name'),'nodes':ns})
assert {n['raw_name']for n in nets}==names
components=[]
for c in children(child(doc,'components'),'comp'):
 if atom(c,'ref')in refs:components.append({'ref':atom(c,'ref'),'value':atom(c,'value'),'footprint':atom(c,'footprint'),'libsource':{q[0]:q[1]for q in child(c,'libsource')[1:]},'fields':{atom(q,'name'):q[-1]for q in children(child(c,'fields')or[],'field')}})
er=pin(nf.parent/'receipt-r2.json');erc=json.loads(er.read_bytes());put('source-export-receipt-schema.json',{'keys':list(erc),'source_receipt_SHA256':sha(er)})
put('exact-fresh-AO1-source-pin-and-component-contract.json',{'raw_net_and_pin_contract':nets,'components':components,'source_netlist_SHA256':sha(nf),'source_ERC_receipt_SHA256':sha(er),'source_changed':False,'source_ERC_does_not_qualify_board_routing':True})
put('receipt.json',{'verdict':'REAL_SOURCE_VREF_MON_SDI_COM_NET_PIN_CONTRACT_BOUND_WITH_CURRENT_F_ENDPOINT_CAGE','ports':ports,'nearby_original_tracks_file':str(near.resolve()),'native_jobs':0,'source_changed':False,'Cu_changed':False,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st})
print(json.dumps({'verdict':'SOURCE_CONTRACT_BOUND','nets':nets,'components':len(components),'elapsed_seconds':time.monotonic()-st}),flush=True)
