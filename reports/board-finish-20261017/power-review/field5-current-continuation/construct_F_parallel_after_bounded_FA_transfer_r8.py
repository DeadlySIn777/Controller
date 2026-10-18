"""Test a .5mm F power path with exactly two FA signal retirements and one via.

The signal's all-layer new-hole, replacement route, return/reference and finite
old contact checks are separate and open. No route retirement is adopted here.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'probe_parallel_existing_barrel_corridors_r2.py'
s=SOURCE.read_text()
def replace(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("OUT=HERE/'parallel-fixed-native-copper-probe-r2'","OUT=HERE/'F-parallel-bounded-FA-transfer-probe-r8'")
replace('roi=box(268,138,316,184)','roi=box(250,120,350,210)')
replace("for layer,width in(('F.Cu',.5),('B.Cu',.35),('In2.Cu',.5),('In3.Cu',.5)):","for layer,width in(('F.Cu',.5),):\n        source_pad=next(p for p in g['pads']if(p['ref'],p['num'])==('L11003','2'));start=tuple(unary_union(K.L.poly(source_pad['layers'][layer])).centroid.coords)[0]")
replace("net=T.NET;domain=g['domains_normalized'][net]", "net=T.NET;domain=g['domains_normalized'][net];retired={'f231adb1-b5c9-422a-82eb-c6a859d26a93','21702822-e41c-488c-a23a-db6e3e94614d'};assert len([t for t in g['tracks']if t['uuid']in retired])==2;g=g|{'tracks':[t for t in g['tracks']if t['uuid']not in retired],'vias':g['vias']+[{'uuid':'8270a55c-2466-5791-a4e1-1597d37e5ab4','net':'/motherboard_power_entry/FA_SHDN_CONTACT','x':297.25,'y':155.65,'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']}]}")
replace("if K.L.norm(q['net'])==net:continue", "if K.L.norm(q['net'])==net or(q['kind']=='fill'and K.L.norm(q['net'])=='/motherboard_motors/FIELD_GND'):continue")
replace("gap=.15 if q['domain']==domain else.6", "if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None):body=body.buffer(.005,quad_segs=128)\n            if q['kind']=='track'and q['source'].get('m')is None:\n                t=q['source'];body=LineString([t['a'],t['b']]).buffer((t['w']/2+1e-8)/math.cos(math.pi/512),quad_segs=128)\n            gap=.15 if q['domain']==domain else.6")
replace("'fixed_native_foreign_copper':True", "'fixed_other_actual_native_Cu_except_FG_fills':True,'conditional_FA_two_track_transfer_and_one_via_NOT_yet_qualified':True,'actual_source_terminal':'L11003.2','actual_source_pad_center_mm':list(start)")
replace("'no_foreign_native_fill_cuts_proposed':True", "'only_explicit_FG_native_fill_cuts_allowed_and_still_open':True,'retired_FA_signal_tracks_are_not_approved_or_adopted':sorted(retired),'signal_all_layer_new_hole_SMD_return_reference_and_replacement_contact_checks':'OPEN; routing agent independent screen underway'")
replace("'roi_mm':[268,138,316,184]","'roi_mm':[250,120,350,210]")
exec(compile(s,str(SOURCE),'exec'),globals())
