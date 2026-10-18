# Current motherboard diagnostic gateware

This separate bring-up target preserves the historical six-axis/two-encoder CNC1 endpoint and its evidence. It implements the fitted TPS3851 waveform: one 50-clock HIGH pulse followed by LOW per accepted ARM/UPDATE, and a distinct output-domain pulse only after all four physical IOL1 links return a complete, validated response in the same polling cycle.

The IOL1 masters send SYNC and zero-output diagnostic commands. They never assert OUT_REQ, FPGA_OUTPUT_REQUEST, process commands, PWM, analog enable or an output-enable strobe. Unprogrammed, absent, stale, corrupt or faulted acquisition MCUs cannot produce a useful-progress pulse. A missing target IOL1 firmware remains a real bring-up dependency. Epoch is a nonzero build/provisioning input; every link restart must use a new value. This image does not implement commercial commissioning, identity/configuration acceptance, watchdog self-test or twelve-axis runtime authority.

The current bench target has six active motion generators and two encoders. Motors 6–11 have STEP/DIR LOW and individual EN_N HIGH. This does not prove twelve coordinated axes. Vendor placement, pin constraints, clock timing and physical watchdog/partial-power qualification remain separate gates.
