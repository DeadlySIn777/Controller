"""Use the proven owned single-outer native writer and guarded exact readback."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'native_single_outer_zone_roundtrip_r9.py').read_text().replace("'single-outer-real-corridor-native-r9'","'strict-FG-F-native-single-outer-r16'")
s=s.replace("z.GetFilledPolysList(ly).OutlineCount()==0","(not z.HasFilledPolysForLayer(ly)or z.GetFilledPolysList(ly).OutlineCount()==0)")
exec(compile(s,str(HERE/'native_single_outer_zone_roundtrip_r9.py'),'exec'),globals())
