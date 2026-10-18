"""Preserve r15b precision-model failure; restore cutter precision before buffer.

Shapely pickle uses WKB and drops the precision model. The originating r15
crossing cutter had a1nm precision model. Restoring it is necessary to reproduce
its buffer and exact boolean carve, not a geometric-tolerance exemption.
"""
from pathlib import Path
path=Path(__file__).resolve().parent/'audit_field_io3_crossings_r15b.py'
code=path.read_text()
code=code.replace("OUT=HERE/'field-io3-crossing-contact-audit-r15b'","OUT=HERE/'field-io3-crossing-contact-audit-r15c'")
code=code.replace("finger['shape'].buffer(.625)","set_precision(finger['shape'],1e-6).buffer(.625)")
code=code.replace("expected.equals_exact(new['shape'],0)","expected.normalize().equals_exact(new['shape'].normalize(),0)")
exec(compile(code,str(path),'exec'))
