"""Correct only the unaccepted resistor X pose to retain native FG contacts."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_saved_GATE_SENSE_existing_barrels_r450.py'
code=base.read_text().replace('Q0-saved-GATE-SENSE-existing-barrels-r450','Q0-native-ground-contact-pose-r474').replace('[229.15,156.57]','[228.95,156.95]')
old="exec(compile(prefix,str(base),'exec'))"
new="prefix=prefix.replace('xoff=-.5,yoff=-.5','xoff=-.4,yoff=-.5')\nexec(compile(prefix,str(base),'exec'))"
assert old in code;code=code.replace(old,new,1).replace("'R10016_translation_mm':[-.5,-.5]","'R10016_translation_mm':[-.4,-.5]")
exec(compile(code,str(base),'exec'))
