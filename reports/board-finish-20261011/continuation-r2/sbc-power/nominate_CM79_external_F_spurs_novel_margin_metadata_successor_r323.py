"""Freeze R322 metadata-name failure; same exact geometry in successor."""
from pathlib import Path
parent=Path(__file__).with_name('nominate_CM79_external_F_spurs_exact_novel_Cu_margin_r322.py')
code=parent.read_text(encoding='utf-8')
code=code.replace("'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r322'", "'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r323'")
code=code.replace("s=p.read_text(encoding='utf-8')", "frozenParentScriptSha=hashlib.sha256(p.read_bytes()).hexdigest()\ns=p.read_text(encoding='utf-8')")
code=code.replace("'parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest()", "'parent_script_sha256':frozenParentScriptSha")
code=code.replace('R322_SPUR','R323_SPUR').replace('R322_COMPLETE','R323_COMPLETE')
exec(compile(code,str(parent),'exec'))
