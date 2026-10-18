"""Preserved R124 serializer failure; read-only result converts numpy count."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent
s=(H/'probe_owned_CORE_source_wall_precision_r124.py').read_text().replace("get_num_coordinates(s),","int(get_num_coordinates(s)),")
exec(compile(s,str(H/'probe_owned_CORE_source_wall_precision_r124.py'),'exec'))
