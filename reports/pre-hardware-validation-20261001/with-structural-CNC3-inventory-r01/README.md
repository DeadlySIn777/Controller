# Disconnected pre-hardware validation

Overall: **NOT_RUN**. Manufacturing ready: **false**.

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
| host_suite | NOT_RUN | HOST_UNIT_CONTRACT_TEST | Inventory mode did not execute validation |
| native_source_validation | NOT_RUN | SOURCE_INSPECTION | Inventory mode did not execute validation |
| native_test_replay | NOT_RUN | NATIVE_KICAD_TEST | Inventory mode did not execute validation |
| native_ERC | NOT_RUN | NATIVE_KICAD_ERC | Inventory mode did not execute validation |
| native_DRC | NOT_RUN | NATIVE_KICAD_DRC | Inventory mode did not execute validation |
| source_physical_connectivity | NOT_RUN | NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT | Inventory mode did not execute validation |
| complete_PCB_routing | NOT_RUN | NATIVE_PHYSICAL_CONNECTIVITY | Inventory mode did not execute validation |
| historical_linuxcnc_six_two | NOT_RUN | REAL_LINUXCNC_CNC1 | Inventory mode did not execute validation |
| cnc3_host_model | NOT_RUN | HOST_C_MODEL | Inventory mode did not execute validation |
| cnc3_layout_contract | NOT_RUN | GENERATED_C_PROTOCOL_LAYOUT_CHECK | Inventory mode did not execute validation |
| watchdog_RTL | NOT_RUN | RTL_SIMULATION_LINT_FAMILY_SYNTHESIS | Inventory mode did not execute validation |
| cnc3_structural_RTL | NOT_RUN | ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS | Inventory mode did not execute validation |
| isolated_stepgen12_sweep | NOT_RUN | ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP | Inventory mode did not execute validation |
| supervisor_fault_scenarios | NOT_RUN | HOST_SUPERVISOR_MODEL | Inventory mode did not execute validation |
| IOL1_target | NOT_RUN | TARGET_COMPILATION | Inventory mode did not execute validation |
| isolated_stepgen12_dynamic | NOT_RUN | ACTUAL_RTL_DYNAMIC_COMPONENT_TEST | Inventory mode did not execute component validation |
| isolated_encoder4_sweep | NOT_RUN | ACTUAL_RTL_IDEAL_DIGITAL_COMPONENT_SWEEP | Inventory mode did not execute component validation |
| input_integrity | PASS | EXACT_SOURCE_HASHES | Scoped source and frozen PCB hashes retained |

Numerical production ratings remain null where complete chain/corners/fit/final-route qualification is absent. Host/model, actual RTL, target compilation, real LinuxCNC, native ERC/DRC and physical measurement are separate.
