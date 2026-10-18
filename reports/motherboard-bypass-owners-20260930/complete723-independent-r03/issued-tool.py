"""Independent source/native capacitor-owner checks and targeted negative controls.

No board or source is changed. A rail match alone does not establish ownership:
original reviewed receipts, explicit source roles and package/function contracts
also constrain the ledger, including same-rail FPGA-bank and MCU-VREF swaps.
"""
import argparse,copy,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/motherboard-integration-20260930/r23-2688-reset-bypass-staged'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def context():
    model=json.loads((SOURCE/'design.json').read_text())['components'];x=ET.parse(SOURCE/'netlist.xml')
    nets={(n.attrib['ref'],n.attrib['pin']):a.attrib['name']for a in x.findall('.//nets/net')for n in a.findall('node')}
    libs={(a.attrib['lib'],a.attrib['part']):{n.attrib['num']:n.attrib['name']for n in a.findall('./pins/pin')}for a in x.findall('.//libparts/libpart')}
    fun={a.attrib['ref']:libs[a.find('libsource').attrib['lib'],a.find('libsource').attrib['part']]for a in x.findall('.//components/comp')}
    reviewed={}
    p=ROOT/'reports/motherboard-bypass-owners-20260930/actual-r24f-r03/owner-distances.json'
    for r in json.loads(p.read_text())['rows']:reviewed[r['ref']]=(r['owner'],r['power_nodes'],r['return_nodes'],r.get('reviewed_series_path',[]))
    for p in [ROOT/'reports/motherboard-motors-20260930/capacitor-owners-r01.json',ROOT/'reports/motherboard-return-zoning-20260930/di-capacitor-owner-r01/capacitor-owners.json']:
        for r in json.loads(p.read_text())['capacitors']:reviewed[r['ref']]=(r['owner_ref'],r['actual_owner_endpoints']['1'],r['actual_owner_endpoints']['2'],[])
    return model,nets,fun,reviewed
def endpoint_set(nodes):return {(n['ref'],str(n['pin']))for n in nodes}
def validate(d,c):
    model,nets,fun,reviewed=c;errors=[];rows=d.get('capacitors',[]);caps={r for r in model if r.startswith('C')}
    def check(ok,msg):
        if not ok:errors.append(msg)
    check(len(rows)==723 and len({r['ref']for r in rows})==723,'Exclusive723 required')
    check({r['ref']for r in rows}==caps,'Exact native capacitor population required')
    for r in rows:
        ref=r['ref'];owner=r['owner'];cap=model.get(ref);own=model.get(owner)
        if not cap or not own:errors.append('Missing physical owner/cap '+ref);continue
        check(r['actual_MPN']==cap['mpn']and r['actual_owner_MPN']==own['mpn'],'Actual MPN '+ref)
        check(r['source_block']==cap['source_block'],'Source block '+ref)
        check(r.get('physical_loop_or_effective_capacitance_qualified')is False,'No fabricated physical proof '+ref)
        pp=endpoint_set(r['power_nodes']);gg=endpoint_set(r['return_nodes']);pn=nets[(ref,r['cap_power'])];gn=nets[(ref,r['cap_return'])]
        check(bool(pp)and all(a==owner for a,b in pp),'Declared owner and physical signal endpoints '+ref)
        path=r.get('reviewed_series_path',[])
        direct=bool(pp)and all(nets.get(k)==pn for k in pp)
        if not direct and len(path)==3:
            one,two,three=path
            direct=two['reference']==three['reference']and two['reference'].startswith('R')and nets.get((one['reference'],str(one['pin'])))==nets.get((two['reference'],str(two['pin'])))and nets.get((three['reference'],str(three['pin'])))==pn
        check(direct,'Signal topology '+ref);check(bool(gg)and all(nets.get(k)==gn for k in gg),'Own-domain return '+ref)
        check(r['actual_cap_signal_net']==pn and r['actual_cap_return_net']==gn,'Actual capacitor net '+ref)
        if ref in reviewed:
            eo,ep,eg,es=reviewed[ref];check(owner==eo and pp==endpoint_set(ep)and gg==endpoint_set(eg),'Prior independently reviewed owner '+ref)
            check(path==es,'Reviewed series path retained '+ref)
        # A generic named owner is constrained by the frozen component role or
        # decouples/source_reference, not selected by its rail. Special exact
        # pin functions below independently guard equal-rail substitutions.
        elif r['evidence'].startswith('Frozen source component role'):
            declared=cap.get('decouples');names=re.findall(r'\bU\d+',cap.get('role',''))
            if declared:
                valid=own.get('source_reference')==declared and own['source_block']==cap['source_block']
            else:
                valid=len(set(names))==1 and (owner==names[0]or own.get('source_reference')==names[0]and own['source_block']==cap['source_block'])
            check(valid,'Source-declared owner '+ref)
        if cap['source_block']=='fpga_core'and owner=='U1001':
            target=cap['placement_target']
            expected={target}if target in fun['U1001']else{k for k,v in fun['U1001'].items()if v==('VCC'if target=='VCC cluster'else'VCCIO'+target)}
            check(pp=={('U1001',k)for k in expected},'Physical FPGA bank/ball '+ref)
        if r['category'].startswith('MCU_'):
            kind=own['kind'];vp,gp,rp=('6','7','10')if kind=='G031C'else('4','5','6')
            expect='5'if r['category']=='MCU_VREF_bypass'else rp if r['category']=='MCU_reset_RF_filter'else vp
            check(pp=={(owner,expect)}and gg=={(owner,gp)},'Exact MCU package/function '+ref)
        if r['category']=='DO_post_RCB_terminal_RF_filter':
            check(own['mpn']=='CSD19538Q3AT'and pp=={(owner,k)for k in ['5','6','7','8','9']},'Post-RCB physical drain '+ref)
            check(all(fun[a][b]in ['GND','EP_GND']for a,b in gg),'DO driver return '+ref)
        if r['category']=='AC_only_Y2_chassis_coupling':
            check(cap['mpn']=='VY2472M49Y5US63V7'and all(nets[k].endswith('/CHASSIS')for k in gg),'Y2 AC-only chassis return '+ref)
            expected_ports={'C19501':'J15004','C19502':'J19513','C19503':'J19501','C19504':'J19534','C19505':'J19529','C19506':'J19530','C19507':'J19531','C19508':'J19532','C19509':'J19533'}
            check(owner==expected_ports.get(ref),'Exact physical Y2 coupling region '+ref)
        if r['category'].startswith('DO_')and r['category']!='DO_post_RCB_terminal_RF_filter':
            expected_quad={f'C{base+i}':driver for base,driver in [(10005,'U10004'),(10014,'U10009'),(10027,'U10017'),(10036,'U10022')]for i in range(5)}
            check(owner==expected_quad.get(ref),'Exact physical DO quad '+ref)
        # Function snapshots must agree with actual native functions even if
        # another functional pad happens to be connected to the same rail.
        for side,ns in [('signal',r['power_nodes']),('return',r['return_nodes'])]:
            actual=[dict(ref=n['ref'],pin=str(n['pin']),function=fun[n['ref']][str(n['pin'])],net=nets.get((n['ref'],str(n['pin']))))for n in ns]
            claimed=[{k:z[k]for k in ['ref','pin','function','net']}for z in r['actual_native_function_nodes'][side]]
            check(actual==claimed,'Actual native pin function snapshot '+ref)
    return errors
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--manifest',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args();assert not args.out.exists();args.out.mkdir(parents=True)
    d=json.loads(args.manifest.read_text());c=context();errors=validate(d,c);tests=[]
    def mutation(name,fn):
        x=copy.deepcopy(d);fn(x);e=validate(x,c);tests.append(dict(name=name,rejected=bool(e),errors=e[:6]));assert e,name
    def row(x,ref):return next(r for r in x['capacitors']if r['ref']==ref)
    mutation('Missing capacitor',lambda x:x['capacitors'].pop())
    mutation('Duplicate capacitor replacing a real capacitor',lambda x:x['capacitors'].__setitem__(-1,copy.deepcopy(x['capacitors'][0])))
    mutation('Wrong fitted MPN',lambda x:row(x,'C13004').__setitem__('actual_MPN','unverified'))
    mutation('Wrong owner MPN',lambda x:row(x,'C13004').__setitem__('actual_owner_MPN','STM32G031K8T6'))
    mutation('Same-rail MCU VREF swapped to VDD',lambda x:row(x,'C13004').__setitem__('power_nodes',[dict(ref='U13001',pin='6')] ))
    mutation('C48 NRST index incorrectly applied to K32 MCU',lambda x:row(x,'C13008').__setitem__('power_nodes',[dict(ref='U13004',pin='10')] ))
    mutation('Same-rail FPGA bank reservoir swapped to a different bank',lambda x:row(x,'C1028').__setitem__('power_nodes',[dict(ref='U1001',pin='H6')] ))
    mutation('DI filter upstream IN instead of SENSE',lambda x:row(x,'C8001').__setitem__('power_nodes',[dict(ref='U8001',pin='15')] ))
    mutation('DI logic NC7 substituted for ground',lambda x:row(x,'C8101').__setitem__('return_nodes',[dict(ref='U8001',pin='7')] ))
    mutation('DO terminal filter before reverse-blocking FET',lambda x:row(x,'C10010').__setitem__('power_nodes',[dict(ref='U10005',pin='1')] ))
    mutation('Field filter returned to logic ground',lambda x:row(x,'C10010').__setitem__('return_nodes',[dict(ref='U13001',pin='7')] ))
    mutation('Same-ground Y2 field coupling assigned to wrong physical port',lambda x:row(x,'C19504').__setitem__('owner','J19503'))
    mutation('Timing capacitor mislabeled as supply bypass',lambda x:row(x,'C3001').__setitem__('power_nodes',[dict(ref='U3001',pin='6')] ))
    mutation('Reference ESR path removed and treated as copper short',lambda x:row(x,'C14717').__setitem__('reviewed_series_path',[]))
    mutation('Hardware measurement fabricated',lambda x:row(x,'C13004').__setitem__('physical_loop_or_effective_capacitance_qualified',True))
    inputs={str(p):digest(p)for p in [args.manifest,SOURCE/'design.json',SOURCE/'netlist.xml',Path(__file__)]};result=dict(source_capacitors=723,errors=errors,baseline_pass=not errors,negative_controls=tests,all_negative_controls_rejected=all(t['rejected']for t in tests),input_hashes=inputs,source_modified=False,PCB_modified=False,physical_qualification=False)
    (args.out/'review.json').write_text(json.dumps(result,indent=2)+'\n');(args.out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','negative_controls']}));assert not errors,errors
if __name__=='__main__':main()
