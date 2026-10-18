"""Roundtrip exact r5 outlines, including one complete empty-fill FG retirement."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'roundtrip_native_splice_outlines.py').read_text().replace("'native-50um-splice-roundtrip-r1'","'native-50um-splice-roundtrip-r5'")
s=s.replace("z=index[row['uuid']];z.SetOutline(polygon_input(row));z.UnFill();z.SetNeedRefill(True)","z=index[row['uuid']]\n    if not row['polygons_integer_IU']:board.Remove(z);continue\n    z.SetOutline(polygon_input(row));z.UnFill();z.SetNeedRefill(True)")
s=s.replace("z=index[row['uuid']];ps=z.Outline();polys=[]", "if not row['polygons_integer_IU']:\n        assert row['uuid']not in index;rows.append({'uuid':row['uuid'],'complete_empty_fill_source_zone_retirement':True});continue\n    z=index[row['uuid']];ps=z.Outline();polys=[]")
exec(compile(s,str(HERE/'roundtrip_native_splice_outlines.py'),'exec'),globals())
