"""Correct a model field adapter in a separate preserved constructor."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;src=H/'construct_pen_existing_In3_or_dive_r84.py';b=src.read_bytes();s=b.decode().replace('r84','r86').replace("v['diam']","v['d']")
dst=H/'construct_pen_existing_In3_or_dive_r86.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec');out=H/'prepare-PEN-model-via-adapter-r86.json';assert not out.exists();out.write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'original_failure':'R84 stopped before return nomination, KeyError diam; frozen model native diameter field is d. No board/operation/receipt or passing geometry claim resulted.','delta':'Use exact d model field, same source/masks and obligations, separate output/cache.'},indent=1)+'\n');print(dst)
