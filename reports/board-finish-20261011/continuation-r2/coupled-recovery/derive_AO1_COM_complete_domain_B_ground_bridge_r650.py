"""Same-net SOURCE-to-isolator DC-ground connection on B at .20 mm."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_complete_domain_In1_ground_bridge_r648.py';dest=H/'construct_AO1_COM_complete_domain_B_ground_bridge_r650.py';assert not dest.exists();text=src.read_text().replace('r648','r650').replace('R648_','R650_').replace("LY='In1.Cu'","LY='B.Cu'").replace('In1-Cu','B-Cu').replace('IN1_CU_GROUND_BRIDGE','B_CU_GROUND_BRIDGE')
text=text.replace('radius=.15','radius=.10').replace("'width_mm':.30","'width_mm':.20").replace('identity.serial_segment(COM,LY,a,z,.30)','identity.serial_segment(COM,LY,a,z,.20)').replace("'w':.30","'w':.20")
old='[[365.540084,143.159914],[371.840088789812,149.45991049947006]]';new='[[361.7409622594442,142.52870979134772],[372.89919811712986,150.5010751738769]]';assert old in text;text=text.replace(old,new)
dest.write_text(text);print('R650_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
