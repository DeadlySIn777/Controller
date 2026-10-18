# Fitted-target diagnostic IOL1 revision

`cnc_motherboard_iol1_target_bringup` preserves the previous safe-output wrapper and historical motion endpoint. Its four independent `cnc_iol1_readonly_target_master` instances add20us setup/5us hold and a truthful ACC held-reset health branch: zero unavailable analog payload, ageFFFF, AI-valid0 and clamp-control bits03. It does not accept synthetic DAC-readback bits0F or a falsely fresh ADC age under reset. All process/DO/PWM/AO authority remains LOW. Startup peers can remain INIT/unavailable without granting authority; after qualification, three failed replies latch that port and stop complete-cycle O progress.

The test uses the actual target protocol C through VPI and explicit disconnected GPIO/driver fixtures. It does not execute ARM target DMA/IRQ code, analog converters or actual watchdog ICs. Historical60-check synthetic-peer tests remain byte-preserved in the earlier directory and are rerun separately. All accepted M/O pulses are idleLOW, HIGH for exactly1us. The motion portion remains the historical six-axis/two-encoder diagnostic path, not production12axis.

The physical FPGA ports/pins are unchanged from the reviewed fitted watchdog pin map; four PB5 count taps affect only MCU-side inputs. Actual FPGA vendor package fit, clock constraints, timing closure, bitstream and loaded physical qualification are still required.
