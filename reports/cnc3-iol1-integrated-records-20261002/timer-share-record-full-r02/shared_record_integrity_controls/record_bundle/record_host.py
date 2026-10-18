"""Proposed IS2 one-motherboard region-record validator, no live hardware writes.

CRC and target UID binding detect corruption/mix-up. Only an explicitly supplied
trust registry plus real Ed25519 verification authenticates the signed record.
Fixture keys are marked developer-only and can never produce production trust.
No result grants ACTIVE, outputs, motion, compatibility or calibration accuracy.
"""
import hashlib,struct
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
POPULATION=bytes([12,4,24,16,2,2,2,2,4,15])
def crc32c(data):
 c=0xffffffff
 for b in data:
  c^=b
  for _ in range(8):c=(c>>1)^ (0x82f63b78 if c&1 else 0)
 return c^0xffffffff
def fixture_record(slot,uid,serial=b'DEVELOPMENT-ONLY',generation=1,source_sha=bytes(32),private=None):
 """Explicit disconnected test fixture, never a real provisioned-board record."""
 if private is None:private=Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
 if not(0<=slot<=3 and len(uid)==12 and 0<len(serial)<=16 and 1<=generation<=0xffffffff):raise ValueError('fixture bounds')
 p=bytearray(b'\xff'*512);p[:4]=b'MBR2';p[4:12]=bytes([2,[0x11,0x21,0x21,0x31][slot],slot,1,0,1,2,0]);p[12:16]=struct.pack('>I',generation)
 p[16:32]=serial.ljust(16,b'\0');p[32:44]=uid;p[44:56]=struct.pack('>HBBHHHH',2,3,3,1,1,3,3)
 p[56:66]=POPULATION;p[66:68]=b'\0\0';p[68:100]=source_sha
 for off,name in [(100,b'fixture-calibration'),(132,b'fixture-factory-test'),(164,b'fixture-firmware')]:p[off:off+32]=hashlib.sha256(name).digest()
 pub=private.public_key().public_bytes_raw();p[196:212]=hashlib.sha256(pub).digest()[:16]
 p[440:504]=private.sign(bytes(p[:440]));p[504:508]=struct.pack('>I',crc32c(p[:504]));p[508:]=b'CMT2'
 return bytes(p),{p[196:212].hex():{'public_key':pub.hex(),'environment':'developer-fixture'}}
def validate_record(p,slot,uid,registry=None,source_sha=None,firmware_version=1,gateware_version=3):
 """Full structural plus signature validation; default trust set is empty."""
 if type(slot) is not int or not 0<=slot<=3:raise ValueError('fitted slot must be0..3')
 if not isinstance(uid,(bytes,bytearray,memoryview)) or len(uid)!=12:raise ValueError('actual MCU UID must be12bytes')
 result={'integrity_valid':False,'signature_verified':False,'production_trusted':False,'ACTIVE_or_authority':False}
 if len(p)!=512:raise ValueError('length')
 if p[:4]!=b'MBR2' or p[4]!=2 or p[5]!=[0x11,0x21,0x21,0x31][slot] or p[6]!=slot or p[7]>15 or p[9:12]!=bytes([1,2,0]):raise ValueError('header')
 if int.from_bytes(p[12:16],'big')==0 or p[32:44]!=uid:raise ValueError('generation/UID')
 serial=p[16:32].split(b'\0')[0]
 if not serial or any(x<33 or x>126 for x in serial) or p[16:32]!=serial.ljust(16,b'\0'):raise ValueError('serial')
 if int.from_bytes(p[44:46],'big')==0 or not p[46]<=3<=p[47] or p[56:66]!=POPULATION or p[66:68]!=b'\0\0':raise ValueError('topology')
 if not int.from_bytes(p[48:50],'big')<=firmware_version<=int.from_bytes(p[50:52],'big') or not int.from_bytes(p[52:54],'big')<=gateware_version<=int.from_bytes(p[54:56],'big'):raise ValueError('software compatibility')
 if p[212:440]!=b'\xff'*228 or p[508:]!=b'CMT2' or int.from_bytes(p[504:508],'big')!=crc32c(p[:504]):raise ValueError('integrity/commit')
 if source_sha is not None and p[68:100]!=source_sha:raise ValueError('source provenance')
 result['integrity_valid']=True;result['board_serial']=serial.decode('ascii');result['slot']=slot;result['generation']=int.from_bytes(p[12:16],'big');result['hardware_major']=p[7]
 key=(registry or {}).get(p[196:212].hex())
 if key is None:result['reason']='untrusted-key';return result
 pub=bytes.fromhex(key['public_key'])
 if hashlib.sha256(pub).digest()[:16]!=p[196:212]:raise ValueError('key registry fingerprint')
 try:Ed25519PublicKey.from_public_bytes(pub).verify(p[440:504],p[:440])
 except InvalidSignature:raise ValueError('signature')
 result['signature_verified']=True
 # No manufacturer trust-root provisioning exists in this staged prototype.
 # Renaming a test key/environment cannot manufacture production provenance.
 result['production_trusted']=False
 result['reason']='signature under explicitly supplied key only; production trust-root/attestation unimplemented'
 return result
def validate_four_region_set(records,uids,registry=None,source_sha=None):
 if len(records)!=4 or len(uids)!=4 or len(set(uids))!=4:raise ValueError('four unique fitted MCU regions required')
 rows=[validate_record(p,i,uids[i],registry,source_sha) for i,p in enumerate(records)]
 # All actual regions share the BOARD lineage, not fabricated card serials.
 for i in range(1,4):
  for a,b in [(16,32),(44,48),(56,100)]:
   if records[i][a:b]!=records[0][a:b]:raise ValueError('mixed motherboard/source/topology')
 return {'regions':rows,'same_motherboard':True,'all_signatures_verified':all(r['signature_verified'] for r in rows),'production_trusted':all(r['production_trusted'] for r in rows),'ACTIVE_or_authority':False}
