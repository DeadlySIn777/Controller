"""Gate the exact original-preserving current corridor and explicit FG targets."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'qualify_native_50um_splices.py').read_text().replace("'native-50um-splice-host-qualification-r1'","'separate-real-corridor-zone-host-qualification-r7'").replace("'native-50um-splice-construction-r3'","'separate-real-corridor-zone-construction-r7'")
s=s.replace("CON/'field-native-positive-intent.wkb'","CON/'field-new-real-corridor-intent.wkb'")
s=s.replace("assert oldintent.difference(intent).is_empty", "assert next(z for z in h['zones']if z['uuid']==ZID)==fz;assert support.equals(intent)")
exec(compile(s,str(HERE/'qualify_native_50um_splices.py'),'exec'),globals())
