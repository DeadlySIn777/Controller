// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vcnc3_runtime__pch.h"

//============================================================
// Constructors

Vcnc3_runtime::Vcnc3_runtime(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vcnc3_runtime__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , rst_n{vlSymsp->TOP.rst_n}
    , spi_cs_fb_n{vlSymsp->TOP.spi_cs_fb_n}
    , spi_cs_cmd_n{vlSymsp->TOP.spi_cs_cmd_n}
    , spi_sclk{vlSymsp->TOP.spi_sclk}
    , spi_mosi{vlSymsp->TOP.spi_mosi}
    , spi_miso{vlSymsp->TOP.spi_miso}
    , spi_miso_oe{vlSymsp->TOP.spi_miso_oe}
    , sim_context{vlSymsp->TOP.sim_context}
    , provider_strobe{vlSymsp->TOP.provider_strobe}
    , provider_abi{vlSymsp->TOP.provider_abi}
    , provider_valid_mask{vlSymsp->TOP.provider_valid_mask}
    , probe_raw{vlSymsp->TOP.probe_raw}
    , inhibit_n{vlSymsp->TOP.inhibit_n}
    , wd_m_ok{vlSymsp->TOP.wd_m_ok}
    , wd_o_ok{vlSymsp->TOP.wd_o_ok}
    , reset_arm_ready{vlSymsp->TOP.reset_arm_ready}
    , reset_arm_held{vlSymsp->TOP.reset_arm_held}
    , contactor_deenergized{vlSymsp->TOP.contactor_deenergized}
    , sto_arm_expected{vlSymsp->TOP.sto_arm_expected}
    , gate_high{vlSymsp->TOP.gate_high}
    , opi_ok{vlSymsp->TOP.opi_ok}
    , output_gate_high{vlSymsp->TOP.output_gate_high}
    , output_opi_ok{vlSymsp->TOP.output_opi_ok}
    , output_opi_rearm{vlSymsp->TOP.output_opi_rearm}
    , encoder_a{vlSymsp->TOP.encoder_a}
    , encoder_b{vlSymsp->TOP.encoder_b}
    , encoder_z{vlSymsp->TOP.encoder_z}
    , encoder_port_valid{vlSymsp->TOP.encoder_port_valid}
    , motion_request{vlSymsp->TOP.motion_request}
    , output_request{vlSymsp->TOP.output_request}
    , permit_out_req{vlSymsp->TOP.permit_out_req}
    , progress_m{vlSymsp->TOP.progress_m}
    , progress_o{vlSymsp->TOP.progress_o}
    , opi_rearm{vlSymsp->TOP.opi_rearm}
    , reset_arm_consumed{vlSymsp->TOP.reset_arm_consumed}
    , config_valid{vlSymsp->TOP.config_valid}
    , selftest_passed{vlSymsp->TOP.selftest_passed}
    , selftest_state{vlSymsp->TOP.selftest_state}
    , accepted_pulse{vlSymsp->TOP.accepted_pulse}
    , last_reject{vlSymsp->TOP.last_reject}
    , sim_ready{vlSymsp->TOP.sim_ready}
    , provider_error{vlSymsp->TOP.provider_error}
    , physical_authority{vlSymsp->TOP.physical_authority}
    , production_profile_complete{vlSymsp->TOP.production_profile_complete}
    , do_applied{vlSymsp->TOP.do_applied}
    , do_fault{vlSymsp->TOP.do_fault}
    , home_raw{vlSymsp->TOP.home_raw}
    , limit_low_raw{vlSymsp->TOP.limit_low_raw}
    , limit_high_raw{vlSymsp->TOP.limit_high_raw}
    , alarm_current_raw{vlSymsp->TOP.alarm_current_raw}
    , step_out{vlSymsp->TOP.step_out}
    , dir_out{vlSymsp->TOP.dir_out}
    , enable_n{vlSymsp->TOP.enable_n}
    , armed_mask{vlSymsp->TOP.armed_mask}
    , pos_continuity{vlSymsp->TOP.pos_continuity}
    , dout_request{vlSymsp->TOP.dout_request}
    , sim_expected_session{vlSymsp->TOP.sim_expected_session}
    , sim_expected_config_hash{vlSymsp->TOP.sim_expected_config_hash}
    , provider_tag{vlSymsp->TOP.provider_tag}
    , provider_session{vlSymsp->TOP.provider_session}
    , provider_config_hash{vlSymsp->TOP.provider_config_hash}
    , provider_sequence{vlSymsp->TOP.provider_sequence}
    , provider_faults{vlSymsp->TOP.provider_faults}
    , di_raw{vlSymsp->TOP.di_raw}
    , external_fault_word{vlSymsp->TOP.external_fault_word}
    , physical_safety_power_word{vlSymsp->TOP.physical_safety_power_word}
    , session{vlSymsp->TOP.session}
    , last_sequence{vlSymsp->TOP.last_sequence}
    , fault_word{vlSymsp->TOP.fault_word}
    , actual_feedback_payload{vlSymsp->TOP.actual_feedback_payload}
    , actual_status_payload{vlSymsp->TOP.actual_status_payload}
    , provider_accepted_sequence{vlSymsp->TOP.provider_accepted_sequence}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vcnc3_runtime::Vcnc3_runtime(const char* _vcname__)
    : Vcnc3_runtime(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vcnc3_runtime::~Vcnc3_runtime() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vcnc3_runtime___024root___eval_debug_assertions(Vcnc3_runtime___024root* vlSelf);
#endif  // VL_DEBUG
void Vcnc3_runtime___024root___eval_static(Vcnc3_runtime___024root* vlSelf);
void Vcnc3_runtime___024root___eval_initial(Vcnc3_runtime___024root* vlSelf);
void Vcnc3_runtime___024root___eval_settle(Vcnc3_runtime___024root* vlSelf);
void Vcnc3_runtime___024root___eval(Vcnc3_runtime___024root* vlSelf);

void Vcnc3_runtime::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcnc3_runtime::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vcnc3_runtime___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vcnc3_runtime___024root___eval_static(&(vlSymsp->TOP));
        Vcnc3_runtime___024root___eval_initial(&(vlSymsp->TOP));
        Vcnc3_runtime___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vcnc3_runtime___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vcnc3_runtime::eventsPending() { return false; }

uint64_t Vcnc3_runtime::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vcnc3_runtime::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vcnc3_runtime___024root___eval_final(Vcnc3_runtime___024root* vlSelf);

VL_ATTR_COLD void Vcnc3_runtime::final() {
    contextp()->executingFinal(true);
    Vcnc3_runtime___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vcnc3_runtime::hierName() const { return vlSymsp->name(); }
const char* Vcnc3_runtime::modelName() const { return "Vcnc3_runtime"; }
unsigned Vcnc3_runtime::threads() const { return 1; }
void Vcnc3_runtime::prepareClone() const { contextp()->prepareClone(); }
void Vcnc3_runtime::atClone() const {
    contextp()->threadPoolpOnClone();
}
