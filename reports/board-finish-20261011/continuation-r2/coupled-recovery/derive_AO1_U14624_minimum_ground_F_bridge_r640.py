"""Recheck the real F ground gap at permitted .20 mm, all old power fixed."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent;src=H/'construct_AO1_COM_actual_source_ground_bridge_r636.py';dest=H/'construct_AO1_COM_U14624_actual_minimum_F_ground_bridge_r640.py';assert not dest.exists();text=src.read_text().replace('r636','r640').replace('R636_','R640_')
assert 'radius=.15' in text;text=text.replace('radius=.15','radius=.10').replace("'width_mm':.30","'width_mm':.20").replace("identity.serial_segment(COM,LY,a,z,.30)","identity.serial_segment(COM,LY,a,z,.20)").replace("'w':.30","'w':.20")
assert ' for z in q:' in text;text=text.replace(' for z in q:'," latefile=pin(P/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');late=pickle.loads(latefile.read_bytes())\n for z in list(q)+late:")
dest.write_text(text);print('R640_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
