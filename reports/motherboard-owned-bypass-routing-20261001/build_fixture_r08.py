from pathlib import Path
folder=Path(__file__).parent/'native-fixture-r08'
folder.mkdir()
text=(Path(__file__).parent/'native-fixture-r07/build_fixture.py').read_text()
assert 'SetDoNotAllowCopperPour' in text
(folder/'build_fixture.py').write_text(text.replace('SetDoNotAllowCopperPour','SetDoNotAllowZoneFills'))
