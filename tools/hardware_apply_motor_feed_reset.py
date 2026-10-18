"""Bounded receiving-feed POR/CLR conditioning on copied native source only.
No original child or parent is rewritten by apply_feed_reset(). Final direct
TX permission contacts, watchdogs, rearm sources and bank separation persist.
"""
from __future__ import annotations
import copy,math,uuid
from hardware_build_assembly import parse,child,children,value,q,point,ref_property
from hardware_apply_motherboard_io3_upgrade import exact_label,symbol_for
from hardware_build_tx_schematic import symbol,effects
NS=uuid.UUID("47f339a2-c7e7-596d-8985-40bfc5bf129a")
uid=lambda s:str(uuid.uuid5(NS,s))
ID="MB-MOTOR-FEED-POR-001"
BLOCK="motherboard_power_entry"
REFS={"A":dict(latch="U11032",source="R11074",supervisor="U11035",buffer="U11036",caps=("C11089","C11090"),pd="R11082"),"B":dict(latch="U11034",source="R11078",supervisor="U11037",buffer="U11038",caps=("C11091","C11092"),pd="R11083")}
PINS={"FEED_POR":{1:("RESET_N","open_collector"),2:("GND","power_in"),3:("MR_N","input"),4:("CT","input"),5:("SENSE","input"),6:("VDD","power_in")},"FEED_SCHMITT":{1:("NC","no_connect"),2:("A","input"),3:("GND","power_in"),4:("Y","output"),5:("VCC","power_in")},"FEED_CAP":{1:("","passive"),2:("","passive")},"FEED_PD":{1:("","passive"),2:("","passive")}}

def footprint_text(count):
 """TI DBV0005A/0006A exact manufacturer example lands, not IPC alternates."""
 if count not in (5,6):raise ValueError("Only reviewed five/six-pin DBV lands")
 positions={1:(-1.3,-.95),2:(-1.3,0),3:(-1.3,.95)}
 positions.update({4:(1.3,.95),5:(1.3,-.95)} if count==5 else {4:(1.3,.95),5:(1.3,0),6:(1.3,-.95)})
 pads=''.join(f'(pad "{n}" smd roundrect(at {x} {y})(size 1.1 .6)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .0833333333))'for n,(x,y)in positions.items())
 return f'(footprint "TI_DBV{count}"(version 20241229)(generator "manufacturer_land_contract")(layer "F.Cu")(descr "TI DBV000{count}A manufacturer example land; 1.1x0.6 pads at x+/-1.30; 0.95 pitch")(attr smd)(property "Reference" "REF**"(at 0 -2.3 0)(layer "F.SilkS")(effects(font(size .8 .8)(thickness .12))))(property "Value" "TI_DBV{count}"(at 0 2.3 0)(layer "F.Fab")(effects(font(size .8 .8)(thickness .12))))(fp_rect(start -.875 -1.525)(end .875 1.525)(stroke(width .1)(type default))(fill none)(layer "F.Fab"))(fp_line(start -.875 -1.05)(end -.40 -1.525)(stroke(width .1)(type default))(layer "F.Fab"))(fp_rect(start -2.10 -1.80)(end 2.10 1.80)(stroke(width .05)(type default))(fill none)(layer "F.CrtYd")){pads})\n'

def added_components():
 p={}
 for bank,r in REFS.items():
  slow="MOTOR_FEED_CLEAR_N_"+bank;fast="MOTOR_FEED_CLEAR_FAST_N_"+bank
  p[r["supervisor"]]=dict(kind="FEED_POR",mpn="TPS3808G50DBVR",value="TPS3808G50DBVR",footprint="CNC_MB_FeedReset:TI_DBV6",physical=True,pins={"1":slow,"2":"LOGIC_GND","3":"MOTION_5V_RAW","4":None,"5":"MOTION_5V_RAW","6":"MOTION_5V_RAW"},role="independent receiving-RAW4.65V supervisor; CT intentionally open; published12..28ms release under manufacturer test load, actual loaded release needs qualification, activeLOW reset sink on original contact/RC node")
  p[r["buffer"]]=dict(kind="FEED_SCHMITT",mpn="SN74LVC1G17DBVR",value="SN74LVC1G17DBVR",footprint="CNC_MB_FeedReset:TI_DBV5",physical=True,pins={"1":None,"2":slow,"3":"LOGIC_GND","4":fast,"5":"MOTION_5V_RAW"},role="genuine unlimited-slew noninverting Schmitt; RC/supervisor LOW to fast DFF CLR without shared A/B nodes")
  for ref,owner in zip(r["caps"],(r["supervisor"],r["buffer"])):
   p[ref]=dict(kind="FEED_CAP",mpn="GRM188R72A104KA35D",value="100nF100V X7R",footprint="Capacitor_SMD:C_0603_1608Metric",physical=True,pins={"1":"MOTION_5V_RAW","2":"LOGIC_GND"},role="exact local RAW bypass for "+owner,owner=owner,initial_tolerance=.1,rated_voltage_v=100)
  p[r["pd"]]=dict(kind="FEED_PD",mpn="CRCW0603100KFKEA",value="100k 1%",footprint="Resistor_SMD:R_0603_1608Metric",physical=True,pins={"1":fast,"2":"LOGIC_GND"},resistance_ohm=100000,initial_tolerance=.01,tcr_ppm=100,rated_power_w=.1,working_voltage_v=75,role="actual DFF CLR LOW default if conditioner is missing/high-Z")
 for ref,row in p.items():row.update(source_block=BLOCK,source_reference=ref,selection_required=False,status="source_candidate_not_physical_qualified")
 return p

def apply_feed_reset(trees,model):
 t,m=copy.deepcopy(trees),copy.deepcopy(model);tree=t[BLOCK];parts=m["components"];extra=added_components()
 if set(extra)&set(parts):raise ValueError("Feed reset refs already fitted/collision")
 ledger=[]
 for bank,r in REFS.items():
  latch=parts[r["latch"]];source=parts[r["source"]];slow="MOTOR_FEED_CLEAR_N_"+bank;fast="MOTOR_FEED_CLEAR_FAST_N_"+bank
  expected={"1":"MOTOR_FEED_REARM_"+bank,"2":"MOTION_5V_RAW","3":None,"4":"LOGIC_GND","5":"MOTOR_FEED_ON_"+bank,"6":slow,"7":"MOTION_5V_RAW","8":"MOTION_5V_RAW"}
  if latch.get("mpn")!="SN74LVC1G74DCUR"or latch.get("footprint")!="Package_SO:VSSOP-8_2.3x2mm_P0.5mm"or latch.get("pins")!=expected:raise ValueError("Unreviewed receiving DFF "+bank)
  if source.get("mpn")!="CRCW06031K00FKEA"or source.get("pins")!={"1":"MOTION_5V_RAW","2":"MOTOR_FEED_CLEAR_SOURCE_"+bank}:raise ValueError("Unreviewed clear source "+bank)
  exact_label(tree,r["latch"],"6",slow)[1]=q(fast);latch["pins"]["6"]=fast
  source.update(mpn="CRCW060312K1FKEA",value="12.1k 1%",resistance_ohm=12100,inherited_mpn="CRCW06031K00FKEA",component_substitution=ID)
  for prop in children(symbol_for(tree,r["source"]),"property"):
   if value(prop[1])=="MPN":prop[2]=q(source["mpn"])
   if value(prop[1])=="Value":prop[2]=q(source["value"])
  ledger.append(dict(bank=bank,latch_reference=r["latch"],pin="6",old_net=slow,new_net=fast,source_reference=r["source"],old_mpn="CRCW06031K00FKEA",new_mpn="CRCW060312K1FKEA",all_other_existing_pin_nets_preserved=True))
 # Native library geometry has the actual manufacturer pin contract. No power
 # flags are invented: every new power input joins existing RAW/return sources.
 geometry={};lib=child(tree,"lib_symbols")
 for kind,pinmap in PINS.items():
  if kind in["FEED_CAP","FEED_PD"]:
   coords=[(1,"",0,5.08,270,"passive"),(2,"",0,-5.08,90,"passive")];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
  else:
   keys=list(pinmap);left=keys[:(len(keys)+1)//2];right=keys[len(left):];half=max(len(left),len(right))*5.08;coords=[]
   for side,keys in[(-1,left),(1,right)]:
    for i,n in enumerate(keys):coords.append((n,pinmap[n][0],side*20.32,half-i*10.16,0 if side<0 else 180,pinmap[n][1]))
   body=f'(rectangle(start -17.78 {half+5.08})(end 17.78 {-half+5.08})(stroke(width .254)(type default))(fill(type background)))'
  geometry[kind]=coords;definition=parse(symbol(kind,coords,body,"C"if kind=="FEED_CAP"else"R"if kind=="FEED_PD"else"U"));definition[1]=q("CNC_MB_FeedReset:"+kind);lib.append(definition)
 template=symbol_for(tree,"U11032");instances=copy.deepcopy(child(template,"instances"));base_y=max(float(child(s,"at")[2])for s in children(tree,"symbol"))+152.4
 for i,(ref,row)in enumerate(extra.items()):
  x=177.8+(i%4)*266.7;y=base_y+(i//4)*167.64;kind=row["kind"];coords=geometry[kind]
  props=''.join(f'(property {q(k)} {q(v)}(at {x} {y-45.72+j*5.08} 0){effects(.8, "hide"if k in["MPN","Footprint"]else"")})'for j,(k,v)in enumerate([("Reference",ref),("Value",row["value"]),("MPN",row["mpn"]),("Footprint",row["footprint"])]))
  sym=parse(f'(symbol(lib_id {q("CNC_MB_FeedReset:"+kind)})(at {x} {y} 0)(unit 1)(in_bom yes)(on_board yes)(dnp no)(uuid {q(uid(ref))}){props})');inst=copy.deepcopy(instances)
  for pr in children(inst,"project"):
   for path in children(pr,"path"):child(path,"reference")[1]=q(ref)
  sym.append(inst);tree.append(sym)
  for n,_,px,py,_,_ in coords:
   xx=round(x+px,4);yy=round(y-py,4);net=row["pins"][str(n)]
   if net is None:tree.append(parse(f'(no_connect(at {xx} {yy})(uuid {q(uid(ref+str(n)+"nc"))}))'));continue
   ex=round(xx+(-30.48 if px<0 else 10.16),4);ey=yy
   tree.append(parse(f'(wire(pts(xy {xx} {yy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid {q(uid(ref+str(n)+"wire"))}))'))
   tree.append(parse(f'(label {q(net)}(at {ex} {ey} 0){effects(.7,"(justify left bottom)")}(uuid {q(uid(ref+str(n)+"label"))}))'))
 parts.update(extra);m["physical_footprints"]+=len(extra);m["assembly_fitted_parts"]+=len(extra)
 receipt=dict(id=ID,exact_existing_pin_net_delta=ledger,exact_added_references=sorted(extra),exact_added_components=copy.deepcopy(extra),power_domains_unchanged=True,independent_final_TX_gate_watchdog_and_rearm_paths_unchanged=True,original_sources_unchanged=True,physical_qualification=False)
 m["motor_feed_reset_correction"]=receipt;return t,m,receipt

def feed_reset_screen(source_r=12100,drift=.025,pd=100000,cap=1e-9,raw_min=4.95,raw_max=5.05,off_leak=8e-6):
 # Published static endpoint and leakage conditions; intermediate voltage/ramp,
 # PCB loading, temperature and contact timing are not silently interpolated.
 rh=source_r*(1+drift)+6;rl=source_r*(1-drift);pl=pd*(1-drift);ph=pd*(1+drift);leak_on=6e-6
 high=(raw_min/rh-leak_on)/(1/rh+1/pl);off=off_leak*ph;threshold=1.51
 decay=ph*cap*1.05*math.log((raw_max-off)/(threshold-off)) if off<threshold else None
 return dict(healthy_old_CLR_node_screen_v=high,highest_schmitt_VTplus_discrete_screen_v=3.33,off_node_screen_v=off,lowest_steady_schmitt_VTminus_discrete_screen_v=threshold,source_min_ohm=rl,TPS3808_mandatory_min_pullup_ohm=10000,reset_sink_at_raw1V65_a=1.65/rl,reset_sink_at_raw5V25_a=5.25/rl,reset_VOL1V65_max_v=.3,schmitt_VTminus1V65_min_v=.35,startup_low_endpoint_margin_v=.05,fast_CLR_load_screen_a=5.5/(pd*(1-drift))+5e-6,fast_CLR_light_load_test_a=100e-6,fast_output_LOW_max_v=.1,fast_output_HIGH_min_offset_v=-.1,reset_nominal_threshold_v=4.65,reset_threshold_corner_v=[4.65*.985,4.65*1.015],reset_max_positive_release_threshold_screen_v=4.65*1.015+4.65*.025,reset_threshold_accuracy_for_G50_0_to_85C_fraction=.015,reset_release_delay_ms=[12,28],reset_release_test_conditions={"VDD_min_v":1.7,"RL_ohm":100000,"CL_f":50e-12},actual_RESET_node_load_different_from_timing_test=True,conditional_contact_RC_withdrawal_s=.0002+decay if decay is not None else None,conditioner_propagation_max_s_at_5V_85C=4.4e-9,minimum_input_slew_requirement_ns_per_v=5,fast_output_edge_measured_qualification=False,reset_low_hold_during_intermediate_rail_slew_qualification=False,all_existing_direct_final_inhibit_paths_unchanged=True,complete_partial_ramp_loaded_edge_and_thermal_qualification=False,contact25C_bound_not_promoted_to_full_temperature=True)
