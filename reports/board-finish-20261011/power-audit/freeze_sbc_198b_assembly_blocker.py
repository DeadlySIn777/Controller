"""Freeze exact old/new ordinary SMD drill/mask/paste blockage; no CAD mutation."""
import hashlib,json,math,re,sys
from pathlib import Path
from shapely.geometry import Point,box
from shapely.ops import unary_union
import screen_sbc_198b_corridors as S
p,A,C,live=S.p,S.A,S.C,S.live
DEST=S.OUT/'C15001-assembly-blocker.json'
PRO=live.REPORT/'measure/r07-four-fag-shared/copy/board.kicad_pro'
DRU=PRO.with_suffix('.kicad_dru')
DEFAULT=S.OUT/'board_design_settings-10.0.4.h'
CPP=p.HERE/'project-binding-source/board_design_settings.cpp'
def nominal_aperture(center):
    x,y=center
    # Serialized1x1.45mm roundrect,90degrees absolute pad angle,ratio.25.
    # Exact dimensions produce the observed global1.45x1mm native pad bbox.
    return box(x-.725+.25,y-.5+.25,x+.725-.25,y+.5-.25).buffer(.25,quad_segs=256)
def main():
    p.require(not DEST.exists(),'new immutable receipt required')
    prior=json.loads(p.read(S.INPUT));p.require(prior['board_sha256']==live.SHA,'wrong native source')
    for path,sha in prior['read_set_sha256'].items():p.require(hashlib.sha256(p.read(path)).hexdigest()==sha,'packing source changed')
    board=p.read(live.COMBINED);native=p.base.inventory(board);fp=native[3][prior['old_components']['C15001']['uuid']]
    nodes=p.base.children(fp)[1];pad=next(n for n in nodes if p.base.kind(n)==b'pad' and n.startswith(b'(pad "2"'))
    p.require(b'(layers "F.Cu" "F.Mask" "F.Paste")' in pad and b'(size 1 1.45)' in pad and b'(roundrect_rratio 0.25)' in pad,'SMD aperture definition differs')
    p.require(not any(flag in fp for flag in (b'solder_paste_margin',b'solder_paste_margin_ratio',b'solder_mask_margin',b'padstack')),'unmodeled local aperture override')
    setup=next(ch for ch in native[5] if p.base.pcbtext.chunk_kind(ch)=='setup')
    p.require(b'(pad_to_mask_clearance 0)' in setup and b'(filling no)' in setup and b'(capping no)' in setup,'source setup differs')
    p.require(not any(flag in setup for flag in (b'pad_to_paste_clearance',b'pad_to_paste_clearance_ratio')),'unmodeled global paste override')
    rules=p.read(DRU);p.require(not any(flag in rules.lower() for flag in (b'solder_mask',b'solder_paste')),'unmodeled custom aperture rule')
    project=json.loads(p.read(PRO));project_rules=project['board']['design_settings']['rules']
    p.require(not any(k in project_rules for k in ('solder_paste_clearance','solder_paste_margin_ratio','solder_mask_clearance')),'project aperture override differs')
    defaults=p.read(DEFAULT).decode();cpp=p.read(CPP).decode()
    p.require(all(re.search(r'#define\s+'+name+r'\s+0\.0',defaults) for name in ('DEFAULT_SOLDERPASTE_CLEARANCE','DEFAULT_SOLDERPASTE_RATIO')),'official default paste constants differ')
    p.require('m_SolderPasteMargin = pcbIUScale.mmToIU( DEFAULT_SOLDERPASTE_CLEARANCE )' in cpp and 'm_SolderPasteMarginRatio = DEFAULT_SOLDERPASTE_RATIO' in cpp,'official source initialization differs')
    vg=native[3][C.GROUND_VIA]
    p.require(not any(flag in vg for flag in (b'filling',b'capping',b'plugging',b'covering')),'unmodeled via process override')
    g=json.loads(p.read(p.base.GEOM));oldpad=next(r for r in g['pads'] if r['ref']=='C15001' and r['num']=='2')
    old=oldpad['x'],oldpad['y'];new=old[0]+prior['deltas_mm']['C15001'][0],old[1]+prior['deltas_mm']['C15001'][1]
    via=next(v for v in g['vias'] if v['uuid']==C.GROUND_VIA)
    drill=Point(via['x'],via['y']).buffer(via['drill']/2,quad_segs=256)
    annulus=Point(via['x'],via['y']).buffer(via['d']/2,quad_segs=256)
    rows=[]
    for label,center in (('old',old),('proposed',new)):
        aperture=nominal_aperture(center)
        rows.append({'pose':label,'pad_center_mm':center,'copper_pad_area_mm2':aperture.area,
            'drill_overlap_copper_mm2':aperture.intersection(drill).area,
            'drill_overlap_F_Mask_aperture_mm2':aperture.intersection(drill).area,
            'drill_overlap_F_Paste_aperture_mm2':aperture.intersection(drill).area,
            'annulus_overlap_copper_mm2':aperture.intersection(annulus).area,
            'annulus_overlap_F_Mask_aperture_mm2':aperture.intersection(annulus).area,
            'annulus_overlap_F_Paste_aperture_mm2':aperture.intersection(annulus).area})
    p.read(Path(__file__));p.read(sys.executable)
    for path,sha in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,'source changed')
    result={'schema':'exact198b-C15001-ordinary-SMD-hole-mask-paste-blocker-v1','verdict':'WITHHELD_SMD_DRILL_PASTE_MASK_COLLISION',
        'board_sha256':live.SHA,'parent_packing_receipt_sha256':hashlib.sha256(S.INPUT.read_bytes()).hexdigest(),
        'pad_uuid':oldpad['uuid'],'footprint_sha256':hashlib.sha256(fp).hexdigest(),'via_uuid':C.GROUND_VIA,'via_sha256':hashlib.sha256(vg).hexdigest(),
        'via_center_mm':[via['x'],via['y']],'via_copper_drill_mm':[via['d'],via['drill']],
        'nominal_serialized_aperture_model':{'pad_mm':[1.,1.45],'absolute_angle_deg':90,'roundrect_ratio':.25,'mask_expansion_mm':0.,
            'paste_absolute_margin_mm':0.,'paste_ratio':0.,'circle_quadrant_segments':256,'exported_native_mask_paste_verified':False,
            'scope':'source-derived nominal aperture area, not native Gerber/aperture or fabrication measurement; native copper sampled metrics remain in separate receipt'},
        'old_and_proposed_aperture_drill_annulus_overlaps':rows,'board_default_filling':False,'board_default_capping':False,
        'vippo_waiver_or_new_mask_waiver':False,'old_native_ordinary_DRC_does_not_qualify_new_drill_SMD_land':True,
        'bounded_pose_action':'reject this exact +.85mmY C15001 pose; source proposal remains withheld, no composer/candidate',
        'conditional_minimum_horizontal_escape_mm':.725+.15+.25+.025-abs(old[0]-via['x']),
        'conditional_escape_scope':'at this Y and retainedvia, a pure Xshift needs approximately1.148mm to satisfy the conservative.275mm drill-to-pad edge rule; untestedalternative, no ownership expansion/placement/current acceptance',
        'decoupler_return_and_complete_4p15A_network_qualified':False,'no_native_or_GPU_jobs':True,'no_board_or_source_mutation':True,
        'source_files_sha256_before':p.READS,'source_files_sha256_after':{path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in p.READS}}
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(DEST),'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'aperture_rows':rows}))
if __name__=='__main__':main()
