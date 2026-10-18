"""Read-only independent divider and pilot sourcing proposal, r0.1.

No project validator is imported and no generated expected analytical result is read.
Writes evidence only beside this script and the parent report, not hardware sources.
"""
from decimal import Decimal, getcontext, ROUND_HALF_UP
from itertools import product
from pathlib import Path
import csv
import hashlib
import json
import xml.etree.ElementTree as ET

getcontext().prec = 32
D = Decimal
OUT = Path(__file__).resolve().parent
REPORT = OUT.parent

def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, default=lambda x: str(x) if isinstance(x,D) else x)+'\n', encoding='utf-8')

# Authored from the circuit paths and manufacturer limits, not copied results.
DIVIDERS = [
    ('CORE_5V', [('R21','87900')], [('R29','92100')], ('R27','R35'),'10000',('4.85','5.15'),('4.95','5.05')),
    ('CORE_1V2', [('R41','1070'),('R42','261')], [('R49','1150'),('R50','316'),('R51','4.02')], ('R47','R55'),'1000',('1.15','1.25'),('1.185','1.215')),
    ('IO_3V3', [('R61','54500')], [('R69','57500')], ('R67','R75'),'10000',('3.2','3.4'),('3.25875','3.34125'))]
BOTTOM_REFS = {ref for row in DIVIDERS for ref in row[3]}
PRECISION_REFS = {ref for row in DIVIDERS for chain in row[1:3] for ref,_ in chain if ref!='R51'} | BOTTOM_REFS
CORE_BOTTOM = {'R47','R55'}

CLASSES = {
    'PLT': {'initial':D('.0001'),'tcr_per_k':D('.000005'),'delta_k':D(100)},
    'TNPW': {'initial':D('.001'),'tcr_per_k':D('.00001'),'delta_k':D(105)},
    'TNPU': {'initial':D('.0005'),'tcr_per_k':D('.00001'),'delta_k':D(105)},
    'RNCF': {'initial':D('.0001'),'tcr_per_k':D('.000005'),'delta_k':D(100)}}

def resistor_corners(ref, nominal, classes, extra_drift, stress=False):
    value = D(nominal)
    if ref=='R51':
        error = (1+D('.01'))*(1+D('.0001')*D(100))-1
        absolute = D(0)
    else:
        typ = classes.get(ref,'PLT'); cl = CLASSES[typ]
        # A symmetric envelope of compounded initial/TCR/drift errors is
        # conservative for both signs when each change is relative to resistance.
        error = (1+cl['initial'])*(1+cl['tcr_per_k']*cl['delta_k'])*(1+extra_drift)-1
        absolute = D(0)
        if stress and typ=='TNPW':
            # Conservatively combine two published test allowances, not a life guarantee.
            error = (1+error)*(1+D('.0005'))*(1+D('.0002'))-1
            absolute = D('.02')
        elif stress and typ=='RNCF':
            # Tol<=0.05%: endurance 0.05%, solder heat 0.05%.
            error = (1+error)*(1+D('.0005'))*(1+D('.0005'))-1
    return [value*(1-error)-absolute,value*(1+error)+absolute]

def threshold_bounds(chain,bref,bnom,classes,drift,stress=False):
    tops=[resistor_corners(ref,n,classes,drift,stress) for ref,n in chain]
    bottoms=resistor_corners(bref,bnom,classes,drift,stress)
    all_corners=[]
    for individual_top,bottom,vthr,bias in product(product(*tops),bottoms,(D('.4975'),D('.5025')),(D('-.000000015'),D('.000000015'))):
        top=sum(individual_top)
        # KCL: (Vrail-Vsense)/Rt = Vsense/Rb + input current.
        rail=vthr*(1+top/bottom)+bias*top
        all_corners.append(rail)
    # Separate monotonic expression provides an independent check of enumeration.
    minimum=D('.4975')*(1+sum(t[0] for t in tops)/bottoms[1])-D('.000000015')*sum(t[0] for t in tops)
    maximum=D('.5025')*(1+sum(t[1] for t in tops)/bottoms[0])+D('.000000015')*sum(t[1] for t in tops)
    assert minimum==min(all_corners) and maximum==max(all_corners)
    return [minimum,maximum],len(all_corners)

def scenario(name,classes,drift=D(0),stress=False):
    rows=[]
    for rail,uv_chain,ov_chain,brefs,bnom,limits,regulation in DIVIDERS:
        uv,uc=threshold_bounds(uv_chain,brefs[0],bnom,classes,drift,stress)
        ov,oc=threshold_bounds(ov_chain,brefs[1],bnom,classes,drift,stress)
        lo,hi=map(D,limits); rlo,rhi=map(D,regulation)
        margins=[uv[0]-lo,rlo-uv[1],ov[0]-rhi,hi-ov[1]]
        rows.append({'rail':rail,'allowed_v':[lo,hi],'regulation_only_v':[rlo,rhi],
                     'uv_bounds_v':uv,'ov_bounds_v':ov,'margins_v':margins,
                     'pass_four_static_margins':min(margins)>0,'corners_evaluated':uc+oc,
                     'guaranteed_common_startup_acceptance_interval_v':[uv[1],ov[0]],
                     'maximum_nominal_10Mohm_sense_probe_threshold_shift_uv_v':D('.5')*sum(D(n) for _,n in uv_chain)/D(10000000),
                     'maximum_nominal_10Mohm_sense_probe_threshold_shift_ov_v':D('.5')*sum(D(n) for _,n in ov_chain)/D(10000000)})
    return {'name':name,'class_overrides':classes,'additional_drift_fraction':drift,
            'combined_endurance_and_solder_test_sensitivity':stress,
            'all_rails_pass_four_static_margins':all(r['pass_four_static_margins'] for r in rows),'rails':rows}

def val_ohm(txt):
    text=txt.split()[0]
    return D(text[:-1])*D(1000) if text.endswith('k') else D(text)

def input_consistency():
    source=json.loads((OUT/'input-01-design.json').read_text(encoding='utf-8'))
    tree=ET.parse(OUT/'input-02-netlist.xml')
    source_comps={c.attrib['ref']:c.findtext('value') for c in tree.findall('.//components/comp')}
    checked=[]
    for rail,uv,ov,br,bnom,*_ in DIVIDERS:
        for ref,nom in uv+ov+[(br[0],bnom),(br[1],bnom)]:
            assert val_ohm(source['components'][ref]['value'])==D(nom)
            assert val_ohm(source_comps[ref])==D(nom)
            checked.append(ref)
    for ref in ('U3','U4','U5'):
        c=source['components'][ref]
        assert c['mpn']=='LTC2962HUD#TRPBF'
        assert c['pins']['6']==c['pins']['5'] and c['pins']['7']=='LOGIC_GND'
        assert c['pins']['3']=='LOGIC_GND' and c['pins']['10']=='CORE_5V'
    assert len(checked)==15 and len(set(checked))==15
    return {'independently_checked_divider_parts':checked,'precision_count':14,'ordinary_series_parts':['R51'],
            'nominal_values_unchanged':True,'read_generated_validator_results':False}

def offer(mpn,qty,stock,url,tiers):
    return {'mpn':mpn,'supplier':'DigiKey','observed_date':'2026-09-30','currency':'USD','per_board_quantity':qty,
            'packaging':'Tube' if mpn.startswith('LTC') else 'Cut Tape','minimum':1,'multiple':1,
            'observed_stock_pieces':stock,'url':url,'tiers':[{'minimum':q,'unit_usd':str(p)} for q,p in tiers],
            'no_quote_contact_or_order':True}

OFFERS = [
    offer('LTC2962HUD#PBF',3,71,'https://www.digikey.com/en/products/detail/analog-devices-inc/LTC2962HUD-PBF/9555593',[(1,D('9.56')),(10,D('7.436')),(25,D('6.90640')),(121,D('6.26033')),(363,D('5.95245')),(605,D('5.83864')),(1089,D('5.72638'))]),
    offer('TNPW06031K00BYEA',2,1026,'https://www.digikey.com/en/products/detail/vishay-dale/TNPW06031K00BYEA/18891209',[(1,D('.60')),(10,D('.497')),(50,D('.435')),(100,D('.4115')),(500,D('.36414'))]),
    offer('TNPW060310K0BYEA',4,4407,'https://www.digikey.com/en/products/detail/vishay-dale/TNPW060310K0BYEA/7660534',[(1,D('.56')),(10,D('.468')),(50,D('.4104')),(100,D('.3882')),(500,D('.34354'))]),
    offer('RNCF0603TKY10K0',4,71206,'https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RNCF0603TKY10K0/2269698',[(1,D('1.61')),(10,D('1.334')),(50,D('1.1716')),(100,D('1.1105')),(500,D('.99044'))])]

def money(n):return n.quantize(D('.01'),rounding=ROUND_HALF_UP)

def offer_line(o,boards):
    q=o['per_board_quantity']*boards
    tier=max((t for t in o['tiers'] if t['minimum']<=q),key=lambda t:t['minimum'])
    available=q<=o['observed_stock_pieces']
    return {'mpn':o['mpn'],'required_pieces':q,'buy_pieces':q,'tier_minimum':tier['minimum'],
            'published_unit_usd':tier['unit_usd'],'published_price_reference_usd':money(D(tier['unit_usd'])*q),
            'observed_stock_covers_quantity':available,'currently_stock_supported_pilot_cash_usd':money(D(tier['unit_usd'])*q) if available else None,
            'stock_shortfall_pieces':max(q-o['observed_stock_pieces'],0),'source_url':o['url']}

def costs():
    before=json.loads((OUT/'input-04-MC_BOM_COST.json').read_text(encoding='utf-8'))
    rows=[]
    for boards in (1,10,100):
        old=next(s for s in before['summaries'] if s['build_boards']==boards)
        oldcash=D(old['known_published_purchase_cash_subtotal_usd'])
        oldlines={l['mpn']:D(l['published_purchase_cash_usd']) for l in before['lines'] if l['build_boards']==boards and l['published_purchase_cash_usd'] is not None}
        ltc=offer_line(OFFERS[0],boards);one=offer_line(OFFERS[1],boards);ten=offer_line(OFFERS[3],boards)
        pack=oldcash-oldlines['LTC2962HUD#TRPBF']+ltc['published_price_reference_usd']
        one_sub=pack-oldlines['PLT0603Z1001LST1']+one['published_price_reference_usd']
        pilot=one_sub-oldlines['PLT0603Z1002LST1']+ten['published_price_reference_usd']
        rows.append({'build_boards':boards,'original_known_purchase_cash_usd':oldcash,
                     'packaging_only_known_price_reference_usd':pack,
                     'packaging_only_known_purchase_cash_if_unchanged_other_offers_usd':pack if ltc['observed_stock_covers_quantity'] else None,
                     'packaging_and_core_1k_only_known_price_reference_usd':one_sub,
                     'conditional_precision_preserving_pilot_basket_known_price_reference_usd':pilot,
                     'conditional_pilot_basket_stock_supported_three_changed_lines_usd':pilot if ltc['observed_stock_covers_quantity'] else None,
                     'remaining_unpriced_mpn_count':old['unpriced_mpn_count'],
                     'new_lines':[ltc,one,ten],'complete_board_manufactured_cost_usd':None,'complete_controller_cost_usd':None,
                     'other_offer_availability_still_unqualified':True})
    return rows

def main():
    consistency=input_consistency()
    comparisons=[]
    choices=[('original',{}),('all_0p1pct_10ppm',{r:'TNPW' for r in PRECISION_REFS}),
             ('all_0p05pct_10ppm',{r:'TNPU' for r in PRECISION_REFS}),
             ('all_bottom_0p1pct_10ppm',{r:'TNPW' for r in BOTTOM_REFS}),
             ('all_bottom_0p05pct_10ppm',{r:'TNPU' for r in BOTTOM_REFS}),
             ('core_1k_0p1pct_10ppm',{r:'TNPW' for r in CORE_BOTTOM}),
             ('conditional_pilot_1k_TNPW_10k_RNCF',dict([(r,'TNPW') for r in CORE_BOTTOM]+[(r,'RNCF') for r in BOTTOM_REFS-CORE_BOTTOM]))]
    for name,classes in choices:
        comparisons.extend([scenario(name+'_fresh',classes),scenario(name+'_400ppm_sensitivity',classes,D('.0004'))])
    comparisons.append(scenario('conditional_pilot_combined_test_allowances',choices[-1][1],D('.0004'),True))
    # TNPW at manufacturer general-mode 125C: solder/endurance sensitivity applies even to the otherwise passing 1k proposal.
    comparisons.append(scenario('core_1k_combined_test_allowances',choices[-2][1],D('.0004'),True))
    tests=[]
    assert comparisons[0]['all_rails_pass_four_static_margins'];tests.append('Original fresh passes independently enumerated corners')
    assert comparisons[1]['all_rails_pass_four_static_margins'];tests.append('Original 400ppm sensitivity passes')
    assert not comparisons[2]['all_rails_pass_four_static_margins'];tests.append('Blanket 0.1pct negative control fails')
    assert not comparisons[4]['all_rails_pass_four_static_margins'];tests.append('Blanket 0.05pct negative control fails')
    assert comparisons[10]['all_rails_pass_four_static_margins'] and comparisons[11]['all_rails_pass_four_static_margins'];tests.append('Core1k-only fresh/400ppm pass')
    assert comparisons[12]['all_rails_pass_four_static_margins'] and comparisons[13]['all_rails_pass_four_static_margins'];tests.append('Conditional same-precision pilot fresh/400ppm pass')
    assert not comparisons[14]['all_rails_pass_four_static_margins'];tests.append('Wider stated stress allowances correctly prevent pilot lifetime qualification')
    assert comparisons[15]['all_rails_pass_four_static_margins'];tests.append('Core1k-only combined test allowances still pass static arithmetic')
    costs_rows=costs()
    assert costs_rows[0]['conditional_precision_preserving_pilot_basket_known_price_reference_usd']==D('101.95')
    assert costs_rows[2]['packaging_only_known_purchase_cash_if_unchanged_other_offers_usd'] is None
    tests.extend(['Known-only conditional pilot basket computes 101.95USD','LTC100-board stock shortfall cannot become available cash figure'])
    result={'proposal_revision':'SOURCING-OPT-r0.1','date':'2026-09-30','read_only_hardware_audit':True,
            'applied_to_source':False,'fabrication_ready':False,'physical_qualification':False,
            'packaging_only_candidate':'MC-PACK-001: LTC2962HUD#TRPBF -> LTC2962HUD#PBF at U2003/U2004/U2005',
            'packaging_substitution_electrical_change':False,'dividers':DIVIDERS,'class_models':CLASSES,
            'monitor_threshold_v':[D('.4975'),D('.5025')],'monitor_bias_a':[D('-.000000015'),D('.000000015')],
            'threshold_formula':'Vthr*(1+sum(Rtop)/Rbottom)+Imon*sum(Rtop)',
            'uncertainty_model':'symmetric conservative envelope of multiplicative initial/TCR/drift terms; individual resistor corners independently enumerated; no RSS or correlated tracking credit',
            'margin_order':['UV_min - rail_min','regulation_min - UV_max','OV_min - regulation_max','rail_max - OV_max'],
            'temperature_scope_c':[-40,125],'additional_drift_sensitivity_not_lifetime_guarantee':True,
            'startup_configuration_max_vcc_v':D('2.2'),'startup_configuration_us_typical_only':D('500'),
            'reset_release_delay_ms':[160,240],'three_stage_release_delay_ms':[480,720],
            'dynamic_20ms_fault_bound_proven':False,'manufacturer_no_intentional_comparator_hysteresis':True,
            'input_consistency':consistency,'corner_checks':comparisons,'offers':OFFERS,'costs':costs_rows,
            'checks':tests,'total_numeric_corners':sum(r['corners_evaluated'] for s in comparisons for r in s['rails']),
            'resistor_substitution_current_status':'NOT APPLIED; parent explicitly deferred every resistor change; RNCF test drift exceeds original400ppm assumption',
            'non_E96_values_ohm':[54500,57500,87900,92100],
            'four_non_E96_values_in_stock_exact_nominal_lower_cost_offers':None}
    save('independent-calculations.json',result)
    (REPORT/'SOURCING_OPTIMIZATION_PROPOSAL.json').write_text(json.dumps(result,indent=2,default=str)+'\n',encoding='utf-8')
    print(json.dumps({'checks':len(tests),'numeric_corners':result['total_numeric_corners'],'costs':costs_rows},indent=2,default=str))

if __name__=='__main__': main()
