"""Generate three real low-voltage regulator circuits from a frozen baseline ledger."""
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/logic_power"
NS = uuid.UUID("c93981d3-c876-4f11-b40f-23d1f657ca80")
RAILS = (("CORE_1V2", 1.2, 0.8, "fpga_core"), ("IO_3V3", 3.3, 0.4, "fpga_io_rx_isolators"),
         ("ESP_3V3", 3.3, 0.7, "esp_peak"))


def uid(key):
    return str(uuid.uuid5(NS, key))


def footprint(name, body, pads):
    lines = [f'(footprint "{name}" (version 20241229) (generator "pcbnew") (layer "F.Cu") (attr smd)',
             '(property "Reference" "REF**" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))',
             f'(property "Value" "{name}" (at 0 2.8 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))',
             f'(fp_rect (start {-body[0]/2} {-body[1]/2}) (end {body[0]/2} {body[1]/2}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))']
    for pin, x, y, width, height in pads:
        lines.append(f'(pad "{pin}" smd roundrect (at {x} {y}) (size {width} {height}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1))')
    # Reviewable copper pattern only; no PCB, placement or manufacturing output.
    return "\n".join(lines)+")\n"


def main():
    frozen = OUT / "input-electrical-design.json"
    design = json.loads(frozen.read_text(encoding="utf-8"))
    rails = {r["id"]: r for r in design["rails"]}
    loads = {r["id"]: r for r in design["power_loads"]}
    if (rails["CORE_5V"]["min_v"], rails["CORE_5V"]["max_v"]) != (4.85, 5.15):
        raise ValueError("Review changed CORE_5V envelope before regeneration")
    for rail, voltage, current, load in RAILS:
        if (rails[rail]["nominal_v"], loads[load]["rail"], loads[load]["budget_a"]) != (voltage, rail, current):
            raise ValueError(f"Review changed rail/load snapshot: {rail}")
    root_id = uid("root")
    pins = [(1,"PG",15.24,5.08,180,"open_collector"), (2,"SW",15.24,20.32,180,"power_out"),
            (3,"VOS",15.24,-10.16,180,"input"), (4,"GND",0,-40.64,90,"power_in"),
            (5,"EN",-15.24,5.08,0,"input"), (6,"VIN",-15.24,20.32,0,"power_in"),
            (7,"MODE/S-CONF",-15.24,-10.16,0,"input"), (8,"SS/TR",-15.24,-25.4,0,"input"),
            (9,"FB/VSET",15.24,-25.4,180,"input")]
    passive = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    coil = [(1,"",-5.08,0,0,"passive"),(2,"",5.08,0,180,"passive")]
    lib = [symbol("TPS62901RPJR",pins,'(rectangle (start -12.7 30.48) (end 12.7 -38.1) (stroke (width 0.254) (type default)) (fill (type background)))'),
           symbol("R",passive,'(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))',"R"),
           symbol("L",coil,'(rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width 0.254) (type default)) (fill (type none)))',"L"),
           symbol("C",passive,'(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none))) (polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))',"C")]
    conn_pins = {}
    for count in (2,6,9):
        cp = [(i,str(i),-5.08,-(i-1)*2.54,0,"passive") for i in range(1,count+1)]
        conn_pins[count] = cp
        lib.append(symbol(f"Conn{count}",cp,f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))',"J"))
    flag_pins = [(1,"pwr",0,0,90,"power_out")]
    lib.append(symbol("PWR_FLAG",flag_pins,"","#FLG"))
    items, positions, boms = [], {}, {}

    def place(name, ref, value, x, y, pin_list, fp="", mpn=""):
        positions[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pin_list}
        if name in ("R","C"):
            text_style, rx, ry, vy = effects(1.0,"(justify left)"), x+3.81, y-2.54, y+1.27
        else:
            text_style, rx, ry, vy = effects(1.0), x, y-6.35, y-3.81
        props = f'(property "Reference" {quote(ref)} (at {rx} {ry} 0) {text_style}) (property "Value" {quote(value)} (at {rx} {vy} 0) {text_style})' \
                f'(property "Footprint" {quote(fp)} (at {x} {y} 0) {effects(extra="hide")}) (property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props} (instances (project "logic_power" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')
        if not ref.startswith("#"):
            boms[ref] = {"value":value,"mpn":mpn,"footprint":fp}

    def label(ref, pin, net, dx=0, dy=0):
        x,y = positions[ref][str(pin)]; ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.9,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,value,size=1.1):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    cmin=6800*.95*.9955;cmax=6800*1.05*1.0045
    vref_min=(.6*.9875-.008)/.75;vref_max=(.6*1.0125+.008)/.75
    tss_min=cmin/2.7*vref_min-700;tss_max=cmax/2.3*vref_max+160
    rail_models = []
    for index,(rail,voltage,current,load) in enumerate(RAILS):
        offset=index*185.42; x=offset+99.06; y=132.08; ref=f"U{index+1}"
        place("TPS62901RPJR",ref,"TPS62901RPJR",x,y,pins,"CNC_Power:TPS62901_RPJ9","TPS62901RPJR")
        nets={1:rail+"_PG_OD",2:rail+"_SW",3:rail,4:"LOGIC_GND",5:rail+"_EN",6:"CORE_5V",7:rail+"_MODE",8:rail+"_SS",9:"LOGIC_GND" if index==0 else rail+"_VSET"}
        for pin,net in nets.items():
            label(ref,pin,net,dx=-43.18 if pin in (5,6,7,8) else 7.62 if pin !=4 else 0,dy=5.08 if pin==4 else 0)
        place("L",f"L{index+1}","2.2uH",offset+147.32,91.44,coil,"CNC_Power:XGL4020","XGL4020-222MEC")
        label(f"L{index+1}",1,rail+"_SW",dx=-25.4)
        label(f"L{index+1}",2,rail,dx=5.08)
        rbase=index*4
        for local,value,top,mpn,px in ((1,"76.8k 1%",rail+"_MODE","CRCW060376K8FKEA",offset+43.18),
                                       (2,"10k 1%",rail+"_EN","CRCW060310K0FKEA",offset+99.06),
                                       (3,"100k 1%",rail,"CRCW0603100KFKEA",offset+149.86)):
            rr=f"R{rbase+local}"; place("R",rr,value,px,200.66,passive,"Resistor_SMD:R_0603_1608Metric",mpn)
            label(rr,1,top,dy=-5.08); label(rr,2,"LOGIC_GND",dy=5.08)
        if index:
            rr=f"R{rbase+4}";place("R",rr,"301k 1%",offset+149.86,241.3,passive,"Resistor_SMD:R_0603_1608Metric","CRCW0603301KFKEA")
            label(rr,1,rail+"_VSET",dy=-5.08);label(rr,2,"LOGIC_GND",dy=5.08)
        caps=(("10uF 25V X7R","CORE_5V",offset+43.18,66.04,"Capacitor_SMD:C_1206_3216Metric","C3216X7R1E106K160AB"),
              ("22uF 10V X7S",rail,offset+104.14,66.04,"Capacitor_SMD:C_0805_2012Metric","C2012X7S1A226M125AC"),
              ("6.8nF 50V C0G",rail+"_SS",offset+63.5,241.3,"Capacitor_SMD:C_0603_1608Metric","GRM1885C1H682JA01D"))
        for j,(value,top,cx,cy,fp,mpn) in enumerate(caps):
            cr=f"C{index*3+j+1}";place("C",cr,value,cx,cy,passive,fp,mpn)
            label(cr,1,top,dy=-5.08);label(cr,2,"LOGIC_GND",dy=5.08)
        note(offset+20.32,39.37,f"{rail}: {voltage}V / {current}A reservation",1.6)
        note(offset+20.32,270.51,"76.8k selects VSET, 1MHz forced PWM and discharge.\nEN defaults off only with high-Z external controller.\nPG is raw open drain: external pull-up and supervision required.",1.05)
        vmax=voltage*1.0125; vmin=voltage*.9875
        conservative_input=current*vmax/(4.85*.85)+.05
        rail_models.append({"rail":rail,"regulator":ref,"output_nominal_v":voltage,"load_a":current,"ledger_load_id":load,
                            "regulation_only_min_v":vmin,"regulation_only_max_v":vmax,
                            "input_a_at_85pct_efficiency_plus_50ma":conservative_input,
                            "normal_ripple_a_at_nominal_frequency":vmax*(1-vmax/5.15)/(1.408e-6*1e6),
                            "startup_local_cap_current_a_model":32.208e-6*vmax/tss_min*1e6,
                            "regulation_includes_transient_or_layout":False})
    boundary={"JIN1":["CORE_5V","LOGIC_GND"],
              "JOUT1":["CORE_1V2","LOGIC_GND","IO_3V3","LOGIC_GND","ESP_3V3","LOGIC_GND"],
              "JCTRL1":[v for rail,_,_,_ in RAILS for v in (rail+"_EN",rail+"_PG_OD","LOGIC_GND")]}
    for ref,x,y,description in (("JIN1",81.28,312.42,"5V INPUT"),("JOUT1",276.86,312.42,"LOGIC RAILS"),("JCTRL1",477.52,304.8,"EXTERNAL SEQUENCER")):
        p=conn_pins[len(boundary[ref])];place(f"Conn{len(p)}",ref,description,x,y,p)
        for pin,net in enumerate(boundary[ref],1):label(ref,pin,net,dx=-48.26)
    for index,net in enumerate(("CORE_5V","LOGIC_GND")):
        ref=f"#FLG0{index+1}";place("PWR_FLAG",ref,"EXTERNAL",60.96+index*60.96,345.44,flag_pins);label(ref,1,net,dy=5.08)
    note(17.78,15.24,"THREE LOW-VOLTAGE REGULATORS - EXTERNAL SEQUENCING REQUIRED",2.1)
    note(17.78,25.4,"TPS62901 replaces the TPS62160 study here: tighter regulation and adjustable ramp. Frozen ledger unchanged. CORE_5V required 4.85–5.15V.")
    note(17.78,365.76,"No PG-to-EN cascade. PG thresholds do not prove strict FPGA rail windows; PG is undefined below 1.8V VIN.\n6.8nF soft start models 2.231ms nominal; loaded ramp, input fault and restart sequencing remain unmeasured.\nVCC/PLL must precede VCCIO; FPGA reset and package supply/filter/decoupling connections are outside this block.")
    note(281.94,345.44,"Discharge is conditional: requires a previous enable and input supply near 2V or above.\nNo guaranteed power-off discharge, latch-off, reverse-current blocking or machine permission.\nESP rail is separately regulated; independent upstream fault isolation is NOT implemented.")
    sch=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A2") (title_block (title "Baseline logic power regulator block") (date "2026-09-28") (rev "r0.1") (comment 1 "Engineering source; no PCB or physical qualification")) (lib_symbols {"".join(lib)})\n'+"\n".join(items)+"\n)\n"
    (OUT/"logic_power.kicad_sch").write_text(sch,encoding="utf-8")
    libtext="\n".join(s.replace('(symbol "CNC:', '(symbol "',1) for s in lib)
    (OUT/"CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT/"sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC") (type "KiCad") (uri "${KIPRJMOD}/CNC.kicad_sym") (options "") (descr "Logic power symbols")))\n',encoding="utf-8")
    (OUT/"logic_power.kicad_pro").write_text('{"meta":{"filename":"logic_power.kicad_pro","version":1}}\n',encoding="utf-8")
    (OUT/"CNC_Power.pretty").mkdir(exist_ok=True)
    rpj=[(1,-.625,-.25,.65,.2),(2,-.625,.25,.65,.2),(3,-.625,.75,.65,.2),
         (4,.45,.75,1,.2),(5,.625,.25,.65,.2),(6,.45,-.25,1,.2),
         (7,.5,-.925,.25,.55),(8,0,-.925,.25,.55),(9,-.5,-.925,.25,.55)]
    # TI RPJ0009A drawing 4224505/A; no exposed ground pad: pin 9 is VSET.
    (OUT/"CNC_Power.pretty/TPS62901_RPJ9.kicad_mod").write_text(footprint("TPS62901_RPJ9",(1.5,2),rpj),encoding="utf-8")
    # Coilcraft 1529-3: 2.37 mm center spacing, 0.98x3.4 mm pads.
    (OUT/"CNC_Power.pretty/XGL4020.kicad_mod").write_text(footprint("XGL4020",(4,4),[(1,-1.185,0,.98,3.4),(2,1.185,0,.98,3.4)]),encoding="utf-8")
    (OUT/"fp-lib-table").write_text('(fp_lib_table (version 7) (lib (name "CNC_Power") (type "KiCad") (uri "${KIPRJMOD}/CNC_Power.pretty") (options "") (descr "Manufacturer land-pattern candidates; no layout qualification")))\n',encoding="utf-8")
    envelope={"schema_version":1,"manufacturing_ready":False,"source_ledger_sha256":hashlib.sha256(frozen.read_bytes()).hexdigest(),
              "candidate_mpn":"TPS62901RPJR","replaces_study_candidate":"TPS62160DSGR",
              "pin_map":{"1":"PG","2":"SW","3":"VOS","4":"GND","5":"EN","6":"VIN","7":"MODE/S-CONF","8":"SS/TR","9":"FB/VSET"},
              "input_min_v":4.85,"input_max_v":5.15,"mode":{"setting":14,"resistor_ohm":76800,"frequency_hz_nominal":1000000,"forced_pwm":True,"vset":True,"discharge_selected":True},
              "boundary":boundary,"components":boms,"rails":rail_models,
              "soft_start":{"capacitance_pf":6800,"tolerance":.05,"tcr_ppm_per_k":30,"excursion_k":150,
                            "nominal_us":6800/2.5*.8+55,"model_min_us":tss_min,"model_max_us":tss_max,
                            "k_us_conservative_graph_bound":700,"reference_min_v_model":vref_min,"reference_max_v_model":vref_max,
                            "includes_datasheet_min_max_equations":True,"includes_loaded_ramp_or_startup_delay":False,"physically_qualified":False},
              "magnetics":{"inductance_uh":2.2,"initial_tolerance":.2,"dc_inductance_drop_allowance":.2,"effective_l_model_min_uh":1.408,
                            "dcr_max_ohm_at_25c":.0215,"isat_20pct_drop_a_at_25c":4.4,"frequency_lower_bound_qualified":False},
              "capacitors":{"input_nominal_uf":10,"input_effective_min_required_uf":3,"output_nominal_uf":22,
                            "output_effective_min_required_uf":6,"output_effective_max_allowed_uf":50,
                            "output_local_max_uf_tolerance_temperature":22*1.2*1.22,"external_load_capacitance_qualified":False,
                            "dc_bias_temperature_aging_qualified":False},
              "boundaries":{"complete_fpga_sequence":False,"pg_is_machine_permission":False,"external_pg_pullups_required":True,
                            "pg_valid_below_vin_1v8":False,"discharge_guaranteed_without_input":False,
                            "discharge_requires_previous_enable":True,"thermal_auto_restart":True,"independent_esp_input_isolation":False,
                            "physical_qualification":False}}
    (OUT/"design-envelope.json").write_text(json.dumps(envelope,indent=2)+"\n",encoding="utf-8")
    print(OUT/"logic_power.kicad_sch")


if __name__ == "__main__":
    main()
