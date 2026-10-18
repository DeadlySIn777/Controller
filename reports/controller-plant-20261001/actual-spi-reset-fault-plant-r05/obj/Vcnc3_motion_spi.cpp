// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vcnc3_motion_spi__pch.h"

//============================================================
// Constructors

Vcnc3_motion_spi::Vcnc3_motion_spi(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vcnc3_motion_spi__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , rst_n{vlSymsp->TOP.rst_n}
    , spi_cs_fb_n{vlSymsp->TOP.spi_cs_fb_n}
    , spi_cs_cmd_n{vlSymsp->TOP.spi_cs_cmd_n}
    , spi_sclk{vlSymsp->TOP.spi_sclk}
    , spi_mosi{vlSymsp->TOP.spi_mosi}
    , spi_miso{vlSymsp->TOP.spi_miso}
    , spi_miso_oe{vlSymsp->TOP.spi_miso_oe}
    , qualification_complete{vlSymsp->TOP.qualification_complete}
    , installed_module_class{vlSymsp->TOP.installed_module_class}
    , inhibit_n{vlSymsp->TOP.inhibit_n}
    , wd_m_ok{vlSymsp->TOP.wd_m_ok}
    , wd_o_ok{vlSymsp->TOP.wd_o_ok}
    , reset_arm_ready{vlSymsp->TOP.reset_arm_ready}
    , reset_arm_held{vlSymsp->TOP.reset_arm_held}
    , contactor_deenergized{vlSymsp->TOP.contactor_deenergized}
    , sto_arm_expected{vlSymsp->TOP.sto_arm_expected}
    , motion_critical_ports_valid{vlSymsp->TOP.motion_critical_ports_valid}
    , gate_high{vlSymsp->TOP.gate_high}
    , opi_ok{vlSymsp->TOP.opi_ok}
    , encoder_a{vlSymsp->TOP.encoder_a}
    , encoder_b{vlSymsp->TOP.encoder_b}
    , encoder_z{vlSymsp->TOP.encoder_z}
    , encoder_installed{vlSymsp->TOP.encoder_installed}
    , encoder_port_valid{vlSymsp->TOP.encoder_port_valid}
    , motion_critical_io_fault{vlSymsp->TOP.motion_critical_io_fault}
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
    , installed_input{vlSymsp->TOP.installed_input}
    , alarm_current_raw{vlSymsp->TOP.alarm_current_raw}
    , step_out{vlSymsp->TOP.step_out}
    , dir_out{vlSymsp->TOP.dir_out}
    , enable_n{vlSymsp->TOP.enable_n}
    , armed_mask{vlSymsp->TOP.armed_mask}
    , pos_continuity{vlSymsp->TOP.pos_continuity}
    , external_fault_word{vlSymsp->TOP.external_fault_word}
    , provider_feedback{vlSymsp->TOP.provider_feedback}
    , provider_status{vlSymsp->TOP.provider_status}
    , physical_safety_power_word{vlSymsp->TOP.physical_safety_power_word}
    , session{vlSymsp->TOP.session}
    , last_sequence{vlSymsp->TOP.last_sequence}
    , fault_word{vlSymsp->TOP.fault_word}
    , actual_feedback_payload{vlSymsp->TOP.actual_feedback_payload}
    , actual_status_payload{vlSymsp->TOP.actual_status_payload}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vcnc3_motion_spi::Vcnc3_motion_spi(const char* _vcname__)
    : Vcnc3_motion_spi(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vcnc3_motion_spi::~Vcnc3_motion_spi() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vcnc3_motion_spi___024root___eval_debug_assertions(Vcnc3_motion_spi___024root* vlSelf);
#endif  // VL_DEBUG
void Vcnc3_motion_spi___024root___eval_static(Vcnc3_motion_spi___024root* vlSelf);
void Vcnc3_motion_spi___024root___eval_initial(Vcnc3_motion_spi___024root* vlSelf);
void Vcnc3_motion_spi___024root___eval_settle(Vcnc3_motion_spi___024root* vlSelf);
void Vcnc3_motion_spi___024root___eval(Vcnc3_motion_spi___024root* vlSelf);

void Vcnc3_motion_spi::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcnc3_motion_spi::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vcnc3_motion_spi___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vcnc3_motion_spi___024root___eval_static(&(vlSymsp->TOP));
        Vcnc3_motion_spi___024root___eval_initial(&(vlSymsp->TOP));
        Vcnc3_motion_spi___024root___eval_settle(&(vlSymsp->TOP));
        vlSymsp->__Vm_didInit = true;
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vcnc3_motion_spi___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vcnc3_motion_spi::eventsPending() { return false; }

uint64_t Vcnc3_motion_spi::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vcnc3_motion_spi::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vcnc3_motion_spi___024root___eval_final(Vcnc3_motion_spi___024root* vlSelf);

VL_ATTR_COLD void Vcnc3_motion_spi::final() {
    contextp()->executingFinal(true);
    Vcnc3_motion_spi___024root___eval_final(&(vlSymsp->TOP));
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vcnc3_motion_spi::hierName() const { return vlSymsp->name(); }
const char* Vcnc3_motion_spi::modelName() const { return "Vcnc3_motion_spi"; }
unsigned Vcnc3_motion_spi::threads() const { return 1; }
void Vcnc3_motion_spi::prepareClone() const { contextp()->prepareClone(); }
void Vcnc3_motion_spi::atClone() const {
    contextp()->threadPoolpOnClone();
}
