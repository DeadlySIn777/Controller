// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Primary model header
//
// This header should be included by all source files instantiating the design.
// The class here is then constructed to instantiate the design.
// See the Verilator manual for examples.

#ifndef VERILATED_VCNC3_RUNTIME_SIM_H_
#define VERILATED_VCNC3_RUNTIME_SIM_H_  // guard

#include "verilated.h"

class Vcnc3_runtime_sim__Syms;
class Vcnc3_runtime_sim___024root;

// This class is the main interface to the Verilated model
class alignas(VL_CACHE_LINE_BYTES) Vcnc3_runtime_sim VL_NOT_FINAL : public VerilatedModel {
  private:
    // Symbol table holding complete model state (owned by this class)
    Vcnc3_runtime_sim__Syms* const vlSymsp;

  public:

    // CONSTEXPR CAPABILITIES
    // Verilated with --trace?
    static constexpr bool traceCapable = false;

    // PORTS
    // The application code writes and reads these signals to
    // propagate new values into/out from the Verilated model.
    VL_IN8(&clk,0,0);
    VL_IN8(&rst_n,0,0);
    VL_IN8(&spi_cs_fb_n,0,0);
    VL_IN8(&spi_cs_cmd_n,0,0);
    VL_IN8(&spi_sclk,0,0);
    VL_IN8(&spi_mosi,0,0);
    VL_OUT8(&spi_miso,0,0);
    VL_OUT8(&spi_miso_oe,0,0);
    VL_IN8(&sim_context,0,0);
    VL_IN8(&provider_strobe,0,0);
    VL_IN8(&provider_abi,7,0);
    VL_IN8(&provider_valid_mask,7,0);
    VL_IN8(&probe_raw,1,0);
    VL_IN8(&inhibit_n,0,0);
    VL_IN8(&wd_m_ok,0,0);
    VL_IN8(&wd_o_ok,0,0);
    VL_IN8(&reset_arm_ready,0,0);
    VL_IN8(&reset_arm_held,0,0);
    VL_IN8(&contactor_deenergized,0,0);
    VL_IN8(&sto_arm_expected,0,0);
    VL_IN8(&gate_high,3,0);
    VL_IN8(&opi_ok,3,0);
    VL_IN8(&encoder_a,3,0);
    VL_IN8(&encoder_b,3,0);
    VL_IN8(&encoder_z,3,0);
    VL_IN8(&encoder_port_valid,3,0);
    VL_OUT8(&motion_request,0,0);
    VL_OUT8(&output_request,0,0);
    VL_OUT8(&permit_out_req,0,0);
    VL_OUT8(&progress_m,0,0);
    VL_OUT8(&progress_o,0,0);
    VL_OUT8(&opi_rearm,3,0);
    VL_OUT8(&reset_arm_consumed,0,0);
    VL_OUT8(&config_valid,0,0);
    VL_OUT8(&selftest_passed,1,0);
    VL_OUT8(&selftest_state,2,0);
    VL_OUT8(&accepted_pulse,0,0);
    VL_OUT8(&last_reject,7,0);
    VL_OUT8(&sim_ready,0,0);
    VL_OUT8(&provider_error,0,0);
    VL_OUT8(&physical_authority,0,0);
    VL_OUT8(&production_profile_complete,0,0);
    VL_IN16(&do_applied,15,0);
    VL_IN16(&do_fault,15,0);
    VL_IN16(&home_raw,11,0);
    VL_IN16(&limit_low_raw,11,0);
    VL_IN16(&limit_high_raw,11,0);
    VL_IN16(&alarm_current_raw,11,0);
    VL_OUT16(&step_out,11,0);
    VL_OUT16(&dir_out,11,0);
    VL_OUT16(&enable_n,11,0);
    VL_OUT16(&armed_mask,11,0);
    VL_OUT16(&pos_continuity,11,0);
    VL_OUT16(&dout_request,15,0);
    VL_IN(&sim_expected_session,31,0);
    VL_IN(&sim_expected_config_hash,31,0);
    VL_IN(&provider_tag,31,0);
    VL_IN(&provider_session,31,0);
    VL_IN(&provider_config_hash,31,0);
    VL_IN(&provider_sequence,31,0);
    VL_IN(&provider_faults,31,0);
    VL_IN(&di_raw,23,0);
    VL_IN(&external_fault_word,31,0);
    VL_IN(&physical_safety_power_word,31,0);
    VL_OUT(&session,31,0);
    VL_OUT(&last_sequence,31,0);
    VL_OUT(&fault_word,31,0);
    VL_OUTW(&actual_feedback_payload,1391,0,44);
    VL_OUTW(&actual_status_payload,751,0,24);
    VL_OUT(&provider_accepted_sequence,31,0);

    // CELLS
    // Public to allow access to /* verilator public */ items.
    // Otherwise the application code can consider these internals.

    // Root instance pointer to allow access to model internals,
    // including inlined /* verilator public_flat_* */ items.
    Vcnc3_runtime_sim___024root* const rootp;

    // CONSTRUCTORS
    /// Construct the model; called by application code
    /// If contextp is null, then the model will use the default global context
    /// If name is "", then makes a wrapper with a
    /// single model invisible with respect to DPI scope names.
    explicit Vcnc3_runtime_sim(VerilatedContext* contextp, const char* name = "TOP");
    explicit Vcnc3_runtime_sim(const char* name = "TOP");
    /// Destroy the model; called (often implicitly) by application code
    virtual ~Vcnc3_runtime_sim();
  private:
    VL_UNCOPYABLE(Vcnc3_runtime_sim);  ///< Copying not allowed

  public:
    // API METHODS
    /// Evaluate the model.  Application must call when inputs change.
    void eval() { eval_step(); }
    /// Evaluate when calling multiple units/models per time step.
    void eval_step();
    /// Evaluate at end of a timestep for tracing, when using eval_step().
    /// Application must call after all eval() and before time changes.
    void eval_end_step() {}
    /// Simulation complete, run final blocks.  Application must call on completion.
    void final();
    /// Are there scheduled events to handle?
    bool eventsPending();
    /// Returns time at next time slot. Aborts if !eventsPending()
    uint64_t nextTimeSlot();
    /// Trace signals in the model; called by application code
    void trace(VerilatedTraceBaseC* tfp, int levels, int options = 0) { contextp()->trace(tfp, levels, options); }
    /// Retrieve name of this model instance (as passed to constructor).
    const char* name() const;

    // Abstract methods from VerilatedModel
    const char* hierName() const override final;
    const char* modelName() const override final;
    unsigned threads() const override final;
    /// Prepare for cloning the model at the process level (e.g. fork in Linux)
    /// Release necessary resources. Called before cloning.
    void prepareClone() const;
    /// Re-init after cloning the model at the process level (e.g. fork in Linux)
    /// Re-allocate necessary resources. Called after cloning.
    void atClone() const;
  private:
    // Internal functions - trace registration
    void traceBaseModel(VerilatedTraceBaseC* tfp, int levels, int options);
};

#endif  // guard
