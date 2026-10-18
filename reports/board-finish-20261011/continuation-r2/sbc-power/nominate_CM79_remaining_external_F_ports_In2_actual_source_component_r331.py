"""Search remaining real LG ports with exact In2 source connectivity required."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r323/exact-expanded-constructor.py'
assert hashlib.sha256((p.parent/'receipt.json').read_bytes()).hexdigest()=='aa45aba75979c06f4ef43932f0ba7fe171808e24443efd609aac7ae90e5e96f0'
s=p.read_text(encoding='utf-8').replace('nominations-r323','nominations-r331').replace('R323_SPUR','R331_SPUR').replace('R323_COMPLETE','R331_COMPLETE')
s=s.replace('region=box(104,190,138,215)','region=box(104,190,180,225)').replace('[104,190,138,215]','[104,190,180,225]')
# The expanded R323 script originally used R322 print labels; retain exact
# geometry but give this diagnostic its own identifiers.
s=s.replace('R322_SPUR','R331_SPUR').replace('R322_COMPLETE','R331_COMPLETE')
s=s.replace('from shapely import set_precision','from shapely import set_precision,from_wkb')
s=s.replace("rows=[];accepted={'left':[],'right':[]};count=0", "sourceNom=H/'sbc-power/CM79-external-larger-power-port-full1p25-In2-actual-source-route-nominations-r328';assert sha(sourceNom/'receipt.json')=='4578885140603385b6f22e4a4f76b5b452364fa9ec8b579f9a748dc9212c2371';sourceFree=zero(from_wkb((sourceNom/'exact-full1p25-In2-centre-free-native-fill-retreat-pending.wkb').read_bytes()));sourceTarget=zero(from_wkb((sourceNom/'actual-source-rooted-In2-spatial-target.wkb').read_bytes()));sourceFaces=[face for face in RF.parts(sourceFree)if not face.intersection(buf(sourceTarget,.624995)).is_empty];assert sourceFaces;put(O/'exact-frozen-In2-actual-source-component-authority.json',{'receipt_sha256':sha(sourceNom/'receipt.json'),'free_space_WKB_sha256':sha(sourceNom/'exact-full1p25-In2-centre-free-native-fill-retreat-pending.wkb'),'actual_source_target_WKB_sha256':sha(sourceNom/'actual-source-rooted-In2-spatial-target.wkb'),'actual_source_touching_component_count':len(sourceFaces),'all_native_discrete_owned_positive_holes_rules_stay_hard':True});rows=[];targets={'right':targets['right']};accepted={'right':[]};count=0")
s=s.replace("if not ff.covers(end):continue", "if not ff.covers(end)or not any(face.covers(end)for face in sourceFaces):continue")
s=s.replace('>=8','>=4')
s=s.replace("'NO_TWO_ENDED_EXTERNAL_FULLWIDTH_SOURCE_SPUR_NOMINEE_IN_DECLARED_WINDOW_AND_ORDINARY_PORT_GRID'", "'NO_EXTERNAL_FULLWIDTH_DETACHED_RIGHT_SPUR_IN_ACTUAL_In2_SOURCE_COMPONENT_IN_DECLARED_GRID'")
s=s.replace("'EXTERNAL_FULLWIDTH_SOURCE_SPURS_NOMINATED_COMBINED_In2_SOURCE_NATIVE_REFERENCE_CURRENT_PROOF_OPEN'", "'EXTERNAL_FULLWIDTH_DETACHED_RIGHT_SPUR_IN_ACTUAL_In2_SOURCE_COMPONENT_NOMINATED_ALL_COMBINED_GATES_OPEN'")
frozenParentScriptSha=hashlib.sha256((Path(__file__).with_name('nominate_CM79_external_fullwidth_F_side_port_spurs_r321.py')).read_bytes()).hexdigest()
exec(compile(s,str(__file__),'exec'))
