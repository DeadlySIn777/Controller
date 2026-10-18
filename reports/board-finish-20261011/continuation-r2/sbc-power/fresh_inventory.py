import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.cwd()
def main():
    d=json.loads((HERE.parent/'native-198b-geometry/geometry.json').read_text())
    print({k:type(v).__name__ for k,v in d.items()})
    print({k:d[k][0] for k in ('tracks','vias','pads','footprints') if k in d})
    a=json.loads((HERE.parent/'native-198b-geometry/actual-via-flashes.json').read_text())
    print('ACTUAL',str(a)[:1800])
    lines=(ROOT/'reports/board-finish-20261011/parity-repair/root106/source/motherboard_power_entry.kicad_sch').read_text().splitlines()
    for i,line in enumerate(lines):
        if '"Reference" "C11088"' in line or '"Reference" "L11001"' in line:print('\n'.join(lines[i:i+5]))
if __name__=='__main__':main()
