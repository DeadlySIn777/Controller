"""Read-only native mechanical inspection and dimensioned 2-D assembly drawing."""
from pathlib import Path
import json,hashlib,math,html,xml.etree.ElementTree as ET
import pcbnew as p

R=Path(__file__).resolve().parent
boardfile=R/'adapter.kicad_pcb';b=p.LoadBoard(str(boardfile));layout=json.loads((R/'placement.json').read_text())
W,H=layout['board_mm'];fps={};pads=[];issues=[]
def bb(box):return [p.ToMM(box.GetLeft())-100,p.ToMM(box.GetTop())-100,p.ToMM(box.GetRight())-100,p.ToMM(box.GetBottom())-100]
for fp in b.GetFootprints():
 ref=fp.GetReference();side='bottom' if fp.IsFlipped() else 'top';outlines=[]
 for g in fp.GraphicalItems():
  if g.GetLayer()==(p.B_Fab if fp.IsFlipped() else p.F_Fab) and g.GetClass()=='PCB_SHAPE':outlines.append(bb(g.GetBoundingBox()))
 envelope=[min(x[0] for x in outlines),min(x[1] for x in outlines),max(x[2] for x in outlines),max(x[3] for x in outlines)] if outlines else None
 fps[ref]={'side':side,'xy':[p.ToMM(fp.GetPosition().x)-100,p.ToMM(fp.GetPosition().y)-100],'angle_deg':fp.GetOrientationDegrees(),'fab_graphics_envelope_mm':envelope,'footprint':str(fp.GetFPID().GetLibItemName()),'model_count':len(list(fp.Models()))}
 for pad in fp.Pads():
  if pad.GetDrillSizeX()>0:
   pads.append({'reference':ref,'pin':pad.GetNumber(),'xy':[p.ToMM(pad.GetPosition().x)-100,p.ToMM(pad.GetPosition().y)-100],'copper_envelope':bb(pad.GetBoundingBox()),'drill_mm':p.ToMM(pad.GetDrillSizeX())})
def distance(a,c):return math.hypot(max(a[0]-c[2],c[0]-a[2],0),max(a[1]-c[3],c[1]-a[3],0))
checks=[]
for ref,fp in fps.items():
 if fp['side']!='top' or not fp['fab_graphics_envelope_mm']:continue
 for pad in pads:
  if pad['reference'] not in ['J1','J2']:continue
  dist=distance(fp['fab_graphics_envelope_mm'],pad['copper_envelope'])
  checks.append({'top_part':ref,'header':pad['reference'],'pin':pad['pin'],'nominal_plan_gap_mm':round(dist,4)})
  if dist<=0:issues.append(checks[-1])
report={'status':'read-only source geometry inspection; actual host fit and assembled height qualification pending','board_sha256':hashlib.sha256(boardfile.read_bytes()).hexdigest(),'placement_sha256':hashlib.sha256((R/'placement.json').read_bytes()).hexdigest(),'board_mm':[W,H],'pcb_thickness_mm':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'source_footprints':fps,'through_holes':pads,'header_top_tail_screen':{'method':'Conservative top F.Fab graphical bounding envelopes versus actual underside-header through-pad copper bounding envelopes; disjoint envelopes establish nominal plan-view clearance only. Solder fillet growth, tolerance stack and lead tilt remain physical assembly checks.','overlaps':issues,'minimum_gap':min(checks,key=lambda x:x['nominal_plan_gap_mm']),'all_checks':checks},'nominal_interface':{'row_centres_mm':[1.27,13.97],'row_spacing_mm':12.7,'pin_pitch_mm':2.54,'legacy_stepstick_body_length_mm':20.32,'dir_end_extension_mm':round(H-20.32,3),'vm_pin_pad_hole_absent':True,'j4_wire_exit_direction':'+Y, outward beyond board end','switch_is_inboard_of_terminal':True},'vertical_stack':{'header_mpn':'61300811121 / 61300711121','header_insulator_nominal_mm':2.54,'header_mating_post_from_insulator_nominal_mm':6.0,'total_below_adapter_pcb_to_tip_nominal_mm':8.54,'header_solder_tail_from_insulator_nominal_mm':3.0,'header_tail_above_1_6mm_pcb_nominal_mm':1.4,'interpretation':'Underside header insulator seated against board underside, 3 mm solder-tail side through the adapter; 6 mm mating post extends from lower plastic surface. Actual mating depth and host socket stack are unconfirmed.','bottom_smt_max_height_requirement_mm':1.5,'bottom_smt_heights_measured':False,'host_component_clearance_verified':False},'missing_custom_models':[r for r,f in fps.items() if f['model_count']==0],'release_gates':['Confirm exact host socket orientation, pinout, voltage and firmware polarity.','Check 17.78 mm DIR-end extension against host board components, neighbouring slots and enclosure.','Verify underside SMD maximum heights and host clearances at full insertion.','Check solder-tail trim, solder fillets, terminal wire access and selector actuator clearance.','Verify selector continuity versus finished labels with power removed.'],'sources':['https://www.we-online.com/components/products/datasheet/61300811121.pdf','https://www.we-online.com/components/products/datasheet/61300711121.pdf','https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mpt-05-2-254-1725656?type=pdf']}
(R/'mechanical-review.json').write_text(json.dumps(report,indent=2)+'\n')

S=14;TX,TY=85,180;BX,BY=475,180
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="980" viewBox="0 0 1400 980">','<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="#54677b"/></marker></defs>','<rect width="1400" height="980" fill="#f8fafc"/>','<style>text{font-family:Arial,sans-serif;fill:#173047}.title{font-size:30px;font-weight:700}.sub{font-size:16px;fill:#54677b}.head{font-size:19px;font-weight:700}.body{font-size:16px}.dim{font-size:13px;fill:#54677b}.ref{font-size:10px;font-weight:700;paint-order:stroke;stroke:#fff;stroke-width:2px;stroke-linejoin:round}.small{font-size:13px;fill:#54677b}.warning{fill:#9a5b00;font-weight:700}</style>']
def text(x,y,s,cls='body',extra=''):
 sizes={'body':16,'title':30,'sub':16,'head':19,'dim':13,'ref':10,'small':13}
 weight='700' if cls in ['title','head','ref'] else '400'
 color='#54677b' if cls in ['sub','dim','small'] else '#173047'
 svg.append(f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{sizes[cls]}" font-weight="{weight}" fill="{color}" {extra}>{html.escape(s)}</text>')
def line(x1,y1,x2,y2,color='#54677b',dash=None):svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.2"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
def dim(x1,y1,x2,y2,label,lx,ly):
 svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#54677b" stroke-width="1" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
 if abs(x1-x2)<.01:
  line(x1-4,y1,x1+4,y1);line(x2-4,y2,x2+4,y2)
  mid=(y1+y2)/2;xx=x1-9
  text(xx,mid,label,'dim',f'text-anchor="middle" transform="rotate(-90 {xx} {mid})"')
 else:
  line(x1,y1-4,x1,y1+4);line(x2,y2-4,x2,y2+4);text(lx,ly,label,'dim')
text(45,55,'OEA r0.2 · assembly geometry review','title')
text(45,86,'15.24 × 38.10 mm · four layers · 1.60 mm PCB · source-derived 2-D views','sub')
text(45,116,'ENGINEERING CANDIDATE — HOST FIT AND ASSEMBLED CLEARANCE NOT QUALIFIED','sub','style="fill:#9a5b00;font-weight:700"')
def draw_board(x,y,side):
 svg.append(f'<rect x="{x}" y="{y}" width="{W*S}" height="{H*S}" rx="0" fill="'+('#ecf8f2' if side=='top' else '#edf3fb')+'" stroke="#2d7766" stroke-width="1.5"/>')
 path=R/f'assembly-{side}-native.svg';root=ET.parse(path).getroot()
 for parent in root.iter():
  for child in list(parent):
   if child.attrib.get('class')=='stroked-text':parent.remove(child)
 inner=''.join(ET.tostring(child,encoding='unicode') for child in root if child.tag.split('}')[-1] not in ['title','desc']);inner=inner.replace('#AFAFAF','#516473').replace('#D0D2CD','#516473')
 trans=f'translate({x},{y}) scale({S})' if side=='top' else f'translate({x+W*S},{y}) scale({-S},{S})'
 svg.append(f'<g transform="{trans}">{inner}</g>')
 for pad in pads:
  px,py=pad['xy'];px=px if side=='top' else W-px
  svg.append(f'<circle cx="{x+px*S}" cy="{y+py*S}" r="{pad["drill_mm"]*S/2}" fill="#fff" stroke="#7f91a0" stroke-width=".7"/>')
  if pad['reference'] in ['J1','J2']:svg.append(f'<rect x="{x+px*S-.32*S}" y="{y+py*S-.32*S}" width="{.64*S}" height="{.64*S}" fill="#9da7af"/>')
 for ref,fp in fps.items():
  if fp['side']!=side or ref in ['J1','J2']:continue
  px,py=fp['xy'];px=px if side=='top' else W-px
  text(x+px*S,y+py*S+3,ref,'ref','text-anchor="middle"')
 # Legacy StepStick length and physical VM omission.
 line(x,y+20.32*S,x+W*S,y+20.32*S,'#7f91a0','5,4')
 vx=13.97 if side=='top' else W-13.97;vy=1.27
 svg.append(f'<circle cx="{x+vx*S}" cy="{y+vy*S}" r="8" fill="none" stroke="#c45d45" stroke-width="1.5" stroke-dasharray="3,2"/>')
 line(x+vx*S-6,y+vy*S-6,x+vx*S+6,y+vy*S+6,'#c45d45')
text(TX,139,'TOP · connector side','head');text(BX,139,'UNDERSIDE · viewed from below','head')
draw_board(TX,TY,'top');draw_board(BX,BY,'bottom')
dim(TX,TY-21,TX+W*S,TY-21,'15.24 mm',TX+65,TY-28)
dim(TX-31,TY,TX-31,TY+H*S,'38.10 mm',TX-51,TY+H*S/2)
dim(TX+W*S+25,TY+20.32*S,TX+W*S+25,TY+H*S,'17.78',TX+W*S+34,TY+30*S)
text(TX+W*S+33,TY+31.4*S,'DIR-end','dim');text(TX+W*S+33,TY+32.7*S,'extension','dim')
dim(BX+1.27*S,BY-20,BX+13.97*S,BY-20,'12.70 mm row centres',BX+30,BY-28)
text(BX+8,BY+H*S+25,'Pin pitch: 2.54 mm · opposite-face holes aligned','small')
line(TX+3.77*S,TY+H*S+3,TX+3.77*S,TY+H*S+44,'#2d7766')
svg.append(f'<path d="M{TX+3.77*S-5},{TY+H*S+37} L{TX+3.77*S},{TY+H*S+47} L{TX+3.77*S+5},{TY+H*S+37}" fill="#2d7766"/>')
text(TX-5,TY+H*S+68,'J4 wires leave outward (+Y)','small')
text(TX-5,TY+H*S+87,'SW1 sits inboard of the terminal','small')
NX=790
text(NX,176,'Assembly checks','head')
for i,t in enumerate(['J1: 8-pin underside male header','J2: 7-pin underside header; VM contact absent','J3: keyed JST XH 4-pin signal header','J4: external supply screw terminal','SW1: 5V / EXT common selector']):text(NX,210+i*27,t,'body')
text(NX,370,'Nominal vertical stack','head')
for i,t in enumerate(['1.60 mm PCB','2.54 mm header plastic below PCB','6.00 mm mating post below that plastic','8.54 mm PCB underside to post tip','≈1.40 mm untrimmed header tail above PCB']):text(NX,404+i*27,t,'body')
text(NX,566,'This is a dimensional source review','head')
for i,t in enumerate(['Fab outlines come directly from the native PCB.','Underside view is mirrored for a real bottom view.','Top bodies were screened against header-tail pads.','Host socket depth and nearby components are unknown.','Bottom SMT height requirement: ≤1.5 mm; unmeasured.','Selector tail trim and both cable exits need checking.']):text(NX,600+i*27,t,'body')
text(45,848,'PLAN-VIEW SCREEN: '+('NO TOP BODY / HEADER-TAIL ENVELOPE OVERLAPS' if not issues else 'OVERLAPS FOUND'),'head')
minimum=report['header_top_tail_screen']['minimum_gap']
text(45,878,f"Minimum nominal bounding-envelope gap: {minimum['nominal_plan_gap_mm']:.3f} mm ({minimum['top_part']} to {minimum['header']} pin {minimum['pin']}). Physical tolerances remain open.",'body')
text(45,910,'No 3-D fit claim. Custom-module 3-D models absent: '+', '.join(report['missing_custom_models'])+'.','small')
text(45,941,'PCB SHA-256 at drawing generation: '+report['board_sha256'][:28]+'… · all dimensions in mm · not a fabrication release','small')
svg.append('</svg>');(R/'assembly-review.svg').write_text('\n'.join(svg),encoding='utf-8')
print('top/header envelope overlaps',issues,'minimum',minimum)
print('wrote assembly-review.svg and mechanical-review.json')
