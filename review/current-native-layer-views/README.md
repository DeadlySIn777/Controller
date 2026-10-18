# Current native board layer views

These views come from KiCad 10.0.7 plotting the exact current global-input PCB `a693477c5a71e26db86345ea2a356ad20519d301989d2f0e3506a8142f23c595`. All 211 frozen native project files remain unchanged after export. The current complete editable source is [the project ZIP](../../archives/joint-global-R3-exact-native-project.zip).

Orange overlays are the 238 source power-planning reservation outlines, including their holes. Magenta overlays are the literal native track keepouts on each layer. This overview omits conditional foreign-net-only restrictions and clearance-expanded router guards; use the exact DSN/rules for decisions. The source planning outlines are unchanged between the joint 2e93 source and current a693 composition.

The underlying copper is the saved cache, not a fresh filled AFTER. All 849 new source zones and eight modified original zones lack current filled caches. Apparent blank space is therefore not proof of legal routing space or an intact return plane. The front/back source power reservations are overlaid explicitly so they are not mistaken for empty signal corridors. In3 has no new power-reservation polygons in this source; it still has native keepouts, existing copper, via clearances and return-path requirements.

The images show uneven congestion, not uniform physical occupancy. This supports testing a correctly constrained global router before wholesale placement changes; it does not prove that every remaining connection is routable. Native full refill, connectivity gain/loss, DRC, paired geometry, current/return/thermal/SI, assembly and physical FPGA implementation remain open. No new join reduction or manufacture readiness is claimed.

- [Front copper with planning overlay](planning-F_Cu.png)
- [Inner signal layer In3](planning-In3_Cu.png)
- [Back copper with planning overlay](planning-B_Cu.png)

Native SVG export peaked at 64.2% sampled total CPU; raster and corrected-font overlay renders peaked at 50.5% and 53.3%, with no samples at or above 80% in these specific jobs. Other jobs have recorded breaches, so this is not a claim of continuous whole-session compliance.
