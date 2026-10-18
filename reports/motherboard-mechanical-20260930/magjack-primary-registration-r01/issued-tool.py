"""Report-only registration of exact manufacturer STEP to reviewed native land."""
import hashlib,json,re
from pathlib import Path
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID,TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.gp import gp_Pnt
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane

ROOT=Path(__file__).resolve().parents[1]
step=ROOT/'reports/motherboard-mechanical-20260930/primary-drawing-review/wurth-7499111446-manufacturer-rev1.stp'
footprint=ROOT/'hardware/motherboard_compute/CNC_COMPUTE.pretty/Wurth_7499111446_Gigabit.kicad_mod'
pdf=ROOT/'reports/motherboard-compute-20260930/sources/wurth-7499111446.pdf'
out=ROOT/'reports/motherboard-mechanical-20260930/magjack-primary-registration-r01'
if (out/'review.json').exists():raise SystemExit('Use a new immutable report directory')
out.mkdir(parents=True,exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def bounds(s):
    box=Bnd_Box();BRepBndLib.AddOptimal_s(s,box,False,False)
    return None if box.IsVoid() else list(box.Get())
reader=STEPControl_Reader();assert reader.ReadFile(str(step))==IFSelect_RetDone
reader.TransferRoots();shape=reader.OneShape();solids=[]
e=TopExp_Explorer(shape,TopAbs_SOLID)
while e.More():solids.append(TopoDS.Solid_s(e.Current()));e.Next()
slab=BRepPrimAPI_MakeBox(gp_Pnt(-50,-50,-9.9),100,100,.9).Shape()
tails=[]
for n,s in enumerate(solids,1):
    sec=BRepAlgoAPI_Common(s,slab).Shape();q=bounds(sec)
    if q and q[3]-q[0]<1.0 and q[4]-q[1]<1.0:
        tails.append({'solid_index_1based':n,'tail_slab_bbox_mm':q,'cad_center_mm':[(q[0]+q[3])/2,(q[1]+q[4])/2]})
native={n:(float(x),float(y))for n,x,y in re.findall(r'\(pad "(\d+)"[^\(]*\(at (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)',footprint.read_text())}
# Primary CAD registration is independently constrained by all ten signal lead
# tails, not the housing bounding box or a generic stock 3D model.
matches=[]
for n in range(1,11):
    want=native[str(n)]
    nearest=min(tails,key=lambda t:(t['cad_center_mm'][0]+5.71-want[0])**2+(9.065-t['cad_center_mm'][1]-want[1])**2)
    actual=[nearest['cad_center_mm'][0]+5.71,9.065-nearest['cad_center_mm'][1]]
    error=[actual[i]-want[i]for i in (0,1)]
    assert max(abs(v)for v in error)<.001, (n,want,actual,error,tails)
    matches.append({'pin':str(n),'native_land_center_mm':list(want),'manufacturer_tail':nearest,'registered_center_mm':actual,'delta_mm':error})
assert len({m['manufacturer_tail']['solid_index_1based']for m in matches})==10
bb=bounds(shape)
native_bb=[bb[0]+5.71,9.065-bb[4],bb[3]+5.71,9.065-bb[1]]
flats=[]
for n,s in enumerate(solids,1):
    fs=TopExp_Explorer(s,TopAbs_FACE)
    while fs.More():
        f=TopoDS.Face_s(fs.Current());surf=BRepAdaptor_Surface(f)
        if surf.GetType()==GeomAbs_Plane:
            pl=surf.Plane()
            if abs(pl.Axis().Direction().Z())>.999999:
                q=bounds(f)
                if q and abs(q[2]+7.1)<1e-5 and q[3]-q[0]>1 and q[4]-q[1]>1:
                    flats.append({'solid':n,'face_bbox_mm':q})
        fs.Next()
candidate=[274.4,321.7]
report={'manufacturer':'Wurth Elektronik','exact_MPN':'7499111446',
        'primary_STEP_URL':'https://www.we-online.com/components/products/download/7499111446%20%28rev1%29.stp',
        'primary_link_page':'https://www.we-online.com/en/components/icref/analog-devices/ADIN1300-EVAL-CN0506-FMCZ-Other',
        'source_hashes':{str(step.relative_to(ROOT)):sha(step),str(pdf.relative_to(ROOT)):sha(pdf),str(footprint.relative_to(ROOT)):sha(footprint)},
        'step_header':step.read_text(errors='replace')[:1000],
        'native_solid_count':len(solids),'manufacturer_STEP_all_metal_bbox_mm':bb,
        'native_XY_registration':{'x_native':'x_STEP + 5.71 mm','y_native':'9.065 mm - y_STEP','evidence':'Ten independent through-hole signal lead-tail sections at CAD Z=-9.9..-9.0 mm match exact reviewed native pin1..10 centres to <0.001 mm. The contact tail is .35 mm deep; its centre is .175 mm above its bbox minimum. Using minimum as centre incorrectly offsets the mouth by .175 mm.'},
        'ten_actual_signal_pin_matches':matches,
        'registered_all_metal_XY_bbox_mm':native_bb,'mating_mouth_local_plus_Y_mm':native_bb[3],
        'native_Fab_body_centerline_bbox_mm':[-2.225,-2.06,13.655,19.78],
        'manufacturer_PDF_body_dimensions_mm':[16,21.25,13.5],
        'all_metal_depth_mm':bb[4]-bb[1],'all_metal_width_including_springs_mm':bb[3]-bb[0],
        'candidate_position_mm':candidate,'candidate_registered_metal_XY_bbox_mm':[native_bb[0]+candidate[0],native_bb[1]+candidate[1],native_bb[2]+candidate[0],native_bb[3]+candidate[1]],
        'candidate_mouth_beyond_board_y340_mm':native_bb[3]+candidate[1]-340,
        'horizontal_faces_at_candidate_CAD_seating_plane_zminus7p1':flats,
        'seating_datum_note':'CAD Z=-7.1 mm has actual horizontal housing faces; the 13.5 mm rated housing top at +6.4 mm supports that seating interpretation. Manufacturer drawing/body datum and fitting remain authoritative, not a generic STEP origin.',
        'provisional_all_metal_top_clearance_mm':15.4,
        'seating_plane_relative_highest_spring_mm':bb[5]+7.1,
        'conclusions':['Exact existing MPN and land pattern are retained; no part substitution is indicated.',
                       'The stock-derived native Fab body is not the primary housing datum: exact CAD depth21.25 mm vs native Fab21.84 mm.',
                       'Actual mouth is local+19.780 mm, and candidate J15007 at274.4/321.7 overhangs the board by1.480 mm nominal.',
                       'All-metal18.703 mm width includes EMI springs; existing native courtyard nearly equals this width and is not a standard0.25 mm assembly clearance around springs.',
                       'Reserve15.4 mm above seating plane provisionally for all metal, while manufacturer13.5 mm is housing height; exact enclosure mating/tolerances remain fit qualification.',
                       'Native strict DRC and routed pair/return/impedance checks remain separate after adopted moves.']}
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'signal_pins':len(matches),'bbox':native_bb,'mouth_local_mm':native_bb[3],'candidate_overhang_mm':report['candidate_mouth_beyond_board_y340_mm'],'seating_flats':len(flats),'top_relative_mm':report['seating_plane_relative_highest_spring_mm']}))
