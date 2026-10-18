"""Create the attributed KiCad-library J4 derivative without changing its lands."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
old='TerminalBlock_Phoenix_MPT-0,5-2-2.54_1x02_P2.54mm_Horizontal'
new='Phoenix_1725656_MPT_0p5_2_2p54_SilkClearance'
source=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/TerminalBlock_Phoenix.pretty')/(old+'.kicad_mod')
text=source.read_text(encoding='utf-8')
before='''\t(fp_line
\t\t(start -1.62 -3.22)
\t\t(end 4.16 -3.22)
\t\t(stroke
\t\t\t(width 0.12)
\t\t\t(type solid)
\t\t)
\t\t(layer "F.SilkS")
\t)'''
assert text.count(before)==1
modified=text.replace(before,before.replace('"F.SilkS"','"Dwgs.User"'))
modified=modified.replace('"'+old+'"','"'+new+'"')
assert modified.replace('"'+new+'"','"'+old+'"').replace(before.replace('"F.SilkS"','"Dwgs.User"'),before)==text
target=R/'Adapter.pretty'/(new+'.kicad_mod');target.write_text(modified,encoding='utf-8')
report={'source_footprint':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derivative':target.name,'derivative_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'only_geometry_change':'Upper horizontal line from (-1.62,-3.22) to (4.16,-3.22) moved from F.SilkS to Dwgs.User.','name_and_value_renamed':True,'reversible_text_comparison_passed':True,'pads_fab_courtyard_and_models_unchanged':True,'source_project':'KiCad footprint libraries, KiCad community','license':'CC-BY-SA-4.0 with KiCad library exception','license_url':'https://www.kicad.org/libraries/license/'}
(R/'j4-footprint-derivative-review.json').write_text(json.dumps(report,indent=2)+'\n')
print('Created',target.name,'with an exact reversible change check')
