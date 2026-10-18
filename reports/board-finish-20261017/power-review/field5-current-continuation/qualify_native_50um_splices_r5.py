"""Host gates for r5 robust explicit native intent and negative Cu targets."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'qualify_native_50um_splices.py').read_text().replace("'native-50um-splice-host-qualification-r1'","'native-50um-splice-host-qualification-r5'").replace("'native-50um-splice-construction-r3'","'native-50um-splice-construction-r5'")
exec(compile(s,str(HERE/'qualify_native_50um_splices.py'),'exec'),globals())
