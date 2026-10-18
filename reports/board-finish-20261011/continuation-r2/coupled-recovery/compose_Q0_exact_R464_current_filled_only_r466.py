"""Immutable-filled-only composition of the reserve-safe exact sparse packet."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'compose_Q0_exact_R452_current_filled_only_r454.py'
code=base.read_text().replace('Q0-exact-R452-current-filled-only-r454','Q0-exact-R464-current-filled-only-r466').replace('Q0-R450-exact-native-owned-operation-r452','Q0-R460-exact-native-owned-operation-r464').replace('ed12eb485bd83caef6632d6d7aaf35bbddf18b06b4dbe277c34447b76bee030e','3f69aef00ad31bc5bcff19bc1ce80aec1f8afb1efe6fa1d05e08e5d993017e9c').replace('9c56a850a48dca1f08eadab78db04d3ac41c8b7eeab8d614a41d77f087a84b11','3f64ad79fd292c54bca3f25457215b4a25789a09b888f795e1788f6e9eb98d14').replace('source_R452_receipt_sha256','source_R464_receipt_sha256')
exec(compile(code,str(base),'exec'))
