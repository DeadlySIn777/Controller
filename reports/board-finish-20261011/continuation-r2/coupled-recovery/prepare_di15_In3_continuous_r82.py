from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;src=H/'diagnose_di15_zero_carve_regions_r78.py';b=src.read_bytes();s=b.decode().replace('r76','r80').replace('R76','R80').replace('r78','r82')
s=s.replace('b9b5d7bcf8939e409fb4dc69400a049cd2cb5fdf5d822ddf42c8aeeb6ed3d70c','7676af5a9fa3b96e966a378a0edbbdac1711dc3158f14d606a5fe84f1bc4f720')
s=s.replace('DI15_ZERO_POWER_CARVE_CONTINUOUS_PATH_NOMINATED_UNQUALIFIED','DI15_ZERO_POWER_CARVE_CONTINUOUS_ADJACENT_IN3_PATH_NOMINATED_UNQUALIFIED').replace('DI15_SAVED_CONTINUOUS_ENDPOINT_REGIONS_SPLIT_WITH_ALL_POWER_HARD','DI15_SAVED_CONTINUOUS_ADJACENT_IN3_REGIONS_SPLIT_ALL_POWER_HARD')
s=s.replace("'max_layer_segments':3", "'selected_In2_adjacent_reference_layer':'In3.Cu','reference_handoff_allowed':False,'max_layer_segments':3")
dst=H/'diagnose_di15_In3_continuous_regions_r82.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec');out=H/'prepare-di15-In3-continuous-r82.json';assert not out.exists();out.write_text(json.dumps({'source_sha256':hashlib.sha256(b).hexdigest(),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Same continuous endpoint-region probe bound to frozen R80 zero-power-carve In3 adjacent-reference cache.'},indent=1)+'\n');print(dst)
