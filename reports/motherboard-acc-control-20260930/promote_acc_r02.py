"""Bounded archived ACC GPIO update for two real readback-capable AO DACs."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[2];archive=Path(__file__).resolve().parent/'r02-ao-spi-correction'/'prior48-inputs';archive.mkdir(parents=True,exist_ok=True)
if 'motherboard-acc-control-r0.2' in (root/'tools/hardware_build_motherboard_acc_control.py').read_text(encoding='utf-8'):raise SystemExit('Already promoted; prior48 archive is immutable. Use the native builder for subsequent regeneration.')
inputs=list((root/'hardware/motherboard_acc_control').rglob('*'))+[root/'tools/hardware_build_motherboard_acc_control.py',root/'tools/hardware_validate_motherboard_acc_control.py',root/'tests/test_motherboard_acc_control.py']
hashes={}
for p in inputs:
 if p.is_file():
  rel=p.relative_to(root);q=archive/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);hashes[str(rel).replace('\\','/')]=hashlib.sha256(p.read_bytes()).hexdigest()
(archive.parent/'prior48-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
p=root/'tools/hardware_build_motherboard_acc_control.py';s=p.read_text(encoding='utf-8')
s=s.replace("('PB8','AO_I2C_SCL_HOST'),('PB9','AO_I2C_SDA_HOST')","('PB8','AO_I2C_SCL_HOST'),('PB9','AO_I2C_SDA_HOST'),('PB3','AO0_CS_N_HOST'),('PB4','AO1_CS_N_HOST')")
s=s.replace(" res('AI_CS_N_HOST','IO_3V3',10000,'unprogrammed MCU deselects isolated AI ADC')"," for net in ['AI_CS_N_HOST','AO0_CS_N_HOST','AO1_CS_N_HOST']:res(net,'IO_3V3',10000,'unprogrammed MCU deselects each independently isolated ADC/DAC')")
s=s.replace("'AI_SDO_HOST','AO_I2C_SCL_HOST'","'AI_SDO_HOST','AO0_CS_N_HOST','AO1_CS_N_HOST','AO_I2C_SCL_HOST'")
s=s.replace('motherboard-acc-control-r0.1','motherboard-acc-control-r0.2')
s=s.replace("'AI_SPI2':{'PB12':'softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'}","'AI_AO_SPI2':{'PB12':'AI_softwareCS','PB3':'AO0_softwareCS','PB4':'AO1_softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'}")
old="'DAC_readback_plan':{'interface':'I2C','DAC80501_SPI_has_no_SDO':True,'asynchronous_update_required':True,'readback_is_buffer_register_not_measured_VOUT':True,'native_frontend_implemented':False}"
new="'DAC_readback_plan':{'interface':'SPI2','selected_DAC':'AD5683RBRMZ-3','DAC80501_SPI_has_no_SDO':True,'asynchronous_update_required':True,'LDAC_tied_LOW':True,'readback_is_buffer_register_not_measured_VOUT':True,'independent_internal_DAC_latch_readout':False,'actual_terminal_monitor':'ADS1115IDGSR on isolated I2C1','native_frontend_implemented':True,'target_firmware_implemented':False}"
assert old in s;s=s.replace(old,new).replace('(rev "r0.1")','(rev "r0.2")');p.write_text(s,encoding='utf-8')
p=root/'tools/hardware_validate_motherboard_acc_control.py';s=p.read_text(encoding='utf-8')
s=s.replace("'PB9':'AO_I2C_SDA_HOST'}","'PB9':'AO_I2C_SDA_HOST','PB3':'AO0_CS_N_HOST','PB4':'AO1_CS_N_HOST'}")
s=s.replace('==48 and d[\'purchased_fitted_parts\']==42','==50 and d[\'purchased_fitted_parts\']==44').replace('48 physical/42 purchased/6 bare pads','50 physical/44 purchased/6 bare pads').replace('==155','==159').replace('155 exact electrical pads','159 exact electrical pads').replace("'R':30","'R':32")
s=s.replace("'AI_SPI2':{'PB12':'softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'}","'AI_AO_SPI2':{'PB12':'AI_softwareCS','PB3':'AO0_softwareCS','PB4':'AO1_softwareCS','PB13':'SCK_AF0','PB14':'MISO_AF0','PB15':'MOSI_AF0'}")
s=s.replace("('AI_CS_N_HOST','IO_3V3'),","('AI_CS_N_HOST','IO_3V3'),('AO0_CS_N_HOST','IO_3V3'),('AO1_CS_N_HOST','IO_3V3'),")
s=s.replace("{'interface':'I2C','DAC80501_SPI_has_no_SDO':True,'asynchronous_update_required':True,'readback_is_buffer_register_not_measured_VOUT':True,'native_frontend_implemented':False}",new.split(':',1)[1])
s=s.replace("'physical_footprints':48,'purchased_fitted_parts':42","'physical_footprints':50,'purchased_fitted_parts':44").replace("'electrical_pads':155","'electrical_pads':159")
p.write_text(s,encoding='utf-8')
p=root/'tests/test_motherboard_acc_control.py';s=p.read_text(encoding='utf-8')
s=s.replace("def test_no_invented_DAC_SPI_readback(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('interface','SPI'))","def test_no_invented_DAC_SPI_readback(self):self.changed(lambda d:d['DAC_readback_plan'].__setitem__('selected_DAC','DAC80501ZDQFR'))")
s=s.replace("d.__setitem__('purchased_fitted_parts',48)","d.__setitem__('purchased_fitted_parts',50)")
p.write_text(s,encoding='utf-8')
print(json.dumps({'prior48_archived_files':len(hashes),'new_GPIO':['PB3','PB4'],'scope':'two real AO SPI chip-selects plus pullups; no removed MCU or extra feature'}))
