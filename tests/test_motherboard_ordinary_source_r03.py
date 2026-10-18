"""Actual native source26 exact digital allowlist and rejection controls."""
import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import hardware_build_ordinary_route_manifest_r03 as tool
ADOPTION=ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json'
class ActualOrdinarySourceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.source=self.base/'source';shutil.copytree(ROOT/'hardware/motherboard',self.source);self.accept=copy.deepcopy(tool.prior.baseline.load(ADOPTION));self.adoption=self.base/'adoption.json';self.write_adoption()
 def write_adoption(self,rehash=False):
  if rehash:self.accept['source_hashes']={str(p.relative_to(self.source)).replace('\\','/'):tool.prior.baseline.sha(p)for p in self.source.rglob('*')if p.is_file()}
  self.adoption.write_text(json.dumps(self.accept))
 def review(self):return tool.review(self.source,self.adoption)
 def test_exact112_current_native_functions(self):
  r=self.review();self.assertEqual(112,len(r['nets']));self.assertEqual(36,r['actual_status_intermediate_nodes_added']);self.assertFalse(r['routing_run'])
 def test_LED_current_paths_and_every_clock_remain_excluded(self):
  r=self.review();self.assertFalse(any(x.endswith(('_A','_K'))or 'DO_LED' in x or 'SCLK' in x or 'REFIO'in x or 'REFCAP'in x for x in r['nets']))
 def test_stale_source_hash_is_rejected(self):
  p=self.source/'design.json';p.write_text(p.read_text()+'\n')
  with self.assertRaises(ValueError):self.review()
 def test_no_independent_adoption_is_rejected(self):
  self.accept['independent_validation_pass']=False;self.write_adoption()
  with self.assertRaises(ValueError):self.review()
 def test_ignored_ERC_is_rejected(self):
  self.accept['ignored_checks']=['fake'];self.write_adoption()
  with self.assertRaises(ValueError):self.review()
 def test_wrong_actual_AHCT_gate_is_rejected(self):
  p=self.source/'design.json';d=json.loads(p.read_text());d['components']['U17001']['mpn']='SN74AHCT14PWR';p.write_text(json.dumps(d));self.write_adoption(True)
  with self.assertRaises(ValueError):self.review()
 def test_current_sink_output_cannot_replace_sink_input(self):
  p=self.source/'netlist.xml';tree=ET.parse(p);n=next(n for n in tree.findall('.//nets/net')if n.attrib['name']=='/motherboard_status/OBS0_INVERTED');next(z for z in n.findall('node')if z.attrib['ref']=='U17002').attrib['pin']='2';tree.write(p);self.write_adoption(True)
  with self.assertRaises(ValueError):self.review()
 def test_own_actual_ground_must_not_cross_field_domain(self):
  p=self.source/'netlist.xml';tree=ET.parse(p);n=next(n for n in tree.findall('.//nets/net')if any(z.attrib.get('ref')=='U17001'and z.attrib.get('pin')=='7'for z in n.findall('node')));node=next(z for z in n.findall('node')if z.attrib['ref']=='U17001'and z.attrib['pin']=='7');n.remove(node);next(x for x in tree.findall('.//nets/net')if x.attrib['name']=='/motherboard_analog_input/AI_AGND').append(node);tree.write(p);self.write_adoption(True)
  with self.assertRaises(ValueError):self.review()
if __name__=='__main__':unittest.main()
