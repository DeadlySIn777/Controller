"""Exact capacitor owners and source-backed layout recipes; no PCB mutation.

Numeric distance screens are engineering targets, not manufacturer guarantees.
The component pin maps and capacitor nets are independently reconciled here.
"""
from pathlib import Path
import hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[1]
BLOCKS=['motherboard_power_entry','motherboard_safety_sensor','motherboard_probe_limit_upgrade']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def qualified_cap_pins(component,net,category):
    """Exclude tied controls/NCs from bypass/return ownership, by exact part."""
    mpn=component['mpn'];pins=component['pins']
    maps={
      'TPS26630RGER':(('1','2','17','18'),('8','25')),
      'LM706A0RRXR':(('1','2','3','27','28','29','8','18','19'),('17','23','24','25','26','30')),
      'LM70660RRXR':(('1','2','3','27','28','29','8','18','19'),('17','23','24','25','26','30')),
      'LMR36506R5RPER':(('4','7'),('9',)),
      'TPS22990DMLR':(('3','4','8','9','10','11'),('6',)),
      'TPS2553DBVR-1':(('1','6'),('2',)),
      'TPS26624DRCR':(('1','10'),('5','6','11')),
      'TPS7A1633DGNR':(('1','8'),('4','9')),
      '74LVC2G04GW,125':(('5',),('2',)), '74LVC2G07GW,125':(('5',),('2',)),
      'SN74LVC1G74DCUR':(('8',),('4',)), '74AHCT1G17GVH':(('5',),('3',)),
      'ISO1212DBQR':(('2','3'),('1','8','9','14')),
      'MAX17612AATB+T':(('1','10'),('9','11')),
      'TPS1H000AQDGNRQ1':(('8',),('6','9')),
      'LTC2962HUD#PBF':(('1',),('3','17')),
      'SN74LVC1G06DBVR':(('5',),('3',)), 'SN74LVC2G34DCKR':(('5',),('2',)),
      'SN74AHCT1G08DBVR':(('5',),('3',)),
      'ISO7720FDWR':(('3','14'),('1','8','9','16')),
      'ISO7760FDWR':(('1','16'),('8','9')),
      'ISO1540DR':(('1','8'),('4','5')),
      'ADS1115IDGSR':(('8',),('3',)), 'TMUX1511PWR':(('14',),('7',)),
      'SN74LVC14APWR':(('14',),('7',)), 'SN74LVC1G17DBVR':(('5',),('3',)),
      'SN74LVC1G08DBVR':(('5',),('3',)), 'SN74LVC2G08DCUR':(('8',),('4',)),
      'SN74LV165APWR':(('16',),('8',)), 'LM4040A25IDBZR':(('1',),('2','3')),
    }
    matched={q for q,v in pins.items()if v==net}
    if mpn not in maps:
        if component.get('kind')in('R','L'):return matched
        raise ValueError('Unreviewed capacitor-owning part '+mpn)
    supply,ground=maps[mpn]
    if 'GND'in net or net.endswith('_0V') or net.endswith('_RTN'):
        return matched & set(ground)
    if category=='local_bypass' or category=='gate_driver_analog_bypass' or mpn=='TPS7A1633DGNR':
        return matched & set(supply)
    # Other capacitor types deliberately attach to signal/timing/filter pins.
    # Buck-output capacitors list Kelvin sense endpoints separately from the
    # actual shunt/coil power feed; those are never ampacity anchor substitutes.
    return matched
def build(models=None):
    models=models or {n:json.loads((ROOT/'hardware'/n/'design.json').read_text()) for n in BLOCKS}
    owners={n:{} for n in BLOCKS}
    def assign(block,first,last,ref,category='local_bypass',extra=()):
        for i in range(first,last+1):owners[block]['C'+str(i)]=(ref,category,tuple(extra))
    b=BLOCKS[0]
    for k,u in [(11001,'U11002'),(11005,'U11004'),(11009,'U11006')]:assign(b,k,k+3,u,'entry_local')
    for start,u,r in [(11013,'U11007','R11022'),(11030,'U11008','R11030')]:
        assign(b,start,start+5,u,'buck_input_hot_loop')
        assign(b,start+6,start+8,u,'buck_output_filter',(r,))
        assign(b,start+9,start+9,u,'bootstrap_local')
        assign(b,start+10,start+11,u,'gate_driver_analog_bypass')
        assign(b,start+12,start+12,u,'compensation_local',('R11026' if u=='U11007' else 'R11034',))
        assign(b,start+13,start+13,u,'compensation_local')
        assign(b,start+14,start+16,u,'buck_output_bulk',(r,))
    assign(b,11088,11088,'U11007','buck_output_bulk',('R11022',))
    assign(b,11047,11051,'U11009','buck_input_hot_loop')
    assign(b,11052,11052,'U11009','bootstrap_local')
    assign(b,11053,11053,'U11009','gate_driver_analog_bypass')
    assign(b,11054,11056,'U11009','buck_output_filter',('L11003',))
    for k,u in [(11057,'U11010'),(11059,'U11011')]:assign(b,k,k+1,u,'switch_local')
    assign(b,11061,11061,'U11012','timing_local');assign(b,11062,11063,'U11012','switch_local')
    assign(b,11064,11065,'U11013','limiter_local');assign(b,11066,11067,'U11014','limiter_local')
    assign(b,11068,11070,'U11015','limiter_local');assign(b,11071,11073,'U11016','limiter_local')
    assign(b,11074,11075,'U11017','LDO_local')
    # The accepted safety interposition changes U11018 IN/EN to B-local 5 V.
    assign(b,11076,11076,'U11006','upstream_entry_reservoir',('U19028',))
    assign(b,11077,11077,'U11018','LDO_output_local')
    for k,u in [(11078,'U11019'),(11079,'U11020'),(11080,'U11025'),(11081,'U11026'),(11083,'U11032'),(11084,'U11031'),(11086,'U11034'),(11087,'U11033')]:assign(b,k,k,u)
    assign(b,11082,11082,'U11032','fault_clear_local');assign(b,11085,11085,'U11034','fault_clear_local')
    b=BLOCKS[1]
    for k,u in [(19001,'U19001'),(19004,'U19002'),(19007,'U19003')]:
        assign(b,k,k+1,u,'safety_receiver_filter');assign(b,k+2,k+2,u)
    for k,u in [(19010,'U19004'),(19012,'U19005'),(19014,'U19006')]:assign(b,k,k+1,u,'limiter_local')
    assign(b,19016,19016,'U19007','timing_local');assign(b,19017,19018,'U19007','limiter_local')
    for k,u in [(19019,'U19008'),(19020,'U19009'),(19021,'U19011'),(19022,'U19013'),(19023,'U19014'),(19024,'U19015'),(19025,'U19017'),(19026,'U19017'),(19029,'U19019'),(19030,'U19019')]:assign(b,k,k,u)
    assign(b,19027,19027,'U19018','timing_local');assign(b,19028,19028,'U19018','limiter_local')
    for k in range(19031,19036):assign(b,k,k,'U'+str(k-11))
    assign(b,19036,19039,'U19026','ADC_input_filter',('U19027',))
    assign(b,19040,19041,'U19025');assign(b,19042,19042,'U19026');assign(b,19043,19043,'U19027')
    assign(b,19044,19048,'U19028','buck_input_hot_loop')
    assign(b,19049,19049,'U19028','bootstrap_local');assign(b,19050,19050,'U19028','gate_driver_analog_bypass')
    assign(b,19051,19052,'U19028','buck_output_filter',('L19001','U11018'))
    assign(b,19053,19053,'U11018','LDO_input_and_buck_output',('L19001','U19028'))
    b=BLOCKS[2]
    assign(b,14001,14006,'U14007','contact_filter');assign(b,14007,14007,'U14007')
    assign(b,14008,14013,'U14014','contact_filter')
    for k in range(14014,14020):assign(b,k,k,'U'+str(k))
    for k,u in [(14020,'U14020'),(14024,'U14021'),(14028,'U14022'),(14032,'U14023'),(14036,'U14024'),(14040,'U14025')]:assign(b,k,k+3,u,'limiter_local')
    assign(b,14044,14048,'U14026','limiter_local');assign(b,14049,14053,'U14027','limiter_local')
    assign(b,14054,14055,'U14028');assign(b,14056,14056,'U14029');assign(b,14057,14057,'U14030')
    assign(b,14058,14059,'U14031')
    assign(b,14060,14060,'U14032');assign(b,14061,14061,'U14033');assign(b,14062,14062,'U14034');assign(b,14063,14063,'U14035','shunt_reference_local')
    # Exact parent-native override already reviewed by the safety source.
    allc={r:dict(c,block=n,pins=dict(c['pins'])) for n,m in models.items() for r,c in m['components'].items()}
    for pin in ['5','8']:allc['U11018']['pins'][pin]='FIELD_B_5V_PRE'
    rows=[]
    for n,m in models.items():
        caps={r for r,c in m['components'].items() if c['kind']=='C' and c['physical']}
        assert caps==set(owners[n]),(n,caps-set(owners[n]),set(owners[n])-caps)
        for r in sorted(caps):
            c=m['components'][r];u,cat,extras=owners[n][r]
            eps={}
            for p,net in c['pins'].items():
                eps[p]=[dict(ref=x,pin=q,net=net) for x in (u,*extras) for q in sorted(qualified_cap_pins(allc[x],net,cat))]
                assert eps[p],(r,p,net,u,extras)
            # Distances intentionally separate from the manufacturer's prose.
            target={'local_bypass':2.0,'buck_input_hot_loop':2.0,'bootstrap_local':2.0,
              'gate_driver_analog_bypass':2.0,'compensation_local':3.0,'timing_local':3.0,
              'fault_clear_local':3.0,'limiter_local':2.5,'entry_local':3.0,'LDO_local':3.0,
              'LDO_output_local':3.0,'LDO_input_and_buck_output':3.0}.get(cat)
            rows.append(dict(block=n,ref=r,mpn=c['mpn'],footprint=c['footprint'],value=c['value'],
              role=c['role'],owner_ref=u,additional_owners=list(extras),category=cat,capacitor_pins=c['pins'],
              actual_owner_endpoints=eps,engineering_pad_to_owner_target_mm=target,
              numeric_target_is_manufacturer_limit=False,
              return_strategy='Keep within the exact local return domain; no cross-isolation DC return',
              effective_capacitance_qualified=False))
    return dict(schema_version=1,source_only=True,pcb_modified=False,layout_qualified=False,
        exact_parent_pin_overrides=[dict(ref='U11018',pin=p,before='FIELD_B_24V_PROTECTED',after='FIELD_B_5V_PRE')for p in ['5','8']],
        capacitor_count=len(rows),capacitors=rows,
        full_power_entry_inventory=[dict(ref=r,mpn=c['mpn'],footprint=c['footprint'],pins=c['pins'],role=c['role'])
          for r,c in models[BLOCKS[0]]['components'].items() if c['physical']],
        source_hashes=[dict(path='hardware/'+n+'/design.json',sha256=sha(ROOT/'hardware'/n/'design.json'))for n in BLOCKS])
def recipes():
    return dict(schema_version=1,proposal_only=True,board_collision_checked=False,
      coordinates='relative millimetres to converter centre, footprint native angle0; rotate/translate entire recipe as a unit',
      manufacturer_sources=[dict(path='research/core-converter/lm70660.pdf',sha256=sha(ROOT/'research/core-converter/lm70660.pdf'),pages=[35,44,45,46]),
        dict(path='reports/motherboard-power-entry-20260930/sources/lmr36506.pdf',sha256=sha(ROOT/'reports/motherboard-power-entry-20260930/sources/lmr36506.pdf'),pages=[38,39,40])],
      mandatory_topology=[
        'VIN ceramic capacitor positive directly into VIN1/2/3/27/28/29 and negative locally into PGND23..26/EP30; smallest top-layer hot-loop area, no distant common-rail substitute',
        'L11001 dotted pad1 must face SW20/21/22; L11001 pad2 feeds R11022 pad1. Coil body and courtyard must clear IC. Do not route switching current through sense traces',
        'R11022 pad2 supplies CORE5 output capacitor positives and load bus. Two separate Kelvin traces depart directly from the inner sense points of shuntpads1/2 to U11007.ISNS11/VOUT12. IC BIAS6 gets a separate CORE5 branch',
        'Grounded input/output capacitors use local top PGND copper plus underlying continuous LOGIC_GND; PGND thermal-via array and no sensitive-signal routing under the SW area',
        'BOOT4↔C11022↔SW_BOOT5, VCC19↔C11023↔PGND and VDDA8/18↔C11024↔quiet AGND17 loops stay local; quiet compensation at pin15 and AGND17 away from SW',
        'Output bulk bank follows the shunt on a wide CORE5/GND pair; no random remote four-cap placement. Preserve four actual330uF devices and three MLCCs/effectivecap budget',
        'MOTION converter uses the same topology independently; no CORE7A claim changes its6A source rating',
        'FIELD_A U11009 and FIELD_B U19028 each keep own VIN/SW/BOOT/VCC/EP9 short local loops and never cross field grounds'],
      manufacturer_numeric_distance_limit_mm=None,
      manufacturer_ground_plane='continuous adjacent underlying ground plane, localized top-side input/output return planes',
      manufacturer_copper='LM706x0 preferably2oz outerlayers/no less1oz; LMR36506 recommends2/1/1/2oz four-layer example; final six-layer stackup/thermal review still required',
      fitted_HF_footprint_deviation='TI Fig7-37 recommends0402 HF ceramics; fitted C11017/18 andC11034/35 are0603. Very short pad-level loops are the engineering proposal; size deviation is not silently manufacturer-qualified',
      CORE7_relative_seed={
       'U11007':[0,0,0],'L11001':[11.4,0,180],'R11022':[18.5,0,0],
       'C11017':[-.25,-4.25,0],'C11018':[-.25,-6,0],
       'C11013':[-7,-5,90],'C11014':[-7,-10,90],'C11015':[-2,-10,0],'C11016':[3,-10,0],
       'C11022':[-4.4,-1.2,270],'C11023':[4.7,.8,270],'C11024':[-4.5,2,270],
       'R11023':[-.5,5.1,90],'R11024':[-2.5,5.1,90],'R11025':[-4.5,5.1,90],
       'R11026':[3.5,5.1,270],'C11025':[4.5,8.5,90],'C11026':[1.5,7.3,270],
       'R11027':[-7.5,6,0],'R11028':[-6,9,0],'R11029':[-6,12,0],
       'C11019':[21,-5,90],'C11020':[23,0,90],'C11021':[21,5,90],
       'C11027':[30,-8,0],'C11028':[30,8,0],'C11029':[41,-8,0],'C11088':[41,8,0]},
      seed_not_accepted=['Run actual component courtyard/copper clearance and existing-route collision review before adopting coordinates',
       'Optimize capacitor orientation by actual supply and return pad edges, not merely centre distance',
       'Thermal relief/spokes on7A/6A main paths cannot be assumed adequate; direct polygon connections/ampacity must be designed',
       'Use Kelvin routes as distinct geometry despite identical schematic nets; audit their separate branching points',
       'The proposed relative seed is not a routable board or manufacturing file'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    manifest=build();assert len(manifest['full_power_entry_inventory'])==221
    r=recipes();c=r['CORE7_relative_seed'];m=json.loads((ROOT/'hardware/motherboard_power_entry/design.json').read_text())['components']
    core={v.get('source_ref'):k for k,v in m.items() if v.get('role','').startswith('CORE reused reviewed')}
    motion={v.get('source_ref'):k for k,v in m.items() if v.get('role','').startswith('MOTION reused reviewed')}
    reverse={v:k for k,v in core.items()}
    ms={motion[reverse[ref]]:xy for ref,xy in c.items()if ref in reverse}
    assert len(ms)==27
    ms.update({'L11002':[11.1,0,0],'R11030':[17,0,0],
     'C11036':[17.5,-5,90],'C11037':[20.5,0,90],'C11038':[17.5,8,90],
     'C11044':[25,-8,0],'C11045':[25,8,0],'C11046':[36,-8,0]})
    fs={'U11009':[0,0,0],'L11003':[6.8,0,0],
      'C11047':[-6,-5,0],'C11048':[-6,-1,0],'C11049':[-6,3,0],'C11050':[-6,7,0],
      'C11051':[-2.4,2,270],'C11052':[2.15,1,270],'C11053':[-2.4,-1.5,270],
      'C11054':[12,-3,90],'C11055':[12,3,90],'C11056':[11.5,0,0],
      'R11038':[-1,4.8,0],'R11039':[-1,7.8,0],'R11040':[3.5,-5.5,0],'R11041':[14,7,0]}
    trans={'U11009':'U19028','L11003':'L19001',**{'C'+str(a):'C'+str(a-11047+19044)for a in range(11047,11057)},**{'R'+str(a):'R'+str(a-11038+19083)for a in range(11038,11042)}}
    bs={trans[k]:v for k,v in fs.items()}
    # The accepted B-local preregulator feeds the existing B-domain LDO.
    # C19053 is the actual IN8 bypass, not a reservoir on the old24V rail.
    bs.update({'U11018':[21,0,0],'C19053':[25.2,-1,270],
      'C11077':[16,0,270],'R11065':[18,4,0]})
    mc1={'U2001':[0,0,0],'L2001':[-4,0,180],'C2001':[3,.5,270],'C2002':[0,3.6,0],
      'C2003':[0,-3.1,90],'R2001':[2.5,-4.5,90],'R2002':[3.5,4.5,0],'R2003':[-3,5.5,0]}
    mc2={'U2002':[0,0,0],'L2002':[-4,0,180],'C2004':[3,.5,270],'C2005':[0,3.6,0],
      'C2006':[0,-3.1,90],'R2005':[2.5,-4.5,90],'R2006':[6,4.5,0],'R2007':[-4,6.5,0],
      'R2008':[-4,-4.5,90],'R18002':[-2,-4,90],'R18001':[3,6,0],'C2010':[0,6,0]}
    r['groups']={'CORE7':c,'MOTION6':ms,'FIELD_A5':fs,'FIELD_B5':bs,'MC_1V2':mc1,'MC_IO3':mc2}
    r['MC_required_topology']=[
      'TPS input capacitor adjacent VIN6/GND4; coil dotted pad1 faces SW2; shortest VOS3 Kelvin to local output capacitor positive',
      'IO3 L2002.2/C2005.1/C2010.1/U2002.3 remain REG_LOCAL; R18001 only boundary into distributed IO3; never bridge resistor with copper plane',
      'R18002 top and R2008 bottom sit close FB9 with quiet GND return; MODE7 ties actual local inputcapVIN viaR2005; SS8 capacitor stays local',
      'C2010 is REG_LOCAL after accepted helper, whileU2006 remains distributedIO3. Accepted additive C18001 owns U2006 VCC5/GND3 and must stay local to that actual reset buffer']
    r['manufacturer_sources'].append(dict(path='reports/motherboard-power-entry-20260930/load-closure/tps62902.pdf',sha256=sha(ROOT/'reports/motherboard-power-entry-20260930/load-closure/tps62902.pdf'),pages=[41]))
    for name,d in [('capacitor-owners.json',manifest),('converter-layout-recipes.json',r)]:
        (a.output_dir/name).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps(dict(capacitors=manifest['capacitor_count'],power_parts=221,pcb_modified=False)))
if __name__=='__main__':main()
