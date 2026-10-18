"""Isolated source correction proposal, complete retained current cases."""
import json,hashlib,math,copy
from pathlib import Path
import layout_r1 as L
ROOT=Path.cwd();OUT=L.OUT

def screen(current,inductance,bulk_count,vin):
    lo=inductance*.8*.7;hi=inductance*1.2;fmin=398000.;v=5.05
    ripple_lo=v*(1-v/vin)/(lo*fmin);ripple_hi=v*(1-v/vin)/(hi*fmin)
    cout_min=bulk_count*330e-6*.8*.8+3*20.5e-6
    cout_max=bulk_count*330e-6*1.2*1.2+3*47e-6*1.2
    esr=2*.0065/bulk_count+.0006666666666666666
    peak=current+ripple_lo/2;correlated=current+ripple_hi/2
    ilim_min=.050/(.005*1.02);ilim_max=.062/(.005*.98)
    return {'load_A':current,'VIN_V':vin,'L_nominal_H':inductance,'L_screen_min_H':lo,'L_screen_max_H':hi,'f_min_assumed_Hz':fmin,
        'bulk_count':bulk_count,'Cout_min_F':cout_min,'Cout_max_F':cout_max,'ESR_assumed_Ohm':esr,
        'ripple_A_pp':ripple_lo,'normal_peak_A':peak,'shunt_limit_min_A':ilim_min,'shunt_limit_max_A':ilim_max,'minimum_limit_margin_A':ilim_min-peak,
        'unload_phase_correlated_V':math.sqrt(v*v+hi*correlated*correlated/cout_min)+correlated*esr,
        'unload_noncorrelated_V':math.sqrt(v*v+hi*peak*peak/cout_min)+peak*esr,
        'typical_75ns_delay_fault_peak_A':ilim_max+vin*75e-9/lo,'maximum_delay_or_fault_bound_guaranteed':False,
        'compensation_nominal_crossover_at_Cmin_Hz':9530/(2*math.pi*(5/.8)*(.005*10/.0012)*cout_min),
        'compensation_zero_Hz':1/(2*math.pi*9530*22e-9),'compensation_pole_including_38pF_Hz':1/(2*math.pi*9530*(330e-12+38e-12)),
        'ESR_zero_Hz':1/(2*math.pi*cout_min*esr),'inductor_hot_L_DCR_Isat_unqualified':True,'stability_startup_and_physical_rating_qualified':False}

def main():
    source=ROOT/'hardware/motherboard_power_entry/design.json';d=json.loads(source.read_text(encoding='utf-8'))
    review=ROOT/'reports/motherboard-compute-20260930/power-closure-r01/power-capacity-review.json';old=json.loads(review.read_text(encoding='utf-8'))['normal_cases'][1]
    normal=old['CORE5_total_normal_screen_a'];old_sbc=old['SBC_normal_screen_a'];aux=old['CM_AUX_5V_equivalent_screen_a']
    caseA=normal-old_sbc+4.15;caseB=caseA+aux
    proposal=copy.deepcopy(d)
    proposal['components']['L11001'].update(mpn='XAL1010-682MED',value='6.8uH 20%',role='CORE higher-inductance candidate for full retained load; hotL/loop/thermal qualification required')
    fifth=copy.deepcopy(d['components']['C11088']);fifth['role']='CORE fifth330uF output bulk proposed for full retained-load unload screen; loop/inrush qualification required'
    if 'C11089' in d['components']:raise ValueError('New capacitor reference occupied')
    proposal['components']['C11089']=fifth
    proposal['continuation_proposal']={'schema':'CORE-retained-full-current-correction-r1','status':'SOURCE_PROPOSAL_ONLY_NOT_ADOPTED','unchanged_original_board':L.live.SHA,'planning_current_A':caseB,'physical_board_current_rating_established':False}
    source_dest=OUT/'source-proposal/design.json';source_dest.parent.mkdir(exist_ok=True)
    if source_dest.exists():raise ValueError('Immutable source proposal exists')
    source_dest.write_text(json.dumps(proposal,indent=2)+'\n',encoding='utf-8')
    inputs=[source,review,ROOT/'reports/motherboard-power-entry-20260930/core7a-r04/receipt-r04.json',ROOT/'hardware/motherboard_power_entry/README.md',ROOT/'reports/motherboard-compute-20260930/power-closure-r01/audit.py',ROOT/'reports/motherboard-compute-20260930/power-closure-r01/sources/xal1010.pdf',ROOT/'research/core-converter/lm70660.pdf',Path(__file__)]
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    tests=[]
    for current in (caseA,caseB,8.):
        for ind in (4.7e-6,6.8e-6):
            for capcount in (4,5):
                for vin in (18.,30.):tests.append(screen(current,ind,capcount,vin))
    receipt={'source_original_sha256':hashes[str(source.resolve())],'proposal_sha256':hashlib.sha256(source_dest.read_bytes()).hexdigest(),
        'original_normal_case_A':normal,'original_SBC_case_A':old_sbc,'all_retained_nonSBC_A':normal-old_sbc,
        'source_load_cases':{'connector_total3p6_includes_AUX':{'common_SBC_A':4.15,'total_CORE_A':caseA,'documented_connector_scope_pending':True},
            'conservative_module3p6_plus_AUX':{'module_A':3.6,'CM_AUX_5V_equivalent_A':aux,'USB_A':.5,'HDMI_A':.05,'common_SBC_A':4.15+aux,'total_CORE_A':caseB}},
        'planning_uses_case':'conservative_module3p6_plus_AUX','original7A_board_rating_physically_unqualified':True,'proposed8A_envelope_is_not_physical_rating':True,
        'electrical_delta':{'L11001':{'old_MPN':'XAL1010-472MED','new_MPN':'XAL1010-682MED','old_uH':4.7,'new_uH':6.8,'same_original_manufacturer_land':d['components']['L11001']['footprint']},'C11089':fifth},
        'unchanged':{'U11007':'LM706A0RRXR','R11022':'5mohm exactKRL3216D-C-R005-F-T1','R11024_RT':'49.9kohm0.1%','R11025_CONFIG':'29.4kohmstandaloneDRSSdisabled','compensation_RC_CC_CHF':[9530,22e-9,330e-12],'fitted_twelve_motor_interfaces_and_all_other_loads':True},
        'primary_sources':{'converter':'https://www.ti.com/lit/ds/symlink/lm70660.pdf','inductor':'https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xal/xal1010/','inductor_pdf':'https://www.coilcraft.com/en-us/files/datasheet/xal1010/'},
        'XAL1010_682_primary_25C_values':{'L_uH':6.8,'tolerance_percent':20,'DCR_typ_mOhm':8.1,'DCR_max_mOhm':8.9,'SRF_typ_MHz':14,'Isat_typ_30percentLdrop_A':21.8,'Irms_20C_rise_characterization_A':14,'Irms_40C_rise_characterization_A':18.5,'same_family_mechanical_land':True,'hot_or_installed_ratings_guaranteed':False},
        'bounded_screens':tests,
        'mandatory_obligations':['ResolveJ15001module-versus-total3.6AcurrentallocationwithoutdroppingCM_AUXloads','recomputeLM706A0 compensation on completeeffectiveC,L/ESR/EA/temp/loadcorners; unchangedRCisnotstabilityproof','manufacturerhotinductorL/Isat/DCR/corelossandboardthermalofconverter,shunt,coil,caps','inputcapacitorRMSandlocalhotloop/Kelvinsense;C11089physicalplacementandallsourceconnectionsrequired','startup/inrushincludingnewbulkandTPS22990C110614.7uF25VeffectiveCTminimum/maximum;restart/UVLOfault/withdrawal','minimum-current-limit,nuisancetrip,maxfaultpeakandfuse/eFuse/sourcecoordination;75nstypnotguaranteedmax','fullconservative4.3963046ASBC/7.8820343ACORECu/vias/pads/connectors/dropandreturnsolves','sourceexportERC,exactsource/nativeparity,whole-boardrefillDRCuncappedconnectivitynoregression,SIDFMandphysicaltests'],
        'source_only':True,'native_jobs':0,'board_written':False,'manufacturing_ready':False,'adopted':False,'qualified_source_or_power':False,'source_hashes_before':hashes,'source_hashes_after':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in hashes}}
    (OUT/'source-correction-r1.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'caseA':caseA,'caseB':caseB,'commonSBC':4.15+aux,'new_source_parts':['L11001','C11089'],'proposal_sha256':receipt['proposal_sha256'],'old4p7_min_margin':[r['minimum_limit_margin_A'] for r in tests if r['load_A']==caseB and r['L_nominal_H']==4.7e-6 and r['bulk_count']==4 and r['VIN_V']==30.], 'new6p8_min_margin':[r['minimum_limit_margin_A'] for r in tests if r['load_A']==caseB and r['L_nominal_H']==6.8e-6 and r['bulk_count']==5 and r['VIN_V']==30.],'new6p8_5bulk_unload':[r['unload_noncorrelated_V'] for r in tests if r['load_A']==caseB and r['L_nominal_H']==6.8e-6 and r['bulk_count']==5 and r['VIN_V']==30.]}),flush=True)
if __name__=='__main__':main()
