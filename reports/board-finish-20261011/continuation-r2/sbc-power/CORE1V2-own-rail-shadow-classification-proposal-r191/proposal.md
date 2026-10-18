The saved continuous-reference requirement names high-speed signals. The exact source shows CORE_1V2 is FPGA core/PLL power, and the historical checker conservatively applies its signal-shadow test to every same-domain non-ground conductor. The literal same-rail B power rows are candidates for a separate PDN qualification; their lost-shadow measurements remain recorded and no row is exempted here.

TI requires close bypass capacitors, low-inductance high-current loops and quiet short sense connections. A same-rail plane can improve supply conductance, but does not prove the ground-return loop, dynamic impedance or decoupling performance. Each actual power branch requires the explicit source/return/current/stability obligations in receipt.json. Actual control, fault, clock and sense paths keep their strict reference requirements.

No circuit, geometry, source, audit result or manufacturing gate is changed by this proposal.
