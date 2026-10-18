from pathlib import Path
import json,hashlib
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-health-composition-inputs-r01');assert not O.exists();O.mkdir()
for owner,folder in [('U20','ROOT94-health-U20-control-A-r236'),('U26','ROOT94-health-U26-cell-Source-pending-r235')]:
 p=Path('reports/motherboard-power-entry-20261001')/folder/'bounded-scope.json';j=json.loads(p.read_text());j['reviewed_scope_reason']='Compose exact frozen '+owner+' Source-preserving receiving-cell physical transaction against adopted ROOT101; actual controls/contacts are Source-connected, receiving Source Ground/reference remains explicitly pending native field/control collar closure. No Source27 adoption, manufacturing or measured20ms claim.';j['frozen_original_peer_scope_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();(O/(owner+'-scope.json')).write_text(json.dumps(j,indent=2)+'\n')
