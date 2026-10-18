"""Meaningful negative controls for exact source/hash/copper publication gates."""
import copy,json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew as p
from publish_full_motherboard_board_review import verify_adoption,copper_delta,sha,verify_layout_member
from hardware_route_logic_return import identity

cases=[]
def reject(name,fn):
    try:fn()
    except ValueError:cases.append({'name':name,'pass':True});return
    raise AssertionError('Tamper accepted: '+name)
with tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp)
    for n,text in [('design.json',json.dumps({'components':{'R1':{'value':'1k','mpn':'TEST'}}})),('netlist.xml','sourcefixture'),('assembly-map.json','{}')]:
        (root/n).write_text(text)
    base={'native_ERC_errors':0,'ignored_checks':0,'independent_source_validation':True,'focused_tests_run':3,'focused_tests_passed':3,'physical_parts':1,'hashes':{n:sha(root/n)for n in ['design.json','netlist.xml','assembly-map.json']}}
    assert verify_adoption(base,root)['components'];cases.append({'name':'exact_source_accepts','pass':True})
    for key,value in [('native_ERC_errors',1),('ignored_checks',1),('independent_source_validation',False),('focused_tests_passed',2),('physical_parts',2)]:
        bad=copy.deepcopy(base);bad[key]=value;reject('reject_'+key,lambda bad=bad:verify_adoption(bad,root))
    (root/'netlist.xml').write_text('changed');reject('reject_changed_native_netlist_hash',lambda:verify_adoption(base,root))

class Fixture:
    def __init__(self,tracks):self.tracks=tracks
    def GetTracks(self):return self.tracks
b=p.BOARD();t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(1,1));t.SetEnd(p.VECTOR2I(5,5));t.SetWidth(200000);t.SetLayer(p.F_Cu)
same=Fixture([t]);assert copper_delta(same,same,None)['unchanged_previous_items']==1
cases.append({'name':'retained_copper_accepts','pass':True})
uid=t.m_Uuid.AsString();old=json.loads(json.dumps(identity(t)));empty=Fixture([])
reject('reject_unreviewed_removed_copper',lambda:copper_delta(same,empty,None))
ledger={'changes':[{'uuid':uid,'old_identity':old,'new_identity':None,'reason':'Exact reviewed shield branch relocation fixture'}]}
assert copper_delta(same,empty,ledger)['explicit_changed_previous_items']==1;cases.append({'name':'exact_removed_UUID_and_reason_accepts','pass':True})
for name,change in [('missing_reason',{'reason':''}),('wrong_old_identity',{'old_identity':['wrong']}),('wrong_new_identity',{'new_identity':['invented']})]:
    bad=copy.deepcopy(ledger);bad['changes'][0].update(change);reject(name,lambda bad=bad:copper_delta(same,empty,bad))
bad=copy.deepcopy(ledger);bad['changes'].append(copy.deepcopy(bad['changes'][0]));reject('reject_duplicate_UUID_ledger',lambda:copper_delta(same,empty,bad))
graphics_path=Path(__file__).resolve().parents[1]/'motherboard-pcb-integration-20260930/mechanical-library-r23-r03/graphic-layer-reconciliation-receipt.json'
graphics=json.loads(graphics_path.read_text());overrides={r['FPID']:r for r in graphics['project_copied_library_overrides']}
for fid,r in overrides.items():
    baseline=Path(r['original_path']);project=Path(r['project_copy_path'])
    assert verify_layout_member(fid,baseline,project,overrides)['physical_land_unchanged'];cases.append({'name':'reviewed_graphics_with_exact_lands_accepts_'+fid,'pass':True})
fid,r=next(iter(overrides.items()));baseline=Path(r['original_path']);project=Path(r['project_copy_path'])
reject('reject_unreviewed_graphics_override',lambda:verify_layout_member(fid,baseline,project,{}))
bad=copy.deepcopy(overrides);bad[fid]['project_copy_sha256']='0'*64
reject('reject_incorrect_graphics_project_hash',lambda:verify_layout_member(fid,baseline,project,bad))
with tempfile.TemporaryDirectory()as tmp:
    directory=Path(tmp)/'fixture.pretty';directory.mkdir();name=fid.split(':',1)[1]
    fp=p.FootprintLoad(str(project.parent),name);pad=next(iter(fp.Pads()));pad.SetSize(p.VECTOR2I(pad.GetSize().x+1000,pad.GetSize().y))
    p.PCB_IO_KICAD_SEXPR().FootprintSave(str(directory),fp)
    changed=directory/(name+'.kicad_mod');bad=copy.deepcopy(overrides);bad[fid]['project_copy_sha256']=sha(changed)
    reject('reject_changed_land_even_with_matching_receipt_hash',lambda:verify_layout_member(fid,baseline,changed,bad))
result={'tests_run':len(cases),'tests_passed':len(cases),'cases':cases,'scope':'Publication guard source/hash/native-copper negative controls. No public manifest, source or candidate PCB written.'}
out=Path(__file__).with_name('full-publisher-guard-tests-r02.json');assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
