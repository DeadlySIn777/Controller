"""Exact raw net inventory includes native pad-only nets; no alias normalization."""
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r751.generated.py'
assert (H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r751/failure.json').exists()
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r751','FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753')
text=text.replace('import sys,json,pickle,hashlib,uuid,time,math,traceback','import sys,json,pickle,hashlib,uuid,time,math,traceback,re')
oldblock="""    net_tokens=set()
    for uid,ch in inv.items():
        if O.C.pcbtext.chunk_kind(ch) in ('zone','segment','via'):n=atom(parse(ch.decode()),'net');net_tokens.add(n) if n else None"""
newblock="""    net_tokens={json.loads('"'+m+'"') for m in re.findall(r'\\(net\\s+"((?:[^"\\\\]|\\\\.)*)"\\)',raw.decode('utf-8'))}
    assert len(net_tokens)==2388,('Complete literal native net inventory',len(net_tokens))"""
assert oldblock in text;text=text.replace(oldblock,newblock)
text=text.replace('R751_STAGED','R753_STAGED')
generated=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r753.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
