from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXT=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec')
sources=[ROOT/'gateware/rtl/cnc_stepgen.v',ROOT/'gateware/rtl/cnc_encoder.v',*sorted((ROOT/'gateware/v3/rtl').glob('*.v'))]
external=['cnc3/model/cnc3_model.c','cnc3/model/cnc3_model.h','cnc3/src/cnc3.c','cnc3/src/cnc3.h','docs/interface-spec/01-protocol-and-schedule.md','docs/interface-spec/04-safety-power-timing.md','docs/MOTION_EXPANSION_8_TO_12.md','spec/protocol.json','spec/safety.json']
rows=[]
for source in sources+[EXT/p for p in external]:
 kind='external' if source.is_relative_to(EXT) else 'workspace'
 relative=source.relative_to(EXT if kind=='external' else ROOT)
 dest=HERE/'inputs'/kind/relative
 if dest.exists():raise RuntimeError('Immutable input snapshot already exists')
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 rows.append({'kind':kind,'source':source.as_posix(),'snapshot':dest.relative_to(HERE).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(HERE/'inputs.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8',newline='\n')
print(len(rows),'actual immutable inputs snapshotted')
