"""Two independently limited encoder rails; frozen-input engineering schematic."""
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/encoder_power"
NS = uuid.UUID("2865be16-6a55-457f-a9af-e0f65a769a9b")


def uid(name):
    return str(uuid.uuid5(NS,name))


def main():
    # Snapshot creation is a deliberate caller action, never a generator refresh.
    frozen = OUT / "input-electrical-design.json"
    design = json.loads(frozen.read_text(encoding="utf-8"))
    reservation = next(row for row in design["power_loads"] if row["id"] == "encoder_supply")
    if reservation["rail"] != "CORE_5V" or reservation["budget_a"] != 0.4:
        raise ValueError("Review current-limit design against the changed input snapshot first")
    for channel in range(2):
        terminal = next(t for t in design["terminals"] if (t["connector"],t["position"]) == (f"JENC{channel}",7))
        if terminal["net"] != f"ENC{channel}_5V_LIMITED":
            raise ValueError("Encoder supply boundary differs from frozen ledger")
    root_id = uid("encoder-power-root")
    ic_pins = [(1,"IN",-15.24,15.24,0,"power_in"),(2,"GND",0,-30.48,90,"power_in"),
               (3,"EN",-15.24,0,0,"input"),(4,"~{FAULT}",15.24,0,180,"open_collector"),
               (5,"ILIM",-15.24,-15.24,0,"output"),(6,"OUT",15.24,15.24,180,"power_out")]
    rectangle = '(rectangle (start -12.7 25.4) (end 12.7 -27.94) (stroke (width 0.254) (type default)) (fill (type background)))'
    passive = [(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")]
    resistor = '(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    capacitor = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))' \
                '(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    library = [symbol("TPS2553DBVR-1",ic_pins,rectangle),symbol("R",passive,resistor,"R"),symbol("C",passive,capacitor,"C")]
    connectors = {}
    for count in (3,4,6):
        pins = [(i,str(i),-5.08,-(i-1)*2.54,0,"passive") for i in range(1,count+1)]
        body = f'(rectangle (start -2.54 2.54) (end 2.54 {-count*2.54}) (stroke (width 0.254) (type default)) (fill (type background)))'
        library.append(symbol(f"Conn{count}",pins,body,"J")); connectors[count] = pins
    library.append(symbol("PWR_FLAG",[(1,"pwr",0,0,90,"power_out")],"","#FLG"))
    items,positions = [],{}

    def place(name,ref,value,x,y,pins,footprint="",mpn=""):
        positions[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        text_style = effects(1.1,"(justify left)") if name in ("R","C") else effects()
        ref_y,value_y = (y-2.54,y+1.27) if name in ("R","C") else (y-5,y-2.5)
        props = f'(property "Reference" {quote(ref)} (at {x+4} {ref_y} 0) {text_style})' \
                f'(property "Value" {quote(value)} (at {x+4} {value_y} 0) {text_style})' \
                f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
                f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) '
                     f'(on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "encoder_power" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')

    def label(ref,pin,net,dx=0,dy=0):
        x,y = positions[ref][str(pin)]; ex,ey = round(x+dx,4),round(y+dy,4)
        if dx or dy:
            items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.95,"(justify left bottom)")} (uuid "{uid(ref+str(pin)+"label")}"))')

    def note(x,y,value,size=1.25):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value)}"))')

    for channel in range(2):
        offset = channel*266.7
        x,y = offset+139.7,137.16
        switch = f"U{channel+1}"
        enabled,fault,ilim,output = (f"ENC{channel}_POWER_EN",f"ENC{channel}_POWER_FAULT_N",f"ENC{channel}_ILIM",f"ENC{channel}_5V_LIMITED")
        place("TPS2553DBVR-1",switch,"TPS2553DBVR-1",x,y,ic_pins,"Package_TO_SOT_SMD:SOT-23-6","TPS2553DBVR-1")
        for pin,net in {1:"CORE_5V",2:"LOGIC_GND",3:enabled,4:fault,5:ilim,6:output}.items():
            label(switch,pin,net,0 if pin == 2 else -40.64 if pin in (1,3,5) else 10.16,5.08 if pin == 2 else 0)
        resistors = [("110k 1% 100ppm",ilim,"LOGIC_GND","CRCW0603110KFKEA",offset+45.72,190.5),
                     ("10k 1%",enabled,"LOGIC_GND","",offset+96.52,190.5),
                     ("10k 1%","IO_3V3",fault,"",offset+185.42,190.5),
                     ("100k 1% 100ppm",output,"LOGIC_GND","",offset+236.22,190.5)]
        for index,(value,top,bottom,mpn,rx,ry) in enumerate(resistors):
            ref = f"R{channel*4+index+1}"
            place("R",ref,value,rx,ry,passive,"Resistor_SMD:R_0603_1608Metric",mpn)
            label(ref,1,top,dy=-5.08); label(ref,2,bottom,dy=5.08)
        caps = [("100nF 25V X7R","CORE_5V",offset+45.72,"Capacitor_SMD:C_0603_1608Metric"),
                ("10uF 16V X7R","CORE_5V",offset+101.6,"Capacitor_SMD:C_0805_2012Metric"),
                ("100nF 25V X7R",output,offset+170.18,"Capacitor_SMD:C_0603_1608Metric"),
                ("1uF 16V X7R",output,offset+226.06,"Capacitor_SMD:C_0603_1608Metric")]
        for index,(value,top,cx,footprint) in enumerate(caps):
            ref = f"C{channel*4+index+1}"
            place("C",ref,value,cx,81.28,passive,footprint)
            label(ref,1,top,dy=-5.08); label(ref,2,"LOGIC_GND",dy=5.08)
        note(offset+27.94,43.18,f"ENCODER {channel}: INDEPENDENT LATCH-OFF CURRENT LIMIT",1.8)
        note(offset+27.94,53.34,"CORE_5V required 4.75–5.25V; this switch does not regulate voltage.\n200mA encoder load target; output at load depends on upstream and cable drop.")
        note(offset+27.94,218.44,f"Place C{channel*4+1} at U{channel+1} IN/GND and R{channel*4+1} close to ILIM.\n10k EN pulldown = off for a high-Z controller; no hardware restart latch drawn.\nFAULT is open-drain, pulled only to IO_3V3; not an output-voltage/power-good measurement.")
    boundary = {"JIN1":["CORE_5V","LOGIC_GND","IO_3V3"],
                "JOUT1":["ENC0_5V_LIMITED","LOGIC_GND","ENC1_5V_LIMITED","LOGIC_GND"],
                "JCTRL1":["ENC0_POWER_EN","ENC0_POWER_FAULT_N","LOGIC_GND","ENC1_POWER_EN","ENC1_POWER_FAULT_N","LOGIC_GND"]}
    for ref,count,x,value in (("JIN1",3,71.12,"INPUT RAIL BOUNDARY"),("JOUT1",4,251.46,"TO RX JPWR1"),("JCTRL1",6,439.42,"CONTROL/FAULT BOUNDARY")):
        place(f"Conn{count}",ref,value,x,269.24,connectors[count])
        for pin,net in enumerate(boundary[ref],1): label(ref,pin,net,dx=-43.18)
    for index,(net,x) in enumerate((("CORE_5V",63.5),("LOGIC_GND",116.84),("IO_3V3",170.18)),1):
        ref = f"#FLG0{index}"
        place("PWR_FLAG",ref,"EXTERNAL RAIL",x,327.66,[(1,"pwr",0,0,90,"power_out")]); label(ref,1,net,dy=5.08)
    note(17.78,15.24,"TWO CURRENT-LIMITED 5V ENCODER SUPPLIES - ENGINEERING BLOCK r0.1",2.1)
    note(17.78,27.94,"TPS2553DBVR-1: DBV/SOT-23-6, not DRV. Exact receiver net names retained. No main supply/input protection, controller or board layout.")
    note(17.78,304.8,"110k RILIM including 1%+150K/100ppm allowance: 207.445–283.605mA.\nTwo simultaneous pre-latch limits: 0.567210A plus switch supply current.\nLedger 0.4A is normal encoder load, not the fault budget. No full power budget approval.")
    note(236.22,304.8,"Overcurrent/reverse events latch off after deglitch; EN toggle or power cycle clears latch.\nTHERMAL SHUTDOWN CAN AUTO-RETRY, including the -1 part. External fault-inhibit policy is missing.\nA high EN retained across power return can energize the port. No automatic-restart prevention is claimed.")
    note(17.78,353.06,"Not a universal reverse-current barrier: reverse current can flow before protection responds.\nNo guarantee for 24V/reversed wiring, surge or system ESD. Board/cable faults need qualification.\n100k output bleed is passive; no active discharge or guaranteed de-energization time.")
    note(236.22,353.06,"EN and FAULT interfaces target 0–3.6V, shared ground; partial-power/backfeed tests remain open.\nDo not infer healthy power from an unasserted FAULT, especially with the switch/host unpowered.\nCapacitor MPN/effective capacitance and startup/load tests are pending. Unreleased engineering source.")
    sch = f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A2")\n' \
          '(title_block (title "Two protected encoder supply branches") (date "2026-09-28") (rev "r0.1") (comment 1 "Engineering block; fault interface/physical qualification incomplete"))\n' \
          f'(lib_symbols {"".join(library)})\n'+"\n".join(items)+"\n)\n"
    (OUT / "encoder_power.kicad_sch").write_text(sch,encoding="utf-8")
    libtext = "\n".join(s.replace('(symbol "CNC:', '(symbol "',1) for s in library)
    (OUT / "CNC.kicad_sym").write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding="utf-8")
    (OUT / "sym-lib-table").write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Encoder power engineering symbols")))\n',encoding="utf-8")
    (OUT / "encoder_power.kicad_pro").write_text('{"meta":{"filename":"encoder_power.kicad_pro","version":1}}\n',encoding="utf-8")
    rmin,rmax = 110*0.99*0.985,110*1.01*1.015
    imin,inom,imax = 25230/rmax**1.016/1000,23950/110**0.977/1000,22980/rmin**0.94/1000
    bleed = 5.25/(100000*0.99*0.985)
    envelope = {"schema_version":1,"scope":"two encoder branches only","manufacturing_ready":False,
                "source_ledger_sha256":hashlib.sha256(frozen.read_bytes()).hexdigest(),
                "mpn":"TPS2553DBVR-1","package":"DBV_SOT23_6","pins":{"1":"IN","2":"GND","3":"EN","4":"FAULT_N","5":"ILIM","6":"OUT"},
                "boundary":boundary,"input_v":{"min":4.75,"nominal":5.0,"max":5.25},
                "logic_io_v":{"min":0,"max":3.6,"ground":"LOGIC_GND","partial_power_qualified":False},
                "rilim":{"ohms":110000,"tolerance":0.01,"tcr_ppm_per_k":100,"temperature_excursion_k":150,
                         "minimum_kohms":rmin,"maximum_kohms":rmax,"mpn_reference":"CRCW0603110KFKEA"},
                "calculated_threshold_a":{"min":imin,"nominal":inom,"max":imax},
                "budget":{"normal_encoder_load_a_each":0.2,"ledger_normal_load_a_both":reservation["budget_a"],
                          "switch_quiescent_a_each_reservation":0.00014,
                          "output_bleed_max_a_each":bleed,
                          "normal_5v_a_both_with_switch_and_bleed":0.4+2*0.00014+2*bleed,
                          "simultaneous_limited_fault_a_both":2*imax,
                          "fault_a_both_with_switch_reservation":2*imax+2*0.00014,
                          "full_rail_fault_budget_qualified":False},
                "thermal":{"ron_max_ohms_dbv":0.135,"normal_switch_loss_w_each":(0.2+bleed)**2*0.135,
                           "normal_switch_drop_v_each":(0.2+bleed)*0.135,"near_short_dissipation_w_each":5.25*imax,
                           "initial_local_ambient_max_c":70,"qualified":False},
                "behavior":{"enable_default":"10k_pulldown_off_if_upstream_high_z","fault_active_low":True,
                            "fault_is_power_good":False,"fault_latch_cleared_by":["enable_toggle","input_power_cycle"],
                            "thermal_auto_retry_possible":True,"reverse_current_before_turnoff_possible":True,
                            "external_fault_inhibit_implemented":False,"active_output_discharge":False},
                "sources":["https://www.ti.com/lit/ds/symlink/tps2553-1.pdf","https://www.ti.com/product/TPS2553-1/part-details/TPS2553DBVR-1",
                           "https://www.vishay.com/docs/20035/dcrcwe3.pdf"]}
    (OUT / "design-envelope.json").write_text(json.dumps(envelope,indent=2)+"\n",encoding="utf-8")
    print(OUT / "encoder_power.kicad_sch")


if __name__ == "__main__":
    main()
