"""Use the complete actual SOURCE/island domain bounds, not the nearest gap ROI."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_actual_source_ground_bridge_r638.py';dest=H/'construct_AO1_COM_complete_domain_In4_ground_bridge_r644.py';assert not dest.exists();text=src.read_text().replace('r638','r644').replace('R638_','R644_').replace("LY='In3.Cu'","LY='In4.Cu'").replace('In3-Cu','In4-Cu').replace('IN3_CU_GROUND_BRIDGE','IN4_CU_GROUND_BRIDGE')
assert 'win=box(353,137,381,163)' in text;text=text.replace('win=box(353,137,381,163)','win=box(332,102,390,172)')
text=text.replace('"""Small real SOURCE-to-isolator COM bridge, ground conduction only.','"""SOURCE-to-isolator COM bridge over complete actual domain, ground only.')
dest.write_text(text);print('R644_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
