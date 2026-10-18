"""Explicit motor capacitor owners, derived from frozen source roles/pins."""
from pathlib import Path
import argparse,json,hashlib
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    src=ROOT/'hardware/motherboard_motors/design.json';d=json.loads(src.read_text());parts=d['components'];b=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};caps=[];errors=[]
    power={'AM26C31':('16',['8']),'LVC07A':('14',['7']),'ISO1212':('2',['1','8']),'LTC6994':('5',['2']),'LVC2G08':('8',['4']),'LVC1G74':('8',['4']),'LVC14A':('14',['7']),'LVC00A':('14',['7']),'AHCT1G17':('5',['3'])}
    def ep(ref,pin):return dict(ref=ref,pin=str(pin),net=parts[ref]['pins'][str(pin)])
    for ref,p in parts.items():
        if p['kind']!='C':continue
        role=p['role'];extra=[]
        if role=='alarm front-end filter':
            sense=p['pins']['1'];owner=next(r for r,q in parts.items()if q['kind']=='ISO1212'and sense in q['pins'].values());chip=parts[owner];sp=next(k for k,v in chip['pins'].items()if v==sense);gp='14'if sp=='16'else'9';positive=[ep(owner,sp)];negative=[ep(owner,gp)];category='alarm_SENSE_filter'
            for rr,q in parts.items():
                if q['kind']=='R'and sense in q['pins'].values():extra.append(dict(ref=rr,role=q['role'],pins=q['pins']))
        else:
            owner=role.rsplit(' ',1)[1];chip=parts[owner]
            if role.startswith('load-switch input'):vp,gp='1',['2'];category='load_switch_input_reservoir'
            elif role.startswith('gated enable supply output'):vp,gp='6',['2'];category='load_switch_output_and_LED_supply_discharge'
            else:vp,gp=power[chip['kind']];category='local_VDD_bypass'
            positive=[ep(owner,vp)];negative=[ep(owner,k)for k in gp]
        ends={'1':positive,'2':negative};checks=[]
        for pin,rows in ends.items():
            cp=next(x for x in fs[ref].Pads()if x.GetNumber()==pin)
            for e in rows:
                qp=next(x for x in fs[e['ref']].Pads()if x.GetNumber()==e['pin']);match=cp.GetNetname()==qp.GetNetname();checks.append(dict(cap_pin=pin,owner_ref=e['ref'],owner_pin=e['pin'],actual_native_net=cp.GetNetname(),exact_native_net_match=match))
                if not match:errors.append(ref+'.'+pin+' / '+e['ref']+'.'+e['pin'])
        caps.append(dict(ref=ref,owner_ref=owner,mpn=p['mpn'],footprint=p['footprint'],capacitor_pins=p['pins'],actual_owner_endpoints=ends,category=category,role=role,related_external_parts=extra,native_pin_checks=checks,placement_target_mm=2.0,placement_target_basis='Engineering proximity screen, not manufacturer numeric maximum',layout_closed=False))
    assert len(caps)==42
    out=dict(schema_version=1,capacitor_count=len(caps),capacitors=caps,native_pin_errors=errors,source_hashes={str(src.relative_to(ROOT)):sha(src),str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},board_hash=sha(a.board),board_read_only=True,physical_power_loop_qualification=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(capacitor_count=len(caps),native_pin_errors=errors)))
if __name__=='__main__':main()
