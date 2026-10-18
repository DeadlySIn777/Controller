"""Read-only whole-plug/service projection audit for the 34 standard field ports."""
import json
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,graphic_box,body_box,transformed_box,grown,overlap

board_path=ROOT/'reports/motherboard-pcb-integration-20260930/mechanical-library-r23-r03/motherboard-mechanical-candidate.kicad_pcb'
recipe_path=ROOT/'reports/motherboard-power-entry-20260930/layout-r05/full-board-fit-r02/power-groups-geometry-candidate.kicad_pcb'
recipe_receipt=recipe_path.with_name('placement-receipt.json')
power_receipt=ROOT/'reports/motherboard-mechanical-20260930/r20-power-mate-candidates-r03-power-groups/review.json'
out=ROOT/'reports/motherboard-mechanical-20260930/r23-all-field-mates-r01'
assert not out.exists();out.mkdir()
before={str(f):sha(f)for f in [board_path,recipe_path,recipe_receipt,power_receipt]}
b=p.LoadBoard(str(board_path));fps={f.GetReference():f for f in b.GetFootprints()}
recipe=p.LoadBoard(str(recipe_path));recipe_fps={f.GetReference():f for f in recipe.GetFootprints()}
for group in json.loads(recipe_receipt.read_text())['groups']:
    for ref in group['refs']:
        fps[ref].SetPosition(recipe_fps[ref].GetPosition());fps[ref].SetOrientationDegrees(recipe_fps[ref].GetOrientationDegrees())
power=json.loads(power_receipt.read_text())
for ref,r in power['poses'].items():
    x,y,a=r['new_pose'];fps[ref].SetOrientationDegrees(a);fps[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
objects={r:(graphic_box(f,p.F_CrtYd)or body_box(f)[0])for r,f in fps.items()}
objects.update({'CM_MODULE':transformed_box(fps['J15001'],[-3,-30,37,25]),'ESP_MODULE':transformed_box(fps['J16001'],[-1.27,-1.565,24.13,61.3]),'ESP_RF_15MM_RECOMMENDATION':grown(transformed_box(fps['J16001'],[2.48,-7.85,20.48,-1.54]),15)})
for ref,r in power['poses'].items():
    for kind,box in r['envelopes_mm'].items():objects[ref+'_'+kind]=box
mates={2:'1840366',3:'1840379',6:'1840405',10:'1840447',12:'1840463',14:'1840489'}
ports={}
for ref,f in sorted(fps.items()):
    if not ref.startswith('J195'):continue
    n=len(list(f.Pads()));assert n in mates
    # Native header contact row is x=0..(n-1)*3.5, mouth at local y=8.
    # Reserve the ENTIRE 16.1-mm mate beyond the mouth, then 20-mm service.
    # Real mating overlap only shrinks this conservative external reservation.
    boxes={'full_plug':transformed_box(f,[-1.75,8,n*3.5-1.75,24.1]),
           'withdraw_wire_service':transformed_box(f,[-2.75,24.1,n*3.5-.75,44.1])}
    ports[ref]={'mate':mates[n],'positions':n,'whole_mate_width_mm':n*3.5,'whole_mate_depth_mm':16.1,'mate_height_mm':11.1,'pose':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y),f.GetOrientationDegrees()],'envelopes_mm':boxes}
for ref,r in ports.items():
    for kind,box in r['envelopes_mm'].items():objects[ref+'_'+kind]=box
for ref,r in ports.items():
    r['conservative_XY_conflicts']={kind:sorted(name for name,other in objects.items()if name!=ref and not name.startswith(ref+'_')and overlap(grown(box,.25),other))for kind,box in r['envelopes_mm'].items()}
    r['conservative_XY_clear']=not any(r['conservative_XY_conflicts'].values())
report={'board_sha256':sha(board_path),'read_only_input_hashes':before,'applied_only_in_RAM':'Exact six source-backed power-group recipes and six mutually checked power-header poses; native graphics/RF profile retained.',
        'native_field_headers':len(ports),'ports':ports,'conservative_clear_ports':sum(r['conservative_XY_clear']for r in ports.values()),
        'primary_source':'https://assets.phoenixcontact.com/file/411777ad-8c2a-42ff-a04f-701de299b37e/media/original?CAT_8_2021_EN_LoRes.pdf=',
        'primary_mating_reference':'https://www.phoenixcontact.com/en-gb/products/pcb-plug-mc-1510-st-35-1840447',
        'source_dimensions':'Manufacturer MC1.5/..-ST3.5 catalogue: width n*3.5mm, length16.1mm, height11.1mm, standard nonlocking female plug,0deg wire entry. Existing header pitch/contact count preserved.',
        'qualification_limit':'A conservative XY overlap is not an asserted physical collision: actual mating overlap and component Z may reduce it. Zero overlap proves this bounded projection clearance; occupied projections require exact 3D fit or relocation.20mm withdrawal is an engineering service allowance, not a universal cable-bend rating. The header contact current rating never changes actual circuit current limits.',
        'PCB_or_source_mutated':False,'manufacturing_ready':False}
assert before=={str(f):sha(f)for f in [board_path,recipe_path,recipe_receipt,power_receipt]}
(out/'review.json').write_text(json.dumps(report,indent=2)+chr(10));(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'ports':len(ports),'conservatively_clear':report['conservative_clear_ports'],'occupied':{ref:r['conservative_XY_conflicts']for ref,r in ports.items()if not r['conservative_XY_clear']}}))
