"""Freeze the reserve-safe Q0 source recipe, with all open gates retained."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'freeze_Q0_R450_exact_native_operation_r452.py'
code=base.read_text().replace('Q0-R450-exact-native-owned-operation-r452','Q0-R460-exact-native-owned-operation-r464').replace('Q0-saved-GATE-SENSE-existing-barrels-r450','Q0-GATE-SENSE-reserve-safe-source-r460').replace('681b07ace4dad300c507f1992e327ab4cfc17a1c73608edf27067054599adc8b','3d4eee7be4b8f6edfeee68ebec7b59404070263132ae382fbdb2eb65c794f0fb').replace('R450_nomination_receipt_sha256','R460_nomination_receipt_sha256')
exec(compile(code,str(base),'exec'))
