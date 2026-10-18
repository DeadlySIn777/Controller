"""Derive fresh bounded nominees; preserve all previous artifacts."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
src=H/'construct_di15_original_boundary_detour_r66.py'
b=src.read_bytes()
assert hashlib.sha256(b).hexdigest()=='1cf771efa34fe6615a4f297700cd0dbed9a6c48108da440c8acb66a44967014b'
s=b.decode().replace("RELEASE={'84b085e3-5361-596d-bea3-6b51cc9bcfb3','882c6aaa-4aa1-5c66-b57e-a1a963dc3817'}","RELEASE=set()")
s=s.replace('r66','r76').replace('R66','R76')
s=s.replace('Potential new In1 ground may carve only the two explicitly owned proposals;', 'Potential new In1 ground keeps every original and proposed power plane hard;')
s=s.replace('DI15_CONCRETE_NEIGHBOR_VOID_AVOIDING_IN2_PATH_NOMINATED_UNQUALIFIED_SUPPLY_CORRECTIONS_OPEN','DI15_ZERO_POWER_CARVE_IN2_PATH_NOMINATED_SOURCE_REFERENCE_CONSTRUCTION_OPEN')
s=s.replace('DI15_NEIGHBOR_VOID_DETOUR_INCOMPLETE','DI15_ZERO_POWER_CARVE_SAVED_TWO_SITE_DETOUR_INCOMPLETE')
dst=H/'construct_di15_zero_power_carve_detour_r76.py'
assert not dst.exists()
dst.write_text(s)
out=H/'prepare-di15-zero-carve-r76.json'
assert not out.exists()
out.write_text(json.dumps({'source':str(src),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':str(dst),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'Only release set is empty, separate filenames/verdict; all saved physical/source/old native foreign-fill predicates retained. Neither original nor owned proposed power plane is released.'},indent=1)+'\n')
print(dst)
