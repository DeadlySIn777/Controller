// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcnc3_motion_spi.h for the primary calling header

#include "Vcnc3_motion_spi__pch.h"

void Vcnc3_motion_spi___024root___nba_sequent__TOP__1(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___nba_sequent__TOP__1\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VdfgRegularize_h6e95ff9d_0_1;
    __VdfgRegularize_h6e95ff9d_0_1 = 0;
    // Body
    __VdfgRegularize_h6e95ff9d_0_1 = (vlSelfRef.session 
                                      == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]);
    vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__rise_d 
        = ((IData)(vlSelfRef.rst_n) && (IData)(vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_rise));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0 = ((IData)(vlSelfRef.cnc3_motion_spi__DOT__frame_valid) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.cnc3_motion_spi__DOT__validation_result)));
    vlSelfRef.cnc3_motion_spi__DOT__req_valid = ((IData)(vlSelfRef.cnc3_motion_spi__DOT__frame_valid) 
                                                 & (0U 
                                                    == (IData)(vlSelfRef.cnc3_motion_spi__DOT__validation_result)));
    vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__readonly_session 
        = ((0U == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]) 
           | (IData)(__VdfgRegularize_h6e95ff9d_0_1));
    vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence 
        = ((IData)(__VdfgRegularize_h6e95ff9d_0_1) 
           & ((0U != vlSelfRef.session) & ((0xffffffffU 
                                            != vlSelfRef.last_sequence) 
                                           & ((vlSelfRef.cnc3_motion_spi__DOT__frame[40U] 
                                               == ((IData)(1U) 
                                                   + vlSelfRef.last_sequence)) 
                                              & (0U 
                                                 != vlSelfRef.cnc3_motion_spi__DOT__frame[40U])))));
    vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_rise 
        = (IData)((2U == (6U & (IData)(vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_sync))));
    vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__cfg_session 
        = ((0U == vlSelfRef.session) ? ((0U == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]) 
                                        & (0U == vlSelfRef.cnc3_motion_spi__DOT__frame[40U]))
            : (IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence));
    vlSelfRef.cnc3_motion_spi__DOT__stop = ((IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__stopping) 
                                            | (((IData)(vlSelfRef.cnc3_motion_spi__DOT__req_valid) 
                                                & (0x00040000U 
                                                   == 
                                                   (0x00ff0000U 
                                                    & vlSelfRef.cnc3_motion_spi__DOT__frame[42U]))) 
                                               & (IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence)));
}

void Vcnc3_motion_spi___024root___nba_sequent__TOP__0(Vcnc3_motion_spi___024root* vlSelf);

void Vcnc3_motion_spi___024root___eval_nba(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___eval_nba\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __Vinline__nba_sequent__TOP__1___VdfgRegularize_h6e95ff9d_0_1;
    __Vinline__nba_sequent__TOP__1___VdfgRegularize_h6e95ff9d_0_1 = 0;
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vcnc3_motion_spi___024root___nba_sequent__TOP__0(vlSelf);
        __Vinline__nba_sequent__TOP__1___VdfgRegularize_h6e95ff9d_0_1 
            = (vlSelfRef.session == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]);
        vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__rise_d 
            = ((IData)(vlSelfRef.rst_n) && (IData)(vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_rise));
        vlSelfRef.__VdfgRegularize_h6e95ff9d_0_0 = 
            ((IData)(vlSelfRef.cnc3_motion_spi__DOT__frame_valid) 
             & (0U != (IData)(vlSelfRef.cnc3_motion_spi__DOT__validation_result)));
        vlSelfRef.cnc3_motion_spi__DOT__req_valid = 
            ((IData)(vlSelfRef.cnc3_motion_spi__DOT__frame_valid) 
             & (0U == (IData)(vlSelfRef.cnc3_motion_spi__DOT__validation_result)));
        vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__readonly_session 
            = ((0U == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]) 
               | __Vinline__nba_sequent__TOP__1___VdfgRegularize_h6e95ff9d_0_1);
        vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence 
            = (__Vinline__nba_sequent__TOP__1___VdfgRegularize_h6e95ff9d_0_1 
               & ((0U != vlSelfRef.session) & ((0xffffffffU 
                                                != vlSelfRef.last_sequence) 
                                               & ((vlSelfRef.cnc3_motion_spi__DOT__frame[40U] 
                                                   == 
                                                   ((IData)(1U) 
                                                    + vlSelfRef.last_sequence)) 
                                                  & (0U 
                                                     != vlSelfRef.cnc3_motion_spi__DOT__frame[40U])))));
        vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_rise 
            = (IData)((2U == (6U & (IData)(vlSelfRef.cnc3_motion_spi__DOT__transport__DOT__sck_sync))));
        vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__cfg_session 
            = ((0U == vlSelfRef.session) ? ((0U == vlSelfRef.cnc3_motion_spi__DOT__frame[41U]) 
                                            & (0U == vlSelfRef.cnc3_motion_spi__DOT__frame[40U]))
                : (IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence));
        vlSelfRef.cnc3_motion_spi__DOT__stop = ((IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__stopping) 
                                                | (((IData)(vlSelfRef.cnc3_motion_spi__DOT__req_valid) 
                                                    & (0x00040000U 
                                                       == 
                                                       (0x00ff0000U 
                                                        & vlSelfRef.cnc3_motion_spi__DOT__frame[42U]))) 
                                                   & (IData)(vlSelfRef.cnc3_motion_spi__DOT__state_machine__DOT__next_sequence)));
    }
}

void Vcnc3_motion_spi___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

void Vcnc3_motion_spi___024root___eval_triggers_vec__act(Vcnc3_motion_spi___024root* vlSelf);
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_motion_spi___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vcnc3_motion_spi___024root___eval_phase__act(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___eval_phase__act\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vcnc3_motion_spi___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcnc3_motion_spi___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vcnc3_motion_spi___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vcnc3_motion_spi___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vcnc3_motion_spi___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

bool Vcnc3_motion_spi___024root___eval_phase__nba(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___eval_phase__nba\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vcnc3_motion_spi___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vcnc3_motion_spi___024root___eval_nba(vlSelf);
        Vcnc3_motion_spi___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_motion_spi___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
bool Vcnc3_motion_spi___024root___eval_phase__ico(Vcnc3_motion_spi___024root* vlSelf);

void Vcnc3_motion_spi___024root___eval(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___eval\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __VicoIterCount;
    IData/*31:0*/ __VnbaIterCount;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VicoIterCount)))) {
#ifdef VL_DEBUG
            Vcnc3_motion_spi___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/controller-plant-20261001/actual-spi-edge-plant-r02/inputs/cnc3_motion_spi.v", 6, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 10000 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = Vcnc3_motion_spi___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vcnc3_motion_spi___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/controller-plant-20261001/actual-spi-edge-plant-r02/inputs/cnc3_motion_spi.v", 6, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vcnc3_motion_spi___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/controller-plant-20261001/actual-spi-edge-plant-r02/inputs/cnc3_motion_spi.v", 6, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vcnc3_motion_spi___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vcnc3_motion_spi___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vcnc3_motion_spi___024root___eval_debug_assertions(Vcnc3_motion_spi___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_motion_spi___024root___eval_debug_assertions\n"); );
    Vcnc3_motion_spi__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst_n & 0xfeU)))) {
        Verilated::overWidthError("rst_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.spi_cs_fb_n & 0xfeU)))) {
        Verilated::overWidthError("spi_cs_fb_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.spi_cs_cmd_n & 0xfeU)))) {
        Verilated::overWidthError("spi_cs_cmd_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.spi_sclk & 0xfeU)))) {
        Verilated::overWidthError("spi_sclk");
    }
    if (VL_UNLIKELY(((vlSelfRef.spi_mosi & 0xfeU)))) {
        Verilated::overWidthError("spi_mosi");
    }
    if (VL_UNLIKELY(((vlSelfRef.qualification_complete 
                      & 0xfeU)))) {
        Verilated::overWidthError("qualification_complete");
    }
    if (VL_UNLIKELY(((vlSelfRef.installed_input & 0xf000U)))) {
        Verilated::overWidthError("installed_input");
    }
    if (VL_UNLIKELY(((vlSelfRef.inhibit_n & 0xfeU)))) {
        Verilated::overWidthError("inhibit_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.wd_m_ok & 0xfeU)))) {
        Verilated::overWidthError("wd_m_ok");
    }
    if (VL_UNLIKELY(((vlSelfRef.wd_o_ok & 0xfeU)))) {
        Verilated::overWidthError("wd_o_ok");
    }
    if (VL_UNLIKELY(((vlSelfRef.reset_arm_ready & 0xfeU)))) {
        Verilated::overWidthError("reset_arm_ready");
    }
    if (VL_UNLIKELY(((vlSelfRef.reset_arm_held & 0xfeU)))) {
        Verilated::overWidthError("reset_arm_held");
    }
    if (VL_UNLIKELY(((vlSelfRef.contactor_deenergized 
                      & 0xfeU)))) {
        Verilated::overWidthError("contactor_deenergized");
    }
    if (VL_UNLIKELY(((vlSelfRef.sto_arm_expected & 0xfeU)))) {
        Verilated::overWidthError("sto_arm_expected");
    }
    if (VL_UNLIKELY(((vlSelfRef.motion_critical_ports_valid 
                      & 0xfeU)))) {
        Verilated::overWidthError("motion_critical_ports_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.gate_high & 0xf0U)))) {
        Verilated::overWidthError("gate_high");
    }
    if (VL_UNLIKELY(((vlSelfRef.opi_ok & 0xf0U)))) {
        Verilated::overWidthError("opi_ok");
    }
    if (VL_UNLIKELY(((vlSelfRef.alarm_current_raw & 0xf000U)))) {
        Verilated::overWidthError("alarm_current_raw");
    }
    if (VL_UNLIKELY(((vlSelfRef.encoder_a & 0xf0U)))) {
        Verilated::overWidthError("encoder_a");
    }
    if (VL_UNLIKELY(((vlSelfRef.encoder_b & 0xf0U)))) {
        Verilated::overWidthError("encoder_b");
    }
    if (VL_UNLIKELY(((vlSelfRef.encoder_z & 0xf0U)))) {
        Verilated::overWidthError("encoder_z");
    }
    if (VL_UNLIKELY(((vlSelfRef.encoder_installed & 0xf0U)))) {
        Verilated::overWidthError("encoder_installed");
    }
    if (VL_UNLIKELY(((vlSelfRef.encoder_port_valid 
                      & 0xf0U)))) {
        Verilated::overWidthError("encoder_port_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.motion_critical_io_fault 
                      & 0xfeU)))) {
        Verilated::overWidthError("motion_critical_io_fault");
    }
    if (VL_UNLIKELY(((vlSelfRef.provider_feedback[43U] 
                      & 0xffff0000U)))) {
        Verilated::overWidthError("provider_feedback");
    }
    if (VL_UNLIKELY(((vlSelfRef.provider_status[23U] 
                      & 0xffff0000U)))) {
        Verilated::overWidthError("provider_status");
    }
}
#endif  // VL_DEBUG
