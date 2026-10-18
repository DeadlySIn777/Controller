"""Render frozen r06 source copper, local landing regions and component poses."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import shape, box
import prepare_sbc_plan as source

HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "sbc-root106-plan.json").read_text())
geometry = json.loads(source.GEOM.read_text())
if geometry["sha256"] != source.BASE_SHA or source.sha(source.BASE) != source.BASE_SHA:
    raise ValueError("source geometry changed")
window = box(213, 130, 228, 144)
fig, ax = plt.subplots(figsize=(12, 10))
def draw(polygon, colour, alpha=1, edge=None):
    for part in [polygon] if polygon.geom_type == "Polygon" else getattr(polygon, "geoms", []):
        if part.geom_type != "Polygon":
            continue
        if part.intersects(window):
            ax.add_patch(Patch(list(part.exterior.coords), closed=True, facecolor=colour, edgecolor=edge or colour, alpha=alpha, lw=0.5))
            for hole in part.interiors:
                ax.add_patch(Patch(list(hole.coords), closed=True, facecolor="white", edgecolor="white", lw=0.5))
draw(shape(plan["source_array_screen"]["front_source_component"]), "#b5ddba", 0.65)
draw(shape(plan["source_array_screen"]["via_landing_region"]), "#2677bd", 0.8)
for track in geometry["tracks"]:
    if track["layer"] == "F.Cu":
        draw(source.body(track), "#006e36" if track["net"] == source.NET else "#b0b0b0", 0.65)
for pad in geometry["pads"]:
    for polygon in source.polygons(pad["layers"].get("F.Cu", [])):
        draw(polygon, "#007a37" if pad["net"] == source.NET else "#7f7f7f", 0.9)
    for polygon in source.polygons(pad["layers"].get("B.Cu", [])):
        draw(polygon, "none", 1, "#b43c99")
for footprint in geometry["footprints"]:
    if footprint["ref"] in {"U11012", "C11061", "C11062", "C11063", "C11059", "U11011"}:
        ax.text(footprint["x"], footprint["y"], footprint["ref"], fontsize=9, bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
        for records in footprint["courtyard"].values():
            for polygon in source.polygons(records):
                draw(polygon, "none", 1, "#ba8400")
ax.set_xlim(213, 228); ax.set_ylim(144, 130)
ax.set_aspect("equal"); ax.grid(alpha=0.2)
ax.set_xlabel("board x (mm)"); ax.set_ylabel("board y (mm)")
ax.set_title("r06 SBC source: existing F copper (grey/green), B pads (magenta),\nsource-connected front free region (light green), all-layer via landing (blue)\nHost geometry planning only; source/load current and native gates open")
fig.tight_layout()
fig.savefig(HERE / "sbc-source-bottleneck.png", dpi=160)
plt.close(fig)
