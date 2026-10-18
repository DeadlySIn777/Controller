"""Read saved single-outer zones without dereferencing missing fill containers."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'native_single_outer_zone_roundtrip_r9.py').read_text()
start=s.index("for row in d['zones']:\n    assert len(row['polygons_integer_IU'])==1")
end=s.index("for row in d['zones']:\n    z=index[row['uuid']];ps=z.Outline();assert ps.OutlineCount()==1",start)
s=s[:start]+"b=pcbnew.LoadBoard(d['minimal_native_output']);index={z.m_Uuid.AsString():z for z in b.Zones()};rows=[]\n"+s[end:]
s=s.replace("z.GetFilledPolysList(ly).OutlineCount()==0", "(not z.HasFilledPolysForLayer(ly)or z.GetFilledPolysList(ly).OutlineCount()==0)")
s=s.replace("'native-roundtrip-receipt.json'","'native-roundtrip-receipt-r10.json'")
s=s.replace("'fill_called':False,'DRC_called':False", "'fill_called':False,'DRC_called':False,'this_run_board_saved':False,'saved_document_created_by':'native_single_outer_zone_roundtrip_r9.py before missing-layer fill-container readback assertion'")
exec(compile(s,str(HERE/'native_single_outer_zone_roundtrip_r9.py'),'exec'),globals())
