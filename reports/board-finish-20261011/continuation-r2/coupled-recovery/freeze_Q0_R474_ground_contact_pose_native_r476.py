"""Freeze only corrected FP pose and its exact sparse Cu operation."""
from pathlib import Path
import builtins
H=Path(__file__).resolve().parent;base=H/'freeze_Q0_R460_exact_native_operation_r464.py'
def scoped_compile(source,filename,mode,*args,**kwargs):
 if isinstance(source,str):
  source=source.replace('Q0-R460-exact-native-owned-operation-r464','Q0-R474-ground-contact-pose-native-r476').replace('Q0-GATE-SENSE-reserve-safe-source-r460','Q0-native-ground-contact-pose-r474').replace('3d4eee7be4b8f6edfeee68ebec7b59404070263132ae382fbdb2eb65c794f0fb','4c19d2697c139b2728133d012fe258ee1ac6072233e8b7e07fc11627f5b20a6f').replace('R460_nomination_receipt_sha256','R474_nomination_receipt_sha256')
  if 'fps=[(uid,ch)'in source:
   source=source.replace('229.86','229.96').replace("'R10016_translation_mm':[-.5,-.5]","'R10016_translation_mm':[-.4,-.5]")
 return builtins.compile(source,filename,mode,*args,**kwargs)
ns={'__file__':str(base),'__name__':'__main__','compile':scoped_compile};exec(scoped_compile(base.read_text(),str(base),'exec'),ns)
