import json,hashlib
from pathlib import Path
p=Path("/root/.cache/controller-lab-linuxcnc/rootfs/usr/lib/linuxcnc/modules")
print(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.glob("*.so"))},indent=2))
