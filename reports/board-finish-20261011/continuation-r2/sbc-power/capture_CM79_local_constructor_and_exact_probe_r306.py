"""Freeze expanded local constructor and inspect exact prescribed free path."""
from pathlib import Path
P=Path(__file__).resolve().parent
owner=P/'nominate_CM79_local_fullwidth_power_and_three_owned_stitches_r305.py'
ns={'__file__':str(owner),'__name__':'_capture_only_without_running_constructor'}
exec(compile(owner.read_text(),str(owner),'exec'),ns)
s=ns['s'];assert 'def main():'in s and 'CM79-local-fullwidth' in s
O=P/'CM79-local-fullwidth-expanded-authority-and-probe-r306';assert not O.exists();O.mkdir()
(O/'exact-expanded-r305-constructor.py').write_text(s,encoding='utf-8')
s=s.replace('CM79-local-fullwidth-CORE5-three-owned-stitch-endpoint-preserving-nomination-r305','CM79-local-fullwidth-actual-free-line-probe-r306')
needle="row['power_route_windows'].append(rrow)"
replacement="row['power_route_windows'].append(rrow);probe=[local_start,[local_start[0],202.715],[anchor_start[0],202.715],anchor_start];rrow['prescribed_probe_coords_mm']=probe;rrow['full_prescribed_probe_free']=pf.covers(LineString(probe));rrow['probe_segment_coverage']=[pf.covers(LineString([aa,bb]))for aa,bb in zip(probe,probe[1:])];(O/(str(y)+'-'+str(radius)+'-exact-power-free.wkb')).write_bytes(pf.wkb)"
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace('R305','R306')
exec(compile(s,str(__file__),'exec'),{'__file__':str(__file__),'__name__':'__main__'})
