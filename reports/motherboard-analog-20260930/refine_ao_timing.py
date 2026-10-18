from pathlib import Path
p=Path(__file__).resolve().parents[2]/'tools/hardware_build_motherboard_analog_output.py'
s=p.read_text(encoding='utf-8')
s=s.replace("'wire_time_only':{'spi_hz':8000000,'clocks_two_writes_and_two_readbacks':144,'seconds':18e-6,'not_full_commit_latency_proof':True}","'wire_time_only':{'spi_hz':4000000,'two_write_clocks':48,'apply_write_seconds':12e-6,'two_readback_clocks':96,'readback_seconds':24e-6,'combined_seconds':36e-6,'readback_is_not_part_of_20us_apply_allocation':True,'not_full_commit_latency_proof':True}")
s=s.replace("'dac_register_readback':True","'input_register_readback':True,'LDAC_LOW_copies_input_to_DAC':True,'no_independent_internal_DAC_latch_readout':True")
s=s.replace('8MHz 144clocks=18us is wiretime only; isolation round-trip/CS gaps/MCU scheduling and frozenwhole160.4uscommit require loaded proof.','4MHz twoDACwrites=12us wiretime within20usapply; twoinputreadbacks=24us separate,36uscombined within59.6usprocessing window. Isolation round-trip/CS gaps/MCU scheduling and frozenwhole160.4uscommit require loaded proof.')
p.write_text(s,encoding='utf-8')
