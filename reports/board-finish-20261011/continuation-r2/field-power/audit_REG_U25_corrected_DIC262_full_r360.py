"""Field-owned complete incremental audit; staged SBC peer not credited."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py').read_text(encoding='utf-8')
s=s.replace('REG-U25-T4-R7-corrected-DIC262-sparse-current-composition-r356','REG-U25-corrected-DIC262-sparse-current-composition-r359').replace('REG-U25-T4-R7-DIC-current-independent-full-audit-r358','REG-U25-corrected-DIC262-current-independent-full-audit-r360').replace("'f4863c44-a057-598a-aef7-adca7cfb15f1'", "'ed7b6af5-93e5-5f20-8977-d10ca721564d'").replace('==(26,6,18)','==(16,5,14)')
exec(compile(s,str(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py'),'exec'))
