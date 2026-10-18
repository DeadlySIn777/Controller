# Disconnected pre-hardware validation

Overall: **BLOCKED**. Manufacturing ready: **false**.

| Stage | Status | Exact evidence class | Boundary |
|---|---|---|---|
| cnc3_actual_rtl_transport | BLOCKED | REAL_LINUXCNC_CNC3_ACTUAL_RTL | Bounded actual CNC3 motion/session/rate/SPI RTL is tested separately; real CNC3 HAL/LinuxCNC integration and complete CAP3/pages/IOL1/events/output authority remain absent |
| twelve_joint_simultaneous_machine | BLOCKED | SIMULATED_FULL_MACHINE | Actual twelve STEP/DIR outputs and four ABZ algorithms couple to ideal mechanics in a separate fixture; full LinuxCNC machine kinematics, electrical providers and all I/O are not integrated |
| critical_circuit_spice_corners | BLOCKED | SPICE_CORNER_MONTE_CARLO | Selected passive and buffer studies are partial; complete analog models/corners, physical power/permission circuits and coupled worst-case loads remain unqualified |
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
| complete_PCB_routing | BLOCKED | NATIVE_PHYSICAL_CONNECTIVITY | 3508 uncapped Source-cluster joins remain; independent integrity PASS |
| watchdog_RTL | PASS | RTL_SIMULATION_LINT_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| IOL1_target | PASS | ARM_TARGET_COMPILE_HOST_C_RTL_VPI_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| isolated_stepgen12_sweep | PASS | ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP | Fresh command and exact artifact checked |
| isolated_stepgen12_dynamic | PASS | ACTUAL_RTL_DYNAMIC_COMPONENT_TEST | Fresh command and exact artifact checked |
| isolated_encoder4_sweep | PASS | ACTUAL_RTL_IDEAL_DIGITAL_COMPONENT_SWEEP | Fresh command and exact artifact checked |
| analog_passive_filter_corners | PASS | ACTUAL_NATIVE_BOUND_PASSIVE_FILTER_SPICE | Fresh command and exact artifact checked |
| analog_active_buffer_corners | PASS | NATIVE_BOUND_MANUFACTURER_BUFFER_MACROMODEL_SPICE | Fresh command and exact artifact checked |
| isolated_edge_plant | PASS | COMPILED_DISCONNECTED_IDEAL_MECHANICS_FIXTURE | Fresh command and exact artifact checked |
| actual_cnc3_SPI_edge_plant | PASS | ACTUAL_VERILATED_CNC3_SPI_PINS_IDEAL_MECHANICS | Fresh command and exact artifact checked |
| seeded_actual_SPI_faults | PASS | FRESH_VERILATED_2048_SEEDED_SERIAL_FAULTS_IDEAL_PROVIDERS | Fresh command and exact artifact checked |
| bounded_IOL1_diagnostic_acquisition | PASS | ACTUAL_C_TARGET_SPI_RTL_AGE_MUTATIONS_FAMILY_MAPPING | Fresh command and exact artifact checked |
| bounded_IS2_CAP3_profile | PASS | ACTUAL_COMPILED_C_RTL_SPI_DISCOVERY_FAIL_CLOSED_MUTATIONS | Fresh command and exact artifact checked |
| bounded_CNC3_stateful_replay | PASS | ACTUAL_CNC3_STATE_RATE_SPI_MUTATIONS_FAMILY_MAPPING | Fresh command and exact artifact checked |
| cnc3_layout_contract | PASS | GENERATED_C_PROTOCOL_LAYOUT_CHECK | Fresh command and exact artifact checked |
| cnc3_host_model | PASS | HOST_C_MODEL_ASAN_UBSAN | Fresh command and exact artifact checked |
| cnc3_structural_RTL | PASS | ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS | Fresh command and exact artifact checked |
| historical_linuxcnc_six_two | PASS | REAL_LINUXCNC_VERILATED_CNC1 | Fresh command and exact artifact checked |
| supervisor_fault_scenarios | PASS | HOST_SUPERVISOR_MODEL | Fresh command and exact artifact checked |
| input_integrity | PASS | EXACT_SOURCE_HASHES | Scoped source and frozen PCB hashes retained |

Numerical production ratings remain null where complete chain/corners/fit/final-route qualification is absent. Host/model, actual RTL, target compilation, real LinuxCNC, native ERC/DRC and physical measurement are separate.
