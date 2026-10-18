"""One global area2 full-SIM2 map; exact qualified RAM/capture overlay."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'event-capture-global-area2-r7'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    source=H/'map_event_capture_full_r2.py';text=source.read_text()
    text=text.replace("OUT=HERE/'event-capture-select-r2/native-full-map'", "OUT=HERE/'event-capture-global-area2-r7/native-full-map'")
    marker="    initial=semantic(ET.parse(xml).getroot());shutil.copyfile(xml,OUT/'project-before.xml')"
    extra='''    tree=ET.parse(xml);ns={'e':'http://www.efinixinc.com/enf_proj'}
    syn=tree.getroot().find('e:synthesis',ns);assert syn is not None
    modes=[x for x in syn if x.attrib.get('name')=='mode'];assert len(modes)<=1
    mode=modes[0] if modes else ET.SubElement(syn,'{'+ns['e']+'}param')
    mode.attrib.update(name='mode',value='area2',value_type='e_option')
    ET.indent(tree);tree.write(xml,encoding='UTF-8',xml_declaration=True)
'''
    assert text.count(marker)==1;text=text.replace(marker,extra+marker)
    text=text.replace('full-SIM2-capture-map','full-SIM2-global-area2-map').replace('EXPLORATORY_NATIVE_SIM2_CAPTURE_MAP_COMPLETE_BEHAVIOR_AND_FIT_SEPARATE','EXPLORATORY_NATIVE_SIM2_GLOBAL_AREA2_MAP_COMPLETE_BEHAVIOR_AND_FIT_SEPARATE')
    text=text.replace("    assert all(sha(x['canonical'])", "    assert re.search(r'^mode\\s*:\\s*area2\\s*$',text,re.M)\n    assert all(sha(x['canonical'])")
    target=H/'map_global_area2_r7.py';assert not target.exists();target.write_text(text)
    record={'status':'ONE_GLOBAL_AREA2_NATIVE_MAP_PREPARED','qualified_packet_SHA256':sha(H/'event-capture-select-r2/reviewable-two-file-overlay-packet.json'),'source_runner_SHA256':sha(source),'derived_runner_SHA256':sha(target),'source_delta':False,'settings_delta':'global synthesis mode=area2 only; two CPUs/max_threads2 retained','setting_sweep':False,'adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
