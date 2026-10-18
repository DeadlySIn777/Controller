"""Build the proposed electrical ledger. Values are review targets, not qualified ratings."""
from pathlib import Path
import csv
import json
import math
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware"
ENDPOINT_RTL = ROOT / "gateware/rtl/cnc_endpoint.v"


def rtl_watchdog_cycles(path=ENDPOINT_RTL):
    """Read WATCHDOG_CYCLES from the reference endpoint RTL so the ledger cannot drift from it."""
    match = re.search(r"parameter\s+integer\s+WATCHDOG_CYCLES\s*=\s*(\d+)", path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"WATCHDOG_CYCLES parameter not found in {path}")
    return int(match.group(1))


CONVERSION_RESERVE_A = 0.05  # explicit reserve added to each derived converter-input reservation


def _round_up(value, step=0.01):
    return math.ceil(round(value / step, 6)) * step


def converter_input(load_a, vout, vin=5.0, efficiency=0.85, reserve_a=CONVERSION_RESERVE_A):
    """Input current reservation for a buck stage: computed value plus a stated reserve, rounded up to 10 mA."""
    raw = load_a * vout / vin / efficiency
    budget = round(_round_up(raw + reserve_a), 2)
    return budget, f"{load_a:g}A*{vout:g}V/{vin:g}V/{efficiency:g}={raw:.4f}A plus {reserve_a:g}A reserve, rounded up to 10mA"


FPGA_CLOCK_HZ = 50000000


def build():
    wd_cycles = rtl_watchdog_cycles()
    # Single source for the downstream rail loads; the CORE_5V-side converter inputs are derived from these.
    io3v3_load, esp3v3_load, core1v2_load = 0.4, 0.7, 0.8
    io3v3_input = converter_input(io3v3_load, 3.3)      # IO_3V3 reservation fpga_io_rx_isolators
    esp3v3_input = converter_input(esp3v3_load, 3.3)    # ESP_3V3 reservation esp_peak
    core1v2_input = converter_input(core1v2_load, 1.2)  # CORE_1V2 reservation fpga_core
    d = {
        "schema_version": 1, "revision": "electrical-r0.1", "date": "2026-09-28",
        "status": "proposed_not_qualified", "manufacturing_ready": False,
        "scope": "Six-joint costing profile; full electrical ledger plus independently drawn two-joint TX subcircuit. No full-board schematic/layout.",
        "host": {"engineering_baseline": "Radxa ROCK 3C RS112-D2", "production_alternative": "Radxa CM3 SODIMM RM117-D2E16",
                 "interface": "dedicated short 3.3V SPI, not Ethernet motion; customer Ethernet on SBC",
                 "qualification": "PREEMPT_RT/SPI driver, pinmux, thermal and loaded UI timing unproved"},
        "sources": {
            "T20": "https://www.efinixinc.com/docs/trion20-ds-v6.0.pdf",
            "TX": "https://www.ti.com/lit/ds/symlink/am26c31.pdf",
            "RX": "https://www.ti.com/lit/ds/symlink/am26lv32e.pdf",
            "DI": "https://www.ti.com/lit/ds/symlink/iso1212.pdf",
            "DO": "https://www.ti.com/lit/ds/symlink/tps4h160-q1.pdf",
            "ISO": "https://www.ti.com/product/ISO7740",
            "DAC": "https://www.ti.com/lit/ds/symlink/dac80501.pdf",
            "AMP": "https://www.ti.com/lit/ds/symlink/opa197.pdf",
            "BUCK": "https://www.ti.com/lit/ds/symlink/tps62160.pdf",
            "WDT": "https://www.ti.com/lit/ds/symlink/tps3431.pdf",
            "EFUSE": "https://www.ti.com/lit/ds/symlink/tps2663.pdf",
            "ROCK": "https://docs.radxa.com/en/rock3/rock3c/getting-started/before-start",
            "ROCK_GPIO": "https://docs.radxa.com/rock3/rock3c/hardware-design/hardware-interface",
            "CM3S": "https://dl.radxa.com/cm3s/docs/hw/RADXA_CM3S_V1.5_SCH.pdf",
            "ESP": "https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf",
            "PCBWAY": "https://www.pcbway.com/assembly-file-requirements.html"
        },
        "domains": [
            {"id":"LOGIC","ground":"LOGIC_GND","external_ties":"SBC USB/HDMI shields and differential cable signal references require reviewed chassis/earth topology"},
            {"id":"FIELD","ground":"FIELD_GND","external_ties":"Separate machine field supply; intentionally common within field I/O, not per-channel isolated"},
            {"id":"ANALOG","ground":"ANALOG_GND","external_ties":"Spindle analog reference only; isolated converter and digital controls required"},
            {"id":"CHASSIS","ground":"CHASSIS_PE","external_ties":"Shield bond at enclosure entry; no default logic/field-ground short"}
        ],
        "rails": [
            {"id":"CORE_24V","domain":"LOGIC","nominal_v":24,"min_v":18,"max_v":30,"capacity_a":2,"source":"external controller PSU; display branch excluded"},
            {"id":"CORE_5V","domain":"LOGIC","nominal_v":5,"min_v":4.85,"max_v":5.15,"capacity_a":6,"source":"required 18-30V input 5V/6A converter; MPN unresolved"},
            {"id":"IO_3V3","domain":"LOGIC","nominal_v":3.3,"min_v":3.2,"max_v":3.4,"capacity_a":1,"source":"TPS62160 from CORE_5V; sequenced after CORE_1V2"},
            {"id":"ESP_3V3","domain":"LOGIC","nominal_v":3.3,"min_v":3.2,"max_v":3.4,"capacity_a":1,"source":"separate TPS62160 from protected CORE_5V branch"},
            {"id":"CORE_1V2","domain":"LOGIC","nominal_v":1.2,"min_v":1.17,"max_v":1.23,"capacity_a":1,"source":"TPS62160 from CORE_5V; estimated load only"},
            {"id":"FIELD_24V","domain":"FIELD","nominal_v":24,"min_v":18,"max_v":30,"capacity_a":6,"source":"separate machine field supply; external motor/field loads not on controller PSU"},
            {"id":"FIELD_5V","domain":"FIELD","nominal_v":5,"min_v":4.85,"max_v":5.15,"capacity_a":0.1,"source":"wide-input buck required; do not use unqualified SOT23 LDO dissipation"},
            {"id":"ANALOG_12V","domain":"ANALOG","nominal_v":12,"min_v":11.4,"max_v":12.6,"capacity_a":0.083,"source":"TMR1-2412 candidate; verify actual regulation/ripple and load range"},
            {"id":"ANALOG_5V","domain":"ANALOG","nominal_v":5,"min_v":4.85,"max_v":5.15,"capacity_a":0.03,"source":"TLV76050 from ANALOG_12V; current provision not regulator rating"}
        ],
        "power_loads": [
            {"id":"sbc_budget","rail":"CORE_5V","budget_a":3,"basis":"engineering reservation; exact5V delivery/connector and measured SBC peak open"},
            {"id":"tx_cables","rail":"CORE_5V","budget_a":0.6,"basis":"conservative12drivers+termination reservation, not datasheet quiescent current"},
            {"id":"encoder_supply","rail":"CORE_5V","budget_a":0.4,"basis":"two independently current-limited5V encoder ports at0.2A each"},
            {"id":"io3v3_input","rail":"CORE_5V","budget_a":io3v3_input[0],"basis":io3v3_input[1]},
            {"id":"esp3v3_input","rail":"CORE_5V","budget_a":esp3v3_input[0],"basis":esp3v3_input[1]},
            {"id":"core1v2_input","rail":"CORE_5V","budget_a":core1v2_input[0],"basis":core1v2_input[1]},
            {"id":"misc5v","rail":"CORE_5V","budget_a":0.1,"basis":"supervision/interface reservation"},
            {"id":"fpga_io_rx_isolators","rail":"IO_3V3","budget_a":io3v3_load,"basis":"reservation; Efinity power estimate and toggle activity open"},
            {"id":"esp_peak","rail":"ESP_3V3","budget_a":esp3v3_load,"basis":"radio and boot margin; measure exact module image"},
            {"id":"fpga_core","rail":"CORE_1V2","budget_a":core1v2_load,"basis":"reservation; not a measured/estimated T20 netlist consumption"},
            {"id":"field_outputs","rail":"FIELD_24V","budget_a":4.3,"basis":"8*0.5A +6*0.05A; excludes external motor drive power"},
            {"id":"field_control","rail":"FIELD_24V","budget_a":0.06,"basis":"switch quiescent, buck and sensing provision; sensors separately verified"},
            {"id":"field_isolation","rail":"FIELD_5V","budget_a":0.05,"basis":"5isolators/gate/diagnostic reservation"},
            {"id":"analog_total","rail":"ANALOG_12V","budget_a":0.03,"basis":"DAC/isolator5V input + amplifier/clamp reservation"},
            {"id":"analog_digital","rail":"ANALOG_5V","budget_a":0.02,"basis":"DAC and ISO7740 reservation"},
            {"id":"logic_converter_input","rail":"CORE_24V","budget_a":None,"basis":None},
            {"id":"analog_converter_input","rail":"CORE_24V","budget_a":0.06,"basis":"isolated stage input reservation at minimum supply"}
        ],
        "interfaces": [
            {"id":"step_dir","channels":12,"domain":"LOGIC","type":"5 V-supplied differential TX, nonisolated","target":"250 ksteps/s electrical goal, minimum 2 us STEP high/low and 2 us DIR guard; cable/drive may require slower","design_goal_steps_per_s":250000,"reference_rtl_limit_steps_per_s":195312.5,"rate_evidence":"Design goal unachieved. Current reference RTL accumulator increment cap 0x01000000 at 50 MHz limits rate to 195312.5 steps/s; not a physical measurement.","reset":"high_Z","qualification":"remote fail-safe bias, reference common-mode, partial-power and cable EMC open"},
            {"id":"encoder","channels":6,"domain":"LOGIC","type":"two differential ABZ ports, nonisolated","target":"5V differential encoder sources; maximum1Medges/s per signal proposed; common-mode acceptance -7..+7V only after protection review","reset":"counts invalid until initialization/homing policy","qualification":"termination, differential threshold, open-wire behavior and timestamp bound open"},
            {"id":"digital_input","channels":22,"domain":"FIELD","type":"sinking input for PNP sources/dry contact to field positive","operating_min_v":0,"operating_max_v":30,"nominal_v":24,"guaranteed_low_target_v":5,"guaranteed_high_target_v":15,"isolation":"FIELD to LOGIC; common FIELD_GND","qualification":"threshold tolerance/EMC/filter latency to verify; neither NPN mode nor AC input"},
            {"id":"general_output","channels":8,"domain":"FIELD","type":"protected sourcing DC","operating_min_v":18,"operating_max_v":30,"continuous_target_a":0.5,"bank_target_a":2,"reset":"off","qualification":"load/inrush/inductive energy and continuous thermal tests open; not dry contacts"},
            {"id":"drive_enable","channels":6,"domain":"FIELD","type":"protected sourcing DC","operating_min_v":18,"operating_max_v":30,"continuous_target_a":0.05,"reset":"off","qualification":"drive input must accept24V sourcing; no STO rating"},
            {"id":"spindle_analog","channels":1,"domain":"ANALOG","type":"isolated0-10V source","operating_min_v":0,"operating_max_v":10,"load_min_ohm":10000,"reset":"zero_request_and_separate_run_off",
             "output_swing_budget":{"dac_reference_v":2.5,"dac_gain":1,"dac_full_scale_v":2.5,"dac_rail":"ANALOG_5V","dac_rail_min_v":4.85,"dac_headroom_min_v":2.35,"amp_gain":4,"amp_gain_network":"30k/10k 0.1%","amp_rail":"ANALOG_12V","amp_rail_min_v":11.4,"amp_output_full_scale_v":10.0,"amp_headroom_min_v":1.4,"load_min_ohm":10000,"basis":"Calculated from ledger rail minima and OPA197 swing-to-rail spec at <=1mA load; a 0-5V DAC range with gain two cannot reach 10V below a 5V rail. Not a measurement."},
             "qualification":"zero clamp, offset/gain/temperature/load/settling and VFD short protection unresolved"},
            {"id":"host_spi","channels":1,"domain":"LOGIC","type":"3.3V mode0 exclusive internal SPI","target":"start<=5MHz; raise only after CDC/timing/SI qualification; no HMI/touch sharing"},
            {"id":"esp_service","channels":1,"domain":"LOGIC","type":"3.3V UART + PGOOD + DISARMED observation","target":"UART1152008N1 study; GPIO assignment omitted; powered-off isolation/buffering required","reset":"ESP has no physical motion, host-reset or inhibit authority"}
        ],
        "channels": [], "components": [], "required_parts": [], "pin_reservations": [],
        "logic_links": [
            {"id":"fpga_tx","source_domain":"LOGIC","destination_domain":"LOGIC","source_rail":"IO_3V3","destination_supply":"CORE_5V","source_voh_min":2.4,"source_vol_max":0.4,"destination_vih_min":2.0,"destination_vil_max":0.8,"destination_input_abs_max":5.5,"source_max_v":3.4,"bridge":"direct TTL-compatible input plus33ohm, no5V pull-up"},
            {"id":"rx_fpga","source_domain":"LOGIC","destination_domain":"LOGIC","source_rail":"IO_3V3","destination_supply":"IO_3V3","source_voh_min":2.4,"source_vol_max":0.4,"destination_vih_min":2.0,"destination_vil_max":0.8,"destination_input_abs_max":3.6,"source_max_v":3.4,"bridge":"3.3V receiver; verify load-specific datasheet limits before freeze"},
            {"id":"output_commands","source_domain":"LOGIC","destination_domain":"FIELD","source_rail":"IO_3V3","destination_supply":"FIELD_5V","bridge":"galvanic_isolator","isolator_mpn":"ISO7740FDBQR"},
            {"id":"field_faults","source_domain":"FIELD","destination_domain":"LOGIC","source_rail":"FIELD_5V","destination_supply":"IO_3V3","bridge":"galvanic_isolator","isolator_mpn":"ISO7740FDBQR","direction":"separate reversed chip, not reverse pins on command chips"},
            {"id":"analog_commands","source_domain":"LOGIC","destination_domain":"ANALOG","source_rail":"IO_3V3","destination_supply":"ANALOG_5V","bridge":"galvanic_isolator","isolator_mpn":"ISO7740FDBQR"}
        ],
        "fpga": {"reference_mpn":"T20F256C4","advertised_gpio":195,"reserved_bank_voltage":3.3,"physical_mapping_complete":False,
                 "pin_assignment_rule":"No package balls assigned until package CSV, Efinity IO placement and all bank/config reservations reviewed",
                 "clock_hz":FPGA_CLOCK_HZ,"core_voltage_v":1.2,"clock_and_reset":"external clock; asynchronous inhibit assertion; reset release synchronized independently per clock domain",
                 "sequencing":"VCC/PLL first; then VCCIO; unused MIPI connection per F256 datasheet Table66; hold CRESET_N until all rails stable; exact times unresolved",
                 "temperature":"C4 commercial grade only; industrial environment claim blocked; no silent I4 price substitution"},
        "permission": {
            "required_true":["RAILS_OK","CONFIG_VALID","EXTERNAL_PERMIT","HW_WATCHDOG_OK","FPGA_ARM_LATCH"],
            "esp_in_required_path":False,"hardware_implementation_status":"not_drawn",
            "watchdog_owner":"FPGA useful accepted control-cycle progress; independent TPS3431 removes hardware permission on progress loss",
            "watchdog_wdi_rule":"No free-running timer, ESP heartbeat or network activity may service it; bound repetition/accepted sequence in endpoint",
            "watchdog_wdi_implementation":"Not exposed by current reference RTL; additional gateware/board integration required",
            "rtl_watchdog_cycles":wd_cycles,"rtl_watchdog_ms":wd_cycles*1000/FPGA_CLOCK_HZ,
            "rtl_watchdog_source":"gateware/rtl/cnc_endpoint.v WATCHDOG_CYCLES at fpga.clock_hz; implemented accepted-progress timeout in the reference endpoint",
            "external_watchdog_study_ms":20,"external_watchdog_status":"TPS3431 supervisory study value; simulation study only; select timing capacitor/tolerance and machine stop contract",
            "fault":"Latch disarmed; output permission removed; fresh verified state and explicit rearm required",
            "tx":"drive G low with /G high; field pair high-Z; active STEP0 before permit release; do not claim glitch-free transitions without test",
            "field":"gate14commands on LOGIC side before isolation; ISO7740F defaults low;14switch-input external pulldowns; no ESP gating",
            "analog":"DAC zero request; separate spindle run off; physical zero clamp still missing",
            "safety_boundary":"operational stop only; machine protective circuit/STO/brakes external and machine-specific"
        },
        "power_protection": {
            "topology":"Physical DC-rated entry fuse in each CORE and FIELD supply, then coordinated electronic protection; branch devices where useful. High-side output ICs already provide channel protection.",
            "entry_fuses":["F_CORE", "F_FIELD"],
            "efuse_family_candidate":"TPS2663; exact ordering variant and MODE configuration unresolved",
            "efuse_mode":"Latched off for FIELD; recovery does not rearm actuators. Firmware cannot bypass current/voltage limits.",
            "reverse_polarity":"TPS2663 requires external reverse-polarity FET implementation; not credited as built-in complete reverse protection",
            "coordination_open":["PSU current-limit/foldback", "minimum and maximum prospective fault current", "wire and connector ampacity", "DC breaking capacity", "time-current and I-squared-t", "capacitor inrush", "eFuse thermal safe-operating area", "field load inductive return energy"],
            "not_claimed":"A generic eFuse is not an emergency-stop or an independently qualified protective circuit; fuse amp rating alone does not prove clearing."
        },
        "support_decisions": [
            "Three local TPS62160 converters are provisioned now: FPGA1.2V, FPGA/I/O3.3V and independent ESP3.3V. Earlier priced two-piece basket is incomplete.",
            "Keep only one TLV76050 candidate in the analog domain. FIELD5V needs a switching regulator pending thermal design; earlier second LDO is not accepted.",
            "ISO1212 already integrates input isolation; do not add another22input isolator channels.",
            "ISO7740 all4channels travel one direction. Four command chips plus one reversed chip provide16commands+4faults; one additional chip serves analogSPI/inhibit.",
            "T20F256 requires external configuration storage/programming plan; Q100F3 embedded-flash claims do not apply.",
            "No 90W adapter or monitor supply compatibility conclusion until monitor exactinput/power, startup surge and converter losses are measured. Field outputs use external power."
        ],
        "release_blockers": [
            "Complete schematic and layout absent; TX block is not a complete controller",
            "Actual drive/sensor/load and first-machine profile compatibility not frozen",
            "FPGA package/bank/boot pins and SBC/ESP pinmux unassigned",
            "Efinity synthesis, fitting, timing and power evidence missing",
            "Output permission latch/gates, transient networks and analog zero clamp incomplete",
            "Useful-progress WDI absent from current reference RTL",
            "250 ksteps/s electrical goal exceeds current reference RTL limit; end-to-end rate goal not achieved",
            "Power sequencing, partial power/backfeed and short-circuit behavior unmeasured",
            "ROCK3C PREEMPT_RT/SPI host, graphics load and thermal deadlines unqualified",
            "No PCBWay quote, complete BOM, fabrication release or conducted/radiated EMC evidence"
        ]
    }
    def part(pid,mpn,qty,package,role,rail=None,allowed=None,status="candidate",blocker="Footprint, sourcing and circuit qualification pending"):
        p={"id":pid,"mpn":mpn,"qty":qty,"package":package,"role":role,"status":status,"unresolved":blocker}
        if rail:p["rail"]=rail
        if allowed:p["allowed_supply_v"]=allowed
        d["components"].append(p)
        d["required_parts"].append({"id":pid,"minimum_qty":qty})
    for row in [
        ("fpga","T20F256C4",1,"FBGA25613x13mm0.8mm","timing reference","CORE_1V2",[1.15,1.25]),
        ("esp","ESP32-S3-WROOM-1-N8",1,"WROOM module PCB antenna","service helper","ESP_3V3",[3.0,3.6]),
        ("tx","AM26C31IPWR",3,"TSSOP16 PW","12differential drivers","CORE_5V",[4.5,5.5]),
        ("rx","AM26LV32EIPWR",2,"TSSOP16 PW","6of8receiver channels","IO_3V3",[3.0,3.6]),
        ("di","ISO1212DBQR",11,"SSOP16 DBQ","22isolated sinking inputs","IO_3V3",[2.25,5.5]),
        ("do","TPS4H160BQPWPRQ1",4,"HTSSOP28 PWP exposed pad","14of16sourcing outputs","FIELD_24V",[4,40]),
        ("iso_cmd","ISO7740FDBQR",4,"SSOP16 DBQ","16forward channels;14used","IO_3V3",[2.25,5.5]),
        ("iso_fault","ISO7740FDBQR",1,"SSOP16 DBQ","4reverse-oriented bank fault channels","FIELD_5V",[2.25,5.5]),
        ("iso_analog","ISO7740FDBQR",1,"SSOP16 DBQ","DACCLK/DIN/CS plus inhibit","IO_3V3",[2.25,5.5]),
        ("dac","DAC80501ZDQFR",1,"WSON8 DQF","16bit zero-scale reset candidate;internal2.5Vref gain1 (0-2.5V full scale) so output stays>=2.35V below ANALOG_5V minimum","ANALOG_5V",[2.7,5.5]),
        ("amp","OPA197IDBVR",1,"SOT23-5 DBV","gain-four analog candidate (0-2.5V DAC to 0-10V);>=1.4V headroom at 11.4V rail minimum","ANALOG_12V",[4.5,36]),
        ("analog_iso_power","TMR 1-2412",1,"SIP8","isolated12V83mA reference","CORE_24V",[18,36]),
        ("analog_ldo","TLV76050DBZR",1,"SOT23-3 DBZ","analog5V only","ANALOG_12V",[7,30]),
        ("buck_fpga_core","TPS62160DSGR",1,"WSON8 DSG","1.2V core;inductor/passives required","CORE_5V",[3,17]),
        ("buck_io","TPS62160DSGR",1,"WSON8 DSG","3.3V I/O;sequenced","CORE_5V",[3,17]),
        ("buck_esp","TPS62160DSGR",1,"WSON8 DSG","3.3V separately current-limited ESP branch","CORE_5V",[3,17]),
        ("watchdog","TPS3431SDRBR",1,"VSON8 DRB","independent timeout","IO_3V3",[1.8,6.5]),
        ("input_tvs","SMF36A",22,"SOD123F","historical costing provision;final surge coordination open",None,None),
        ("terminals","TBP01R1-508-08BE",12,"8way5.08mm THT","96positions placeholder allocation, dimensions/current review open",None,None),
        ("mating_plugs","TBP01P1-508-08BE",12,"8way5.08mm screw plug","96mating positions, shipped loose",None,None)
    ]:part(*row)
    known_support=[
        ("tx_series",12,"0603","33ohm1% initial source damping"),("tx_data_pulldown",12,"0603","10kohm1% at driver inputs"),
        ("tx_permit_pulldown",3,"0603","10kohm1% at each driver G"),("tx_decoupling",3,"0603","100nF25V X7R at VCC/GND"),
        ("tx_bulk",3,"0603","1uF25V X7R at each driver;bias derating"),
        ("di_rsense",22,"0603_or_larger","562ohm1% per input"),("di_rthreshold",22,"MELF>=0.25W","1kohm1% pulse-rated threshold resistor"),
        ("di_filter",22,"0603_or_larger","CIN value/rating TBD;fast probe channels qualified separately"),
        ("di_decoupling",11,"0603","100nF25V X7R per ISO1212"),
        ("do_pulldown",16,"0603","10kohm candidate all16IN pins inclunused"),
        ("do_current_set",4,"0603","perbank current limit from tolerance/thermal design;value TBD"),
        ("do_diag_support",4,"TBD","current-sense/diagnostic pull/filter network incl CS/CL/SEL1/SEL2/DIAG_EN/LATCH/FLT;not just floating pins"),
        ("rx_termination",6,">=0.125W","120ohm1% selectable at receiver;not blindly at both cable ends"),
        ("iso_decoupling",12,"0603","one100nF at each supply side of6isolators"),
        ("local_buck_inductor",3,"TBD","3inductors selected from ripple/saturation/EMI calculation"),
        ("local_buck_caps_feedback",3,"TBD","3sets Cin/Cout/feedback/enable/PG support sized fromdatasheet"),
        ("analog_gain",2,"0603","matched30k/10k0.1% gain-four provisional;reference accuracy plus temp drift open"),
        ("analog_support",1,"TBD","DACreferencecaps/resetstraps;opampbypass/outputisolation/filter/monitor/clamp"),
        ("watchdog_timing",1,"TBD","capacitor/straps and WDO pull-up;20msstudy needs tolerance budget"),
        ("fpga_decoupling",1,"TBD","perpin railcaps/bulk/filter network derived frompackage/reference schematic"),
        ("esp_decoupling_boot",1,"TBD","bulk/bypass/EN/GPIO0 boot/networkantenna clearance"),
        ("tx_rx_line_protection",18,"TBD","12TX+6RX channel networks;capacitance/commonmode/ESD energy TBD")
    ]
    for pid,qty,pkg,role in known_support:part(pid,None,qty,pkg,role,status="required_unselected")
    for pid,role,qty in [
        ("core_24_protection","Core entry TVS/EMI support beyond separately listed fuse/eFuse subassemblies; no 24 V directly into TPS62160",1),
        ("main_5v_converter","18-30V to5V6A regulated stage withPGOOD",1),
        ("field_24_protection","Field entry TVS/EMI distribution and bank protection beyond separately listed fuse/eFuse subassemblies",1),
        ("field_5v_converter","18-30V to5V100mA switching stage",1),
        ("permission_logic","hardwareAND/latch;allpermissives required;14outputANDgates;spindlerun included",1),
        ("power_supervisor","railsupervision/sequenceT20/reset;CPUbootisnotPGOOD",1),
        ("fpga_flash","externalserialNOR compatible with T20bootvoltage/commands/capacity;programmedimage",1),
        ("fpga_clock","50MHz3.3VCMOSoscillator with tolerance/jitter/dutycycle budget",1),
        ("fpga_jtag","programmingconnector,strapresistors,recoverybutton andtestpoints",1),
        ("host_spi_buffer","offstateisolation/source damping forSBC-FPGA partialpower;OEdefaultoff",1),
        ("esp_uart_buffer","Ioff-qualified buffer/isolation for3.3VUARTand2statusinputs",1),
        ("esp_branch_limit","local branchcurrentlimit;ESPshortcannotcollapseFPGA railwithinbudget",1),
        ("encoder_load_switch","independent5V200mA currentlimited encoderports;reverse protection",2),
        ("analog_zero_clamp","defaultdeenergizedzero output independentofDACcode;loadaccuracy retained",1),
        ("usb_recovery","USB-Cdata/protection/CC/powerrole/backfeed design;noautomaticmachinepower",1),
        ("expansion","namedkeyedinterface/power/timingclass;unselected,notadvertisedaxisexpansion",1)
    ]:part(pid,None,qty,"TBD",role,status="required_unselected")
    part("physical_entry_fuse_core",None,1,"TBD","F_CORE: DC-rated physical fuse plus holder; interrupt/time-current/I2t coordination unresolved",status="required_unselected")
    part("physical_entry_fuse_field",None,1,"TBD","F_FIELD: separately coordinated DC physical fuse plus holder",status="required_unselected")
    part("efuse_core",None,1,"TBD","TPS2663 family candidate plus external reverse FET and sense/timing/strap components; core threshold unresolved",status="required_unselected")
    part("efuse_field",None,1,"TBD","TPS2663 family candidate; latch-off; external reverse FET; current margin and connector coordination unresolved",status="required_unselected")
    for pid,rail,limits in [
        ("fpga","IO_3V3",[3.14,3.47]),
        ("iso_cmd","FIELD_5V",[2.25,5.5]),
        ("iso_fault","IO_3V3",[2.25,5.5]),
        ("iso_analog","ANALOG_5V",[2.25,5.5])
    ]:
        next(p for p in d["components"] if p["id"]==pid).setdefault("supply_ports",[]).append({"rail":rail,"allowed_supply_v":limits})
    # Logical channel allocations: exact IC channel, but no unreviewed BGA balls/GPIO numbers.
    def channel(cid,kind,component,unit,logic_net,domain,default,load=0):
        d["channels"].append({"id":cid,"kind":kind,"component":component,"device_channel":unit,"logic_net":logic_net,
            "domain":domain,"default":default,"load_target_a":load,"fpga_package_pin":None,"bank":None})
    for j in range(6):
        for k,fn in enumerate(("STEP","DIR")):
            n=j*2+k
            channel(f"{fn}{j}","step_dir",f"TX{n//4}",n%4+1,f"{fn}{j}_FPGA","LOGIC","low_input_high_Z_output_when_inhibited")
    for enc in range(2):
        for k,fn in enumerate("ABZ"):
            n=enc*3+k;channel(f"ENC{enc}_{fn}","encoder",f"RX{n//4}",n%4+1,f"ENC{enc}_{fn}_FPGA","LOGIC","invalid_until_initialized")
    names=["HOME0","HOME1","HOME2","HOME3","HOME4","HOME5","PROBE","TOOLSETTER","DOOR_STATUS","PROTECTIVE_STATUS","SPINDLE_FAULT","SPINDLE_READY","FEED_HOLD","CYCLE_START","LUBE_STATUS","SPARE"]+[f"ALM{i}" for i in range(6)]
    for i,name in enumerate(names):channel(f"DI{i:02d}","digital_input",f"DI{i//2}",i%2+1,name+"_FPGA","FIELD","read_only")
    names=["SPINDLE_RUN","SPINDLE_DIRECTION","FLOOD","MIST","LUBRICATION","AIR","SPARE0","SPARE1"]+[f"ENABLE{i}" for i in range(6)]
    for i,name in enumerate(names):channel(f"DO{i:02d}","general_output" if i<8 else "drive_enable",f"DO{i//4}",i%4+1,name+"_CMD","FIELD","off",0.5 if i<8 else 0.05)
    channel("AO0","spindle_analog","DAC0",1,"SPINDLE_ANALOG_COMMAND","ANALOG","zero_request_and_separate_run_off")
    # Core signal use:54direct signals plus30support/reservedGPIO =84; configuration needs separate review.
    reserve=[("host_spi",4,"runtimeCS/SCLK/MOSI/MISO"),("analog_spi",4,"DACCS/SCLK/DIN/analogpermit"),
             ("output_faults",4,"oneaggregatefaultperTPS4H160bank"),("motion_permission",1,"FPGAarmrequest"),
             ("external_inhibit",1,"asynchronousassertion/synchronizedrelease"),("watchdog_progress",1,"usefulprogressWDI"),
             ("motion_disarmed",1,"read-only ESP status"),("fault_status",4,"watchdog/link/inhibit/timing fault"),
             ("endpoint_ready",1,"endpoint initialized, not useful progress"),
             ("reference_clock",1,"50MHzdedicatedclock-capableinput"),("logic_reset",1,"resetn"),
             ("power_status",1,"PGOODaggregate"),("future_expansion",6,"reserveduncommitted;notasupportedinterface")]
    d["pin_reservations"]=[{"id":a,"count":b,"purpose":c,"package_pins":None} for a,b,c in reserve]
    d["physical_reserved_functions"]=["JTAG4", "activeconfigurationSPI4plusstraps", "CRESET_N", "CDONE", "power/groundallballs"]
    # Public terminal proposal retains the12x8 costing positions. Pin labels are connector allocation only, not footprint approval.
    terminals=[]
    def conn(name,nets,domain):
        for i,net in enumerate(nets,1):terminals.append({"connector":name,"position":i,"net":net,"domain":domain,"physical_footprint_approved":False})
    for b in range(3):conn(f"JTX{b}",[f"{fn}{j}_{pol}" for j in range(b*2,b*2+2) for fn in ("STEP","DIR") for pol in ("P","N")],"LOGIC")
    for b in range(2):conn(f"JENC{b}",[f"ENC{b}_{sig}_{pol}" for sig in "ABZ" for pol in ("P","N")]+[f"ENC{b}_5V_LIMITED","LOGIC_GND"],"LOGIC")
    for b in range(3):
        nets=[f"DI{i:02d}_FIELD" for i in range(b*8,min(b*8+8,22))]
        conn(f"JDI{b}",nets+["FIELD_GND"]*(8-len(nets)),"FIELD")
    for b in range(2):
        nets=[f"DO{i:02d}_FIELD" for i in range(b*8,min(b*8+8,14))]
        conn(f"JDO{b}",nets+["FIELD_GND"]*(8-len(nets)),"FIELD")
    conn("JPOWER",["CORE_24V","LOGIC_GND","FIELD_24V","FIELD_GND","TX0_REFERENCE","TX1_REFERENCE","TX2_REFERENCE","CHASSIS_PE"],"MIXED_DOCUMENTED")
    conn("JANA",["SPINDLE_0_10V","ANALOG_GND"]+[f"NC_RESERVED_{i}" for i in range(6)],"ANALOG")
    d["terminals"]=terminals
    d["connector_warning"]="JPOWER mixes separately labelled supplies/reference domains; layout/keying review may split connectors and change pricedMPNs. TX*_REFERENCE bond to LOGIC_GND only. SixreservedJANApositions are physicallyNC; never arbitraryvoltage inputs."
    core5v_total = sum(x["budget_a"] for x in d["power_loads"] if x["rail"] == "CORE_5V")
    core24_min_v = next(r for r in d["rails"] if r["id"] == "CORE_24V")["min_v"]
    logic_in = next(x for x in d["power_loads"] if x["id"] == "logic_converter_input")
    raw = core5v_total * 5 / 0.85 / core24_min_v
    logic_in["budget_a"] = round(_round_up(raw), 2)
    logic_in["basis"] = f"{core5v_total:.2f}A*5V/0.85/{core24_min_v:g}V={raw:.4f}A at minimum input, rounded up to 10mA"
    return d


def main():
    OUT.mkdir(exist_ok=True)
    d=build();(OUT/"electrical-design.json").write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    for name,key,fields in [("bom-snapshot.csv","components",["id","mpn","qty","package","role","status","rail","unresolved"]),
                            ("channel-map.csv","channels",["id","kind","component","device_channel","logic_net","domain","default","fpga_package_pin","bank"]),
                            ("terminal-map.csv","terminals",["connector","position","net","domain","physical_footprint_approved"]),
                            ("power-budget.csv","power_loads",["id","rail","budget_a","basis"])]:
        with (OUT/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(d[key])
    print(f"Generated {len(d['channels'])} channels, {len(d['components'])} BOM groups, {len(d['terminals'])} terminal positions")


if __name__=="__main__":main()
