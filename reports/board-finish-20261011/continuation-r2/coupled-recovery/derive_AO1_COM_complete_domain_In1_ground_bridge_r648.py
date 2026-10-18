"""Complete-domain same-net SOURCE ground bridge on the other reference layer."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_complete_domain_In4_ground_bridge_r644.py';dest=H/'construct_AO1_COM_complete_domain_In1_ground_bridge_r648.py';assert not dest.exists();text=src.read_text().replace('r644','r648').replace('R644_','R648_').replace("LY='In4.Cu'","LY='In1.Cu'").replace('In4-Cu','In1-Cu').replace('IN4_CU_GROUND_BRIDGE','IN1_CU_GROUND_BRIDGE')
old='[[361.7409622594442,142.52870979134772],[372.89919811712986,150.5010751738769]]';new='[[365.540084,143.159914],[371.840088789812,149.45991049947006]]';assert old in text;text=text.replace(old,new)
dest.write_text(text);print('R648_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
