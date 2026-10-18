"""Preserve the queued test runner and create a separate shared-slot retry."""
from pathlib import Path

here = Path(__file__).resolve().parent
source = (here / 'measure_composite.py').read_text(encoding='utf-8')
assert source.count('"heavyt.sh"') == 2
assert source.count('test-kicad (one, isolated copy)') == 1
source = source.replace('"heavyt.sh"', '"heavy.sh"').replace(
    'test-kicad (one, isolated copy)', 'shared-kicad (one of two existing slots, isolated copy)')
target = here / 'measure_composite_shared.py'
assert not target.exists()
target.write_text(source, encoding='utf-8')
print(target)
