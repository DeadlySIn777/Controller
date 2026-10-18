from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-two-part-cell-screen-r175.py').read_text().replace('U20-two-part-local-retired-screen-r175','U20-two-part-local-retired-screen-r176').replace('U20-two-part-cell-candidates-r175.json','U20-two-part-cell-candidates-r176.json')
s=s.replace("for ix in range(-12,13):\n  for iy in range(-12,13):","for ix,iy in[(i,j)for i in[0,7,8,9,10,11,12,-7,-8,-9,-10,-11,-12]for j in[0,7,8,9,10,11,12,-7,-8,-9,-10,-11,-12]]:\n  for unused in[0]:")
s=s.replace("gfs=[v for v in paths(mm(pmap['2'].GetPosition()),q)if g.clear(v,gn,pcbnew.F_Cu,.25)]", "gfs=[None]")
s=s.replace("no_cross(gr,bpath)and no_cross(gf,fpath)","no_cross(gr,bpath)")
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-two-part-cell-screen-r176.py').write_text(s)
