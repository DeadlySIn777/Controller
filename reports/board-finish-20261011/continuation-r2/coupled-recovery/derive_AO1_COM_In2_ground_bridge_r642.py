"""Test the finite SOURCE/target plated contacts on the remaining inner layer."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_actual_source_ground_bridge_r638.py';dest=H/'construct_AO1_COM_actual_source_In2_ground_bridge_r642.py';assert not dest.exists();text=src.read_text().replace('r638','r642').replace('R638_','R642_').replace("LY='In3.Cu'","LY='In2.Cu'").replace('In3-Cu','In2-Cu').replace('IN3_CU_GROUND_BRIDGE','IN2_CU_GROUND_BRIDGE')
dest.write_text(text);print('R642_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
