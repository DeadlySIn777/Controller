"""Retained-copper search to actual four-ampere A output-return terminals."""
from pathlib import Path
path=Path(__file__).with_name('variable_return_r2.py')
text=path.read_text(encoding='utf-8').replace("OUT=HERE/'variable-return-r2'","OUT=HERE/'variable-return-r3'")
old="[('FBG',0,box(0,120,255,239)),('FAG',0,box(180,120,455,239))]"
assert old in text
text=text.replace(old,"[('FAG',38,box(0,120,455,239))]")
exec(compile(text,str(path),'exec'))
