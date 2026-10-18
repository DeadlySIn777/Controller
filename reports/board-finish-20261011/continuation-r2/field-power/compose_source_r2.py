"""R2 combined source uses bias-screened C95; preserve r1 composition and proofs."""
from pathlib import Path
import compose_source as M
text=Path(M.__file__).read_text(encoding='utf-8')
text=text.replace("combined-power-source-r1", "combined-power-source-r2")
text=text.replace("ab-local-bypass-source'", "ab-local-bypass-source-r2'")
text=text.replace("root106-combined-power-owned-source-r1", "root106-combined-power-owned-source-r2")
exec(compile(text,M.__file__,'exec'),dict(M.__dict__,__name__='__main__'))
