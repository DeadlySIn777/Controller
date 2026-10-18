"""Bind all723 reviewed owners to the actual adoption and exclude the ADC cell."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--inventory',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--adoption',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    d=load(a.inventory);m=load(a.source/'design.json');ad=load(a.adoption)
    if not ad['passed']or not ad['adopted']or not ad['all_native_pin_nets_preserved']:raise ValueError('Frozen exact native source adoption required')
    for p,h in ad['source_hashes'].items():
        if sha(a.source/p)!=h:raise ValueError('Actual adopted source changed '+p)
    if not d['all_owner_mappings_verified']or d['source_capacitor_count']!=723:raise ValueError('Complete723 ownership required')
    for p,h in d['input_hashes'].items():
        if sha(p)!=h:raise ValueError('Owner inventory source changed '+p)
    requirements=m['adc_bypass_correction']
    if not requirements['direct_AVDD_DVDD_REFCAP_no_via_routes_required']or requirements['reference_effective_bias_age_temp_ESR_qualified']:raise ValueError('Actual precision loop obligations changed')
    old=copy.deepcopy(d['capacitors']);special={}
    for ref in ['C14740','C14741','C14742','C14743','C14744','C14745','C14746']:
        row=next(r for r in d['capacitors']if r['ref']==ref)
        if row['owner']!='U14734'or row['actual_MPN']!=m['components'][ref]['mpn']:raise ValueError('Exact ADC owner/MPN changed '+ref)
        direct=ref not in ['C14740','C14741']
        special[ref]=dict(dedicated_owner_cell='ADS8684A-U14734',generic_router_permitted=False,
            same_side_required=True,no_vias_to_owner=direct,
            REFIO_same_side_no_via_is_engineering_target=not direct,
            primary='TI ADS8684A SBAS680 §11.1 p70; §8.3.8 p29/31',
            existing_nominal_value_f=m['components'][ref]['capacitance_f'],
            effective_capacitance_qualified=False,loop_physically_qualified=False)
        row.update(special[ref])
    for r,o in zip(d['capacitors'],old):
        if {k:v for k,v in r.items()if k not in special.get(r['ref'],{})}!=o:raise ValueError('Other723 ownership declaration changed')
    d['adoption_sha256']=sha(a.adoption);d['source_revision']=a.adoption.parent.name;d['precision_ADC_cell']=special
    d['annotation_tool_sha256']=sha(__file__);d['inventory_sha256']=sha(a.inventory)
    a.out.mkdir(parents=True);(a.out/'capacitor-owners.json').write_text(json.dumps(d,indent=2)+'\n');(a.out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(owners=723,errors=d['errors'],pending=d['pending'],exact_ADC_generic_exclusions=list(special))))
if __name__=='__main__':main()
