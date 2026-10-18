from pathlib import Path
import hashlib,json,math
H=Path(__file__).resolve().parent;R=H.parents[2]
files=[R/'reports/board-finish-20261011/stitch-margin-audit/guard-v2/final2-filtered-plan.json',
       Path('Z:/pcb-runs/claude-finish/agent-work/via-dogbone-proof-r3/v1-stitch/plan3.json'),
       Path('Z:/pcb-runs/claude-finish/agent-work/via-dogbone-proof-r3/stitch/plan3.json'),
       Path('Z:/pcb-runs/claude-finish/route-s3/stitch-work/plan.json')]
strict=H/'paired-returns-r1/receipt.json';diagnostic=H/'paired-returns-prospective-antipads-r1/receipt.json';control=H/'paired-returns-controls-guard-0/receipt.json'
targets=[r['target'] for r in json.loads(strict.read_text())['results'][::2]]
saved=[]
for f in files:
    if not f.is_file():continue
    p=json.loads(f.read_text()); plan=p['plan']; lg=[r for r in plan if r['net'].replace('{slash}','/')=='/LOGIC_GND']
    saved.append({'file':str(f),'SHA256':hashlib.sha256(f.read_bytes()).hexdigest(),'saved_targets':p.get('targets'),'proposal_count':len(plan),'LG_proposals':len(lg),
                  'nearest_to_signal':[{**t,'nearest_any_saved_via_mm':min(math.dist(t['at_mm'],r['via']) for r in plan),
                                       'nearest_LG_saved_via_mm':min((math.dist(t['at_mm'],r['via']) for r in lg),default=None)} for t in targets],
                  'historical_pass_not_reused':True})
rr=json.loads(control.read_text())
out={'status':'BOUNDED_RETURN_SEARCH_NO_COMPLETED_THREE_RETURN_PACKET','saved_coordinate_search':saved,
     'strict_current_actual_foreign_fills_hard_sites':0,
     'zero_discretionary_guard_controls':[{'target':r['target'],'via_diameter_mm':r['via_diameter_mm'],'prospective_antipad_center_region_mm2':r['exact_center_region']['area_mm2'],
                                        'full_disc_actual_J1_In1_In4_support_mm2':r['full_disc_actual_J1_In1_In4_support_center_region']['area_mm2'],
                                        'design_clearance_passing_diagnostic_sites':r['passing_unique_centers'],'all_segments_alone_remaining_region_mm2':r['per_class_remaining_region_mm2'].get('segment')} for r in rr['results']],
     'scope_limit':'All negative results are for the conservative polygonal 0.9<=d<1mm bands and the stated via sizes/guards, not global impossibility. Prospective foreign-plane antipads and zero planning margin are diagnostic only and require independent source/reference/old-contact audit and full native AFTER.',
     'input_SHA256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (strict,diagnostic,control,Path(__file__))},'PCB_written':False,'adopted':False}
(H/'paired-return-boundary-summary.json').write_text(json.dumps(out,indent=1)+'\n')
print(json.dumps({'saved_plans_checked':len(saved),'strict_sites':0,'three_return_packet':False}))
