"""Exact fresh-source and physical-island load catalogue; no current cap."""
from pathlib import Path
import sys,pickle,json,hashlib,time
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path.insert(0,str(ROOT/'field-power'))
import verify_source as V
OUT=H/'AO1-two-joined-ground-islands-exact-fresh-source-downstream-load-catalogue-r662'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();nf=ROOT/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';doc=V.parse(nf.read_text());comps={V.atom(c,'ref'):c for c in V.children(V.child(doc,'components'),'comp')};nets={};byref={}
 for n in V.children(V.child(doc,'nets'),'net'):
  name=V.atom(n,'name');nodes=[{q[0]:q[1]for q in node[1:]}for node in V.children(n,'node')];nets[name]=nodes
  for node in nodes:byref.setdefault(node['ref'],{})[node['pin']]=name
 def component(ref):
  c=comps[ref];return {'ref':ref,'value':V.atom(c,'value'),'footprint':V.atom(c,'footprint'),'pins':byref.get(ref,{})}
 ip=H/'AO1-COM-six-actual-native-ground-islands-source-bridge-census-r632/actual-six-COM-islands-and-SOURCE-metals-NOMINATION_ONLY.pkl';assert sha(ip)=='3ed53fb76aaee578bee266481e72135e52bc0115d1caeb659b4db2e2196c409e';groups=pickle.loads(ip.read_bytes());islands=[]
 for ix in(2,4):
  members=[{'ref':p['ref'],'pin':p['pin'],'UUID':p['UUID'],'layers':p['layers']}for p in groups['islands'][ix]['pads']];refs=sorted({p['ref']for p in members});islands.append({'actual_BEFORE_pad_island_index':ix,'actual_pad_members':members,'physical_pad_count':len(members),'grounded_components':[component(r)for r in refs]})
 roots={'U14623':component('U14623'),'U14636':component('U14636')};ports={};downrefs=set()
 for ref,pins in [('U14623',[str(i)for i in range(1,17)]),('U14636',[str(i)for i in range(1,11)])]:
  rows=[]
  for pin in pins:
   if pin not in byref[ref]:continue
   name=byref[ref][pin];nodes=nets[name];rows.append({'pin':pin,'net':name,'nodes':nodes});downrefs.update(n['ref']for n in nodes if n['ref']not in(ref,)and n['ref'].startswith(('R','C','U')))
  ports[ref]=rows
 # Complete per-port resistor endpoint catalogue; large rails are kept separate.
 localrefs=set()
 for ref,signalpins in [('U14623',['10','11','12','13','14','15']),('U14636',['1','2','4','5','6','7','8','9'])]:
  for pin in signalpins:
   name=byref[ref][pin];localrefs.update(n['ref']for n in nets[name])
 local=[component(r)for r in sorted(localrefs)if r in comps]
 r={'verdict':'EXACT_FRESH_SOURCE_AND_ACTUAL_GROUND_ISLAND_LOAD_CATALOGUE_ONLY_NO_RATING','fresh_net_file':str(nf.resolve()),'fresh_net_SHA256':sha(nf),'island_cache_SHA256':sha(ip),'actual_before_islands_joined_by_ground_proposal':islands,'grounded_ICs':roots,'all_grounded_IC_port_nodes':ports,'signal_port_connected_component_values_and_all_pin_nets':local,'conditional_current_formulas_required':True,'native_after_prospective_sharing_current_SI_thermal':'OPEN','elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R662_COMPLETE',sha(OUT/'receipt.json'),json.dumps({'grounded_ICs':roots,'local_components':local}),flush=True)
if __name__=='__main__':main()
