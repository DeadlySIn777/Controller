"""Attribute every remaining R429 strict gap to actual source/fill pieces."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'diagnose_FIELD5_R393_retained_reference_source_membership_r409.py').read_text(encoding='utf-8')
s=s.replace("R=H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395'", "R=H/'FIELD5-R423-original-rim-fresh-drilled-source-reference-gate-r429';OLD=H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395'")
s=s.replace("M=H/'FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393/model.pkl'", "M=H/'FIELD5-R385-minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423/model.pkl'")
s=s.replace('FIELD5-R393-retained-reference-restored-source-membership-diagnosis-r409','FIELD5-R423-remaining-strict-reference-rim-attribution-r431')
s=s.replace("=='670c62f794e68f7e6a6bbd25fb5d0b5b59f18c3fea076aef76009bb1dd789303'", "=='2e98e8a8fd920f07cd32e0697e1f1694d5a4d52ad0722e21df8c628fed029d85'")
s=s.replace("old=pickle.loads((R/'actual-drilled-before-groups.pkl').read_bytes());new=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes())", "old=pickle.loads((OLD/'actual-drilled-before-groups.pkl').read_bytes());new=pickle.loads((R/'actual-checked-four-net-groups.pkl').read_bytes())")
s=s.replace("json.loads((R/'three-bank-strict-zero-reference-rows.json').read_text())", "json.loads((R/'receipt.json').read_text())['rows']")
s=s.replace("bank['strict_ZERO_retained_old_reference_losses']", "bank['old_strict_zero_reference_losses']")
s=s.replace("'R393_model_sha256'", "'R423_model_sha256'")
s=s.replace("'R395_receipt_sha256'", "'R429_receipt_sha256'")
s=s.replace("'raw_R395_loss_mm2'", "'raw_R429_loss_mm2'")
s=s.replace("'gap_bounds_mm':None if gap.is_empty else gap.bounds", "'gap_bounds_mm':None if gap.is_empty else gap.bounds,'gap_geometry_type':gap.geom_type,'all_source_fill_overlap_mm2':gap.intersection(unary_union([r['shape']for r in nr if r['kind']=='fill'and r['layer']==inner])).area")
exec(compile(s,str(H/'diagnose_FIELD5_R393_retained_reference_source_membership_r409.py'),'exec'))
