"""Move only the unaccepted Q0 source out of the exact SBC5V reserve."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_saved_GATE_SENSE_existing_barrels_r450.py'
code=base.read_text().replace('Q0-saved-GATE-SENSE-existing-barrels-r450','Q0-GATE-SENSE-reserve-safe-source-r460').replace('[229.15,156.57]','[228.95,156.95]')
exec(compile(code,str(base),'exec'))
