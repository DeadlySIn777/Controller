"""Record the exact bounded peer inspection separately from actual simulation."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'peer-scope-cold-state-review-r01'
assert not OUT.exists()
OUT.mkdir()
files = [ROOT / 'gateware/v3/rtl/cnc3_spi_transport.v', ROOT / 'gateware/v3/rtl/cnc3_frame_endpoint.v']
receipt = {
    'status': 'PASS', 'evidence_type': 'INDEPENDENT_SOURCE_INSPECTION_ONLY',
    'reviewer': '/root/motherboard_contract',
    'recorded_utc': datetime.now(timezone.utc).isoformat(),
    'source_hashes': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    'review_text': 'Read-only final CNC3 cold-state/scope review found no additional actionable issue in the current transport/endpoint. Reset clears request_valid/frame_valid/data/MISO and MISO OE is physically disabled by rst_n; opposite-CS start is now explicitly rejected at release, both-select is rejected, overflow saturates into invalid, and queue overrun cannot replace a pending unconsumed request. This is source inspection corroborating your tests only, not stateful authority/vendor fit/physical timing proof. Shared inputs remain unchanged.',
    'independent_review_caught_prior_handoff_defect': True,
    'actual_compiled_handoff_mutation_receipt': 'reports/cnc3-rtl-implementation-20261001/mutation-controls-r03/receipt.json',
    'stateful_authority_proved': False, 'vendor_fit_timing_proved': False,
    'physical_timing_proved': False,
}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
