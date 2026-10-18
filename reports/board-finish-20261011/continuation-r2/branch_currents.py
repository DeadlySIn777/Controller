"""Source-bound passive screens and explicitly conditional branch IC reservations."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent/'branch-load-audit'
INV=HERE/'inventory-r2.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    inv=json.loads(INV.read_bytes());c=inv['selected_components'];rows=[]
    def resistor(ref):
        value=c[ref]['value'];m=re.fullmatch(r'([\d.e+]+)R\s*(0\.1|1)%',value)
        if not m:raise ValueError('Unsupported resistor value '+ref+': '+value)
        return float(m[1]),float(m[2])/100
    def rmin(ref):r,t=resistor(ref);return r*(1-t)
    def connected(a,b):
        if not {p['net'] for p in c[a]['pins']} & {p['net'] for p in c[b]['pins']}:raise ValueError('Disconnected resistor pair')
    def direct(name,ref):
        rows.append({'name':name,'refs':[ref],'at_v':30,'nominal_a':30/resistor(ref)[0],'initial_tolerance_screen_a':30/rmin(ref),'basis':'30 V; source initial resistor tolerance only; temperature/aging not bounded here'})
    def divider(name,top,bottom,parallel=None):
        connected(top,bottom);bot=resistor(bottom)[0];bmin=rmin(bottom)
        if parallel:bot=1/(1/bot+1/resistor(parallel)[0]);bmin=1/(1/bmin+1/rmin(parallel))
        rows.append({'name':name,'refs':[top,bottom]+([parallel] if parallel else []),'at_v':30,'nominal_a':30/(resistor(top)[0]+bot),'initial_tolerance_screen_a':30/(rmin(top)+bmin),'basis':'Parallel post-switch bleed assumes TMUX1511 on resistance zero (conservative for supply current); ADC leakage/dynamic input current separate' if parallel else '30 V; source initial resistor tolerance; IC input leakage separate'})
    for i,(top,bot,bleed) in enumerate([('R14058','R19401','R14062'),('R14064','R19402','R14068')]):
        divider('PRB'+str(i)+' input UVLO',top,bot);direct('PRB'+str(i)+' output bleed',bleed)
    for i,(top,bot,bleed,montop,monbot,post) in enumerate([('R19021','R19022','R19024','R19067','R19068','R19069'),('R19028','R19029','R19031','R19070','R19071','R19072'),('R19034','R19035','R19037','R19073','R19074','R19075')]):
        divider('SENS'+str(i)+' input UVLO',top,bot);direct('SENS'+str(i)+' output bleed',bleed);divider('SENS'+str(i)+' loaded monitor',montop,monbot,post)
    direct('SAFE output bleed','R19039');divider('SAFE monitor UV','R19041','R19042');divider('SAFE monitor OV','R19043','R19044');divider('SAFE loaded ADC monitor','R19076','R19077','R19078');direct('ARM_LAMP output bleed','R19061')
    report={'verdict':'PASS_SOURCE_PASSIVE_SCREEN_ONLY','inventory_sha256':sha(INV),'source_sha256':inv['source_sha256_after'],'rows':rows,'conditional_ic_terms':[{'part':'MAX17612A','refs':['U19004','U19005','U19006','U14026','U14027'],'table_max_a':.00121,'condition':'VIN 24 V, EN 5 V; TA electrical-table range -40 to 125 C unless noted','proposed_planning_reservation_a':.0015,'full_18_30v_max_guaranteed':False,'uvlo_ovlo_leak_max_abs_a':1e-7,'source':'https://www.analog.com/media/en/technical-documentation/data-sheets/max17612a-max17612c.pdf'},{'part':'TPS1H000-Q1','refs':['U19007','U19018'],'operating_table_max_a':.005,'condition':'VS 13.5 V, IN 5 V, DIAG_EN 0 V, IOUT 0.1 A, ICL 0.5 A; max column confirmed by primary PDF coordinates','off_diag_table_max_a':.003,'off_diag_condition':'VS 13.5 V, IN 0 V, DIAG_EN 5 V','proposed_planning_reservation_a':.008,'basis':'Sum of two distinct-mode maxima is a conservative planning reservation, not a guaranteed enabled-diagnostics bound','full_18_30v_max_guaranteed':False,'source':'https://www.ti.com/lit/ds/symlink/tps1h000-q1.pdf'}],'source_replayed':all(sha(Path(p))==h for p,h in inv['source_sha256_after'].items()),'ic_current_limit_resistors_are_not_added_as_external_output_load':True,'limits':['Not a guaranteed full-temperature passive maximum: MPN temperature/aging coefficients remain separate.','MAX UVLO and ADC/LTC input currents require separate mode-aware accounting.','Planning reservations do not establish silicon corner bounds or physical rail capacity.'],'native_jobs':0,'gpu_jobs':0}
    if not report['source_replayed']:raise ValueError('Source changed')
    target=HERE/'passive-and-ic-screen-r1.json'
    if target.exists():raise ValueError('Existing receipt')
    target.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'passive_total_a':sum(x['initial_tolerance_screen_a'] for x in rows),'receipt':str(target),'sha256':sha(target)}))
if __name__=='__main__':main()
