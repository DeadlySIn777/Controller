"""Publish explicit non-readiness from current real, independently checked data."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(relative):
    return json.loads((HERE/relative).read_text())


def main():
    native = read('mc-integrated-r04/review.json')
    routing = read('mc-integrated-r04/fresh-native-routing-inventory/review.json')
    tests = read('post-r04-host-validation/receipt.json')
    cost = read('mc-bom-cost-r04/MC_BOM_COST.json')
    publication = json.loads((ROOT/'hardware/board_review/revisions/20260930-14/publication.json').read_text())
    full = next(r for r in tests['runs'] if r['name']=='full-suite')
    prototype = read('release-state-r04/prototype-release-check.json')
    production = read('release-state-r04/production-release-check.json')
    evidence_paths = (
        'READINESS.md','mc-integrated-r04/review.json',
        'mc-integrated-r04/fresh-native-routing-inventory/review.json',
        'post-r04-host-validation/receipt.json','mc-bom-cost-r04/MC_BOM_COST.json',
        'mc-bom-cost-r04/receipt.json','release-state-r04/prototype-release-check.json',
        'release-state-r04/production-release-check.json','viewer-rev14/board-view-context.jpg')
    result = {
        'schema_version':1,'date':'2026-09-30',
        'completion_target_achieved':False,'manufacturing_ready':False,
        'status':'incomplete_design_with_unresolved_physical_service_contract',
        'source_revision':'motion-card-r0.4-proposed-IS2','published_board_revision':'20260930-14',
        'scope':'Partial327-part motion card, not a complete CNC controller',
        'native_pcb_sha256':publication['native_pcb_sha256'],
        'parts':routing['footprints'],'fitted_pads':routing['fitted_pads'],
        'represented_native_nets':382,'source_assigned_footprints':327,
        'placement_only_candidates':0,'track_segments':643,'vias':30,'copper_zones':0,
        'fully_joined_multiple_pad_nets':routing['fully_joined_multiple_pad_nets'],
        'required_multiple_pad_nets':routing['nets_requiring_multiple_fitted_pads'],
        'incomplete_multiple_pad_nets':routing['incomplete_multiple_pad_nets'],
        'required_missing_physical_joins':routing['independent_physical_cluster_missing_joins'],
        'declared_source_nc_pads':routing['declared_native_NC_pads'],
        'orphan_copper_items':routing['orphan_copper_items'],
        'erc_violations':native['erc_violations'],'erc_ignored_checks':native['erc_ignored_checks'],
        'drc_regular_violations':native['drc_regular_violations'],
        'drc_ignored_checks':native['drc_ignored_checks'],
        'drc_capped_unconnected_items':native['drc_capped_unconnected_items'],'drc_pass':False,
        'layout_assumptions':{'outline_mm':[220,100],'copper_layers':6,'thickness_mm':1.6,
                              'final_manufacturing_stackup_approved':False},
        'manufacturing_package':{'gerbers':None,'drills':None,'fabrication_zip':None,
            'approved_bom':None,'assembly_cpl':None,'assembly_drawing':None,
            'final_stackup_and_rules':None,'factory_programming_bundle':None},
        'host_validation':{'reported':full['reported_tests'],'passed':full['passed_tests'],
            'skipped':full['skipped_tests'],'failures_or_errors':full['failure_or_error_lines'],
            'scoped_inputs':tests['source_file_count_before'],
            'unchanged_during_run':tests['source_hashes_unchanged'],
            'focused_cases_included_in_full_suite':True},
        'component_cost':{'currency':'USD','scope':'Partial MC only; purchased modules excluded',
            'summaries':cost['summaries'],'complete_controller_total_usd':None,
            'complete_manufactured_custom_board_total_usd':None},
        'purchased_modules':{'compute':None,'esp':None,'storage':None,'optional_ai':None,
            'display_packages':{'7inch':None,'10inch':None,'12inch':None,'14inch':None,'18inch':None,'21inch':None}},
        'decision_blocker':{
            'id':'D1','status':'awaiting_user_clarification',
            'conflict':'One custom PCB plus purchased modules vs frozen IS-1 passive base/custom service/expansion cards',
            'common_compute_bay_does_not_resolve_fpga_field_expansion_service_boundaries':True},
        'unfinished_engineering_is_not_physical_only':True,
        'unfinished_engineering_groups':['complete_circuits_and_field_IO','remaining_MC_boundaries',
            'compute_ESP_selector_storage_indicators','full_GPIO_bank_allocation_and_vendor_fit',
            'CNC3_IOL1_target_software','full_routing_planes_and_mechanics','final_manufacturing_package'],
        'physical_or_purchasing_groups':['motion_link_and_inhibit_measurement',
            'electrical_thermal_fault_EMC_environment_qualification',
            '72hour_combined_motor_encoder_and_service_trials',
            'qualified_compute_screen_storage_peripherals','exact_source_availability_and_PCBWay_quote'],
        'prototype_release_ready':prototype['ready'],'prototype_release_blocker_count':len(prototype['blockers']),
        'production_release_ready':production['ready'],'production_release_blocker_count':len(production['blockers']),
        'new_target_compilation':False,'new_hdl_simulation':False,'new_vendor_fit':False,
        'physical_interfaces_connected':False,'supplier_submission':False,'purchase_made':False,
        'evidence_sha256':{relative:hashlib.sha256((HERE/relative).read_bytes()).hexdigest() for relative in evidence_paths},
    }
    (HERE/'READINESS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'manufacturing_ready':False,'missing_joins':result['required_missing_physical_joins'],
        'reported_host_cases':full['reported_tests'],'prototype_blockers':len(prototype['blockers'])}))


if __name__ == '__main__':
    main()
