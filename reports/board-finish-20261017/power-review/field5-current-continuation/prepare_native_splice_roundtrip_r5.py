"""Bind the current r5 outlines to genuine filled R299 and exact stage1 input."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'prepare_native_splice_roundtrip.py').read_text().replace("'native-50um-splice-construction-r3'","'native-50um-splice-construction-r5'").replace("'native-50um-splice-roundtrip-r1'","'native-50um-splice-roundtrip-r5'").replace('r299/copy/board.kicad_pcb','r299/filled-copy/board.kicad_pcb')
exec(compile(s,str(HERE/'prepare_native_splice_roundtrip.py'),'exec'),globals())
