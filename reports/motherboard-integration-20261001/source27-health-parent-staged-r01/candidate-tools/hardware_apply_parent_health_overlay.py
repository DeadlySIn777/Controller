"""Reproduce the exact parent-only health override after fresh integration.
No child/original source is changed. Fresh generated parts must still be the
old reviewed identities, so the frozen helper executes exactly once. Existing
ADC/source26 adoption metadata is preserved only with exact qualified part
identity checks; this is not hierarchy regeneration of the live board.
"""
from pathlib import Path
import json,copy,csv,hashlib
from hardware_build_assembly import parse,dump
from hardware_apply_motherboard_health_source import apply_health_source
META=('adc_bypass_correction','adc_reference_component_qualification')
LEDGERS=('reviewed_adc_bypass_delta','reviewed_source26_qualification_delta')
REFS=('R2106','U11019','U11025')

def capture_prior_qualification(parent):
 parent=Path(parent);m=json.loads((parent/'design.json').read_text());a=json.loads((parent/'assembly-map.json').read_text())
 if len(m['components'])!=2688 or any(k not in m for k in META)or any(k not in a for k in LEDGERS):raise ValueError('Actual prior ADC/source26 parent qualification metadata is required')
 return {'metadata':{k:copy.deepcopy(m[k])for k in META},'ledgers':{k:copy.deepcopy(a[k])for k in LEDGERS},'parts':{r:copy.deepcopy(m['components'][r])for r in ('C14741','C14743','C14744','C14745','C14746','F11001','F11002','F11003')},'reviewed_FPGA_artifacts':{name:(parent/name).read_bytes()for name in('fpga-allocation-proposal.json','fpga-allocation-applied.json')}}

def apply_generated_parent_health(folder,prior,root):
 folder=Path(folder);m=json.loads((folder/'design.json').read_text());a=json.loads((folder/'assembly-map.json').read_text())
 if len(m['components'])!=2688:raise ValueError('Source27 cannot change population')
 for r,c in prior['parts'].items():
  n=m['components'][r]
  if any(n.get(k)!=c.get(k)for k in('mpn','value','footprint','pins')):raise ValueError('Fresh generated ADC/source26 qualified part identity differs '+r)
 for k,v in prior['metadata'].items():m[k]=copy.deepcopy(v)
 for k,v in prior['ledgers'].items():a[k]=copy.deepcopy(v)
 for name,raw in prior['reviewed_FPGA_artifacts'].items():
  target=folder/name
  if target.exists()and target.read_bytes()!=raw:raise ValueError('Reviewed FPGA artifact changed '+name)
  target.write_bytes(raw)
 trees={k:parse((folder/(k+'.kicad_sch')).read_text())for k in('mc_local_power','motherboard_power_entry')};trees,new,receipt=apply_health_source(trees,m)
 for k,t in trees.items():(folder/(k+'.kicad_sch')).write_text(dump(t)+'\n')
 ledger=copy.deepcopy(HEALTH_LEDGER)
 a['reviewed_health_source_delta']=ledger
 # The exact frozen transform is a genuine reproducibility dependency.
 root=Path(root).resolve()
 for dep in (Path(__import__('hardware_apply_motherboard_health_source').__file__).resolve(),Path(__file__).resolve()):
  key=dep.relative_to(root).as_posix();h=hashlib.sha256(dep.read_bytes()).hexdigest()
  for record in(new['source_sha256'],a['input_sha256']):record[key]=h
 (folder/'design.json').write_text(json.dumps(new,indent=2)+'\n');(folder/'assembly-map.json').write_text(json.dumps(a,indent=2)+'\n')
 with (folder/'bom.csv').open(newline='',encoding='utf8')as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
 for row in rows:
  if row['Reference']in REFS:
   c=new['components'][row['Reference']];row['Value']=c['value'];row['MPN']=c['mpn']
 with (folder/'bom.csv').open('w',newline='',encoding='utf8')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return receipt

HEALTH_LEDGER={'id': 'MB-HEALTH-001', 'references': ['R2106', 'U11019', 'U11025'], 'parent_only_override': True, 'immutable_child04_and_original_MC_baselines_retained': True, 'frozen_primary_receipt': 'reports/motherboard-power-entry-20261001/health-source-correction-r01/receipt.json', 'frozen_primary_receipt_sha256': '4b9d5dfe401204cfab08b969d238481211116d15ca54333563343e271f3a35b0', 'frozen_primary_review_sha256': 'dce3d03ccac16298ad597ccce0c5f432af7f9fdeb4b834c637254359123d32ba', 'native_pin_nets_unchanged': True, 'manufacturer_lands_unchanged': True, 'part_count_unchanged': True, 'physical_qualified': False}
