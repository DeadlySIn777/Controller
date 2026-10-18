# Disconnected pre-hardware validation

Overall: **BLOCKED**. Manufacturing ready: **false**.

| Stage | Status | Exact evidence class | Boundary |
|---|---|---|---|
| cnc3_actual_rtl_transport | BLOCKED | REAL_LINUXCNC_CNC3_ACTUAL_RTL | Bounded CNC3 structural RTL transport/codec now exists separately; complete stateful endpoint, HAL/Verilated integration and full machine profile remain absent |
| twelve_joint_simultaneous_machine | BLOCKED | SIMULATED_FULL_MACHINE | No integrated twelve-joint CNC3/RTL/mechanics/encoder/full-I/O machine; standalone step generators do not implement it |
| critical_circuit_spice_corners | BLOCKED | SPICE_CORNER_MONTE_CARLO | No selected-part-complete SPICE benches/models; ngspice availability alone would not qualify them |
| efinity_vendor_fit_timing | BLOCKED | VENDOR_PLACEMENT_ROUTE_STATIC_TIMING | No qualified Efinity project/license/actual source/pin-bank/timing flow; Yosys family synthesis is separate |
| simultaneous_full_load | BLOCKED | LOADED_TARGET_REALTIME | No complete target machine coupled to UI/network/ESP/I/O/analog/fieldbus loads; host tests do not prove servo jitter |
| signal_integrity_and_cables | BLOCKED | IBIS_ROUTED_SI | Routing/stackup/process/receiver/cable models and loaded timing remain unqualified |
| thermal_current_qualification | BLOCKED | ELECTROTHERMAL_MODEL | No complete guaranteed load/copper/contact/enclosure model or physical thermal measurements |
| full_setup_operator_workflow | BLOCKED | END_TO_END_UI_MACHINE | Existing host supervisor/configuration cases do not implement provisioning/CAD registration/homing/machining/recovery of every proposed machine |
| physical_qualification | NOT_RUN | PHYSICAL_MEASUREMENT | No assembled prototype; no physical electrical/EMC/temperature/20ms measurements |
| host_suite | PASS | HOST_UNIT_CONTRACT_TEST | Fresh command and exact artifact checked |
| native_test_replay | PASS | NATIVE_KICAD_TEST | Fresh command and exact artifact checked |
| native_source_validation | PASS | SOURCE_PIN_MPN_FOOTPRINT_CHECK | Fresh command and exact artifact checked |
| native_ERC | PASS | NATIVE_KICAD_ERC | Regular ERC violations: {'warning': 70}; all warnings/ignored-check records retained; full routing requires uncapped independent connectivity |
| native_DRC | PASS | NATIVE_KICAD_DRC | Regular DRC violations: {}; all warnings/ignored-check records retained; full routing requires uncapped independent connectivity |
| source_physical_connectivity | PASS | NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT | Fresh command and exact artifact checked |
| complete_PCB_routing | BLOCKED | NATIVE_PHYSICAL_CONNECTIVITY | 3524 uncapped Source-cluster joins remain; independent integrity PASS |
| watchdog_RTL | PASS | RTL_SIMULATION_LINT_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| IOL1_target | PASS | ARM_TARGET_COMPILE_HOST_C_RTL_VPI_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| isolated_stepgen12_sweep | PASS | ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP | Fresh command and exact artifact checked |
| isolated_stepgen12_dynamic | PASS | ACTUAL_RTL_DYNAMIC_COMPONENT_TEST | Fresh command and exact artifact checked |
| isolated_encoder4_sweep | PASS | ACTUAL_RTL_IDEAL_DIGITAL_COMPONENT_SWEEP | Fresh command and exact artifact checked |
| cnc3_layout_contract | PASS | GENERATED_C_PROTOCOL_LAYOUT_CHECK | Fresh command and exact artifact checked |
| cnc3_host_model | PASS | HOST_C_MODEL_ASAN_UBSAN | Fresh command and exact artifact checked |
| cnc3_structural_RTL | PASS | ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| historical_linuxcnc_six_two | PASS | REAL_LINUXCNC_VERILATED_CNC1 | Fresh command and exact artifact checked |
| supervisor_fault_scenarios | PASS | HOST_SUPERVISOR_MODEL | Fresh command and exact artifact checked |
| input_integrity | PASS | EXACT_SOURCE_HASHES | Scoped source and frozen PCB hashes retained |

Numerical production ratings remain null where complete chain/corners/fit/final-route qualification is absent. Host/model, actual RTL, target compilation, real LinuxCNC, native ERC/DRC and physical measurement are separate.
