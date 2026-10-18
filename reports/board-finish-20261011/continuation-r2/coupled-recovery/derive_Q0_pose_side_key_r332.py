from pathlib import Path
H=Path(__file__).resolve().parent;dst=H/'nominate_Q0_R10016_source_pose_r332.py';assert not dst.exists();s=(H/'nominate_Q0_R10016_source_pose_r330.py').read_text().replace("'F.CrtYd'","'F'").replace('nomination-r330','nomination-r332');dst.write_text(s,encoding='utf-8',newline='\n')
