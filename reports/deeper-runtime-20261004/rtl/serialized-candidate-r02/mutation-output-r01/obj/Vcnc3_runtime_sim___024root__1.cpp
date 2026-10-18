// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcnc3_runtime_sim.h for the primary calling header

#include "Vcnc3_runtime_sim__pch.h"

void Vcnc3_runtime_sim___024root___nba_sequent__TOP__2(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___nba_sequent__TOP__2\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ cnc3_runtime_sim__DOT__effective;
    cnc3_runtime_sim__DOT__effective = 0;
    CData/*0:0*/ __VdfgRegularize_h6e95ff9d_0_10;
    __VdfgRegularize_h6e95ff9d_0_10 = 0;
    // Body
    __VdfgRegularize_h6e95ff9d_0_10 = (vlSelfRef.session 
                                       == vlSelfRef.cnc3_runtime_sim__DOT__frame[41U]);
    vlSelfRef.cnc3_runtime_sim__DOT__transport__DOT__rise_d 
        = ((IData)(vlSelfRef.rst_n) && (IData)(vlSelfRef.cnc3_runtime_sim__DOT__transport__DOT__sck_rise));
    vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__state_machine__limit_active 
        = (0U != ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__limit_low) 
                  | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__limit_high)));
    vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__stale 
        = (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__age_us) 
            >= (IData)(vlSelfRef.cnc3_runtime_sim__DOT__din_limit)) 
           | ((0x00faU > (IData)(vlSelfRef.cnc3_runtime_sim__DOT__din_limit)) 
              | (0x01b8U < (IData)(vlSelfRef.cnc3_runtime_sim__DOT__din_limit))));
    vlSelfRef.cnc3_runtime_sim__DOT__runtime_faults 
        = (vlSelfRef.external_fault_word | ((0x00002000U 
                                             & (- (IData)((IData)(vlSelfRef.provider_error)))) 
                                            | ((0x00040000U 
                                                & (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__event_overflow)))) 
                                               | (0x00010000U 
                                                  & (- (IData)(
                                                               ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_mismatch) 
                                                                | (0U 
                                                                   != (IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_faults)))))))));
    vlSelfRef.cnc3_runtime_sim__DOT__admission__DOT__high_value 
        = ((((0U == (0x0000001fU & (((IData)(0xbfU) 
                                     - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                        << 4U)) - (IData)(0x0fU))))
              ? 0U : (vlSelfRef.cnc3_runtime_sim__DOT__high
                      [(((IData)(0x0000000fU) + (0x000000ffU 
                                                 & (((IData)(0xbfU) 
                                                     - 
                                                     ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                                      << 4U)) 
                                                    - (IData)(0x0fU)))) 
                        >> 5U)] << ((IData)(0x00000020U) 
                                    - (0x0000001fU 
                                       & (((IData)(0xbfU) 
                                           - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                              << 4U)) 
                                          - (IData)(0x0fU)))))) 
            | (vlSelfRef.cnc3_runtime_sim__DOT__high
               [(7U & ((((IData)(0xbfU) - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                           << 4U)) 
                        - (IData)(0x0fU)) >> 5U))] 
               >> (0x0000001fU & (((IData)(0xbfU) - 
                                   ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                    << 4U)) - (IData)(0x0fU))))) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_12));
    vlSelfRef.cnc3_runtime_sim__DOT__admission__DOT__low_value 
        = ((((0U == (0x0000001fU & (((IData)(0xbfU) 
                                     - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                        << 4U)) - (IData)(0x0fU))))
              ? 0U : (vlSelfRef.cnc3_runtime_sim__DOT__low
                      [(((IData)(0x0000000fU) + (0x000000ffU 
                                                 & (((IData)(0xbfU) 
                                                     - 
                                                     ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                                      << 4U)) 
                                                    - (IData)(0x0fU)))) 
                        >> 5U)] << ((IData)(0x00000020U) 
                                    - (0x0000001fU 
                                       & (((IData)(0xbfU) 
                                           - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                              << 4U)) 
                                          - (IData)(0x0fU)))))) 
            | (vlSelfRef.cnc3_runtime_sim__DOT__low
               [(7U & ((((IData)(0xbfU) - ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                           << 4U)) 
                        - (IData)(0x0fU)) >> 5U))] 
               >> (0x0000001fU & (((IData)(0xbfU) - 
                                   ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__rx_rate_channel) 
                                    << 4U)) - (IData)(0x0fU))))) 
           & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_12));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_1 = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__frame_valid) 
                                                & (0U 
                                                   != (IData)(vlSelfRef.cnc3_runtime_sim__DOT__validation_result)));
    vlSelfRef.cnc3_runtime_sim__DOT__req_valid = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__frame_valid) 
                                                  & (0U 
                                                     == (IData)(vlSelfRef.cnc3_runtime_sim__DOT__validation_result)));
    vlSelfRef.cnc3_runtime_sim__DOT__read_session = 
        ((0U == vlSelfRef.cnc3_runtime_sim__DOT__frame[41U]) 
         | (IData)(__VdfgRegularize_h6e95ff9d_0_10));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__next_sequence 
        = ((IData)(__VdfgRegularize_h6e95ff9d_0_10) 
           & ((0U != vlSelfRef.session) & ((0xffffffffU 
                                            != vlSelfRef.last_sequence) 
                                           & ((vlSelfRef.cnc3_runtime_sim__DOT__frame[40U] 
                                               == ((IData)(1U) 
                                                   + vlSelfRef.last_sequence)) 
                                              & (0U 
                                                 != vlSelfRef.cnc3_runtime_sim__DOT__frame[40U])))));
    vlSelfRef.cnc3_runtime_sim__DOT__transport__DOT__sck_rise 
        = (IData)((2U == (6U & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__transport__DOT__sck_sync))));
    vlSelfRef.sim_ready = ((IData)(vlSelfRef.sim_context) 
                           & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__seen) 
                              & ((~ (IData)(vlSelfRef.provider_error)) 
                                 & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__stale)) 
                                    & ((vlSelfRef.sim_expected_config_hash 
                                        == vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__bound_hash) 
                                       & (vlSelfRef.sim_expected_session 
                                          == vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__bound_session))))));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__cfg_session 
        = ((0U == vlSelfRef.session) ? ((0U == vlSelfRef.cnc3_runtime_sim__DOT__frame[41U]) 
                                        & (0U == vlSelfRef.cnc3_runtime_sim__DOT__frame[40U]))
            : (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__next_sequence));
    vlSelfRef.cnc3_runtime_sim__DOT__stop = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__stopping) 
                                             | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__req_valid) 
                                                 & (0x00040000U 
                                                    == 
                                                    (0x00ff0000U 
                                                     & vlSelfRef.cnc3_runtime_sim__DOT__frame[42U]))) 
                                                & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__next_sequence)));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__output_conditions 
        = ((IData)(vlSelfRef.sim_ready) & ((~ (IData)(vlSelfRef.provider_error)) 
                                           & ((IData)(vlSelfRef.inhibit_n) 
                                              & ((IData)(vlSelfRef.wd_o_ok) 
                                                 & ((0U 
                                                     == 
                                                     (0x0000ffffU 
                                                      & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_faults) 
                                                         | (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_mismatch)))))) 
                                                    & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__io_arming) 
                                                       | ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__io)) 
                                                          | (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))))))));
    vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready 
        = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarm_valid) 
           & (IData)(vlSelfRef.sim_ready));
    vlSelfRef.__VdfgRegularize_h6e95ff9d_0_11 = ((IData)(vlSelfRef.encoder_port_valid) 
                                                 & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__encoder_illegal)) 
                                                    & (- (IData)((IData)(vlSelfRef.sim_ready)))));
    vlSelfRef.cnc3_runtime_sim__DOT__output_effective 
        = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__io) 
           & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__output_conditions) 
              & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__io_arming)) 
                 & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_3))));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_changed 
        = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_latched) 
           & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready)) 
              | ((0x0fffU != (IData)(vlSelfRef.cnc3_runtime_sim__DOT__installed_mask)) 
                 | (0U != (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_class)))));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__motion_runtime_fault 
        = (1U & (((((((((((((((((((IData)(vlSelfRef.provider_error) 
                                  | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__state_machine__limit_active)) 
                                 | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber13)) 
                                | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber13)) 
                               | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber13)) 
                              | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber13)) 
                             | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber13)) 
                            | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber13)) 
                           | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber13)) 
                          | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber13)) 
                         | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber13)) 
                        | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber13)) 
                       | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber13)) 
                      | (~ (IData)(vlSelfRef.sim_ready))) 
                     | (~ (IData)(vlSelfRef.inhibit_n))) 
                    | (~ (IData)(vlSelfRef.wd_m_ok))) 
                   | (0U != (0x0e38127fU & vlSelfRef.cnc3_runtime_sim__DOT__runtime_faults))) 
                  | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber13)) 
                 | ((0U != ((~ (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_11)) 
                            & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__required_encoders))) 
                    | (~ (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__arming) 
                           | (((IData)(vlSelfRef.opi_ok) 
                               & (3U | (- (IData)((0U 
                                                   != 
                                                   (0x0000000fU 
                                                    & ((IData)(vlSelfRef.armed_mask) 
                                                       >> 8U))))))) 
                              == (0x0000000fU & (3U 
                                                 | (- (IData)(
                                                              (0U 
                                                               != 
                                                               (0x0000000fU 
                                                                & ((IData)(vlSelfRef.armed_mask) 
                                                                   >> 8U))))))))) 
                          & (0U == ((IData)(vlSelfRef.armed_mask) 
                                    & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__asserted_alarm))))))));
    vlSelfRef.dout_request = (0xfffdU & ((- (IData)(
                                                    ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_effective) 
                                                     & ((IData)(vlSelfRef.sim_ready) 
                                                        & ((IData)(vlSelfRef.inhibit_n) 
                                                           & ((IData)(vlSelfRef.wd_o_ok) 
                                                              & (0U 
                                                                 == vlSelfRef.fault_word))))))) 
                                         & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__dout_image)));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__io_payload_ok 
        = (IData)((((0U == (0xfff0fc00U & vlSelfRef.cnc3_runtime_sim__DOT__frame[26U])) 
                    & (0U == (0x0000ffffU & vlSelfRef.cnc3_runtime_sim__DOT__frame[27U]))) 
                   & ((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__io)
                         ? ((0U == ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__dout_enable_mask)) 
                                    & (vlSelfRef.cnc3_runtime_sim__DOT__frame[27U] 
                                       >> 0x00000010U))) 
                            & ((0U == (vlSelfRef.cnc3_runtime_sim__DOT__frame[27U] 
                                       >> 0x00000010U)) 
                               | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_effective)))
                         : (0U == (vlSelfRef.cnc3_runtime_sim__DOT__frame[27U] 
                                   >> 0x00000010U))) 
                       & (0U == ((((vlSelfRef.cnc3_runtime_sim__DOT__frame[24U] 
                                    << 0x00000010U) 
                                   | (vlSelfRef.cnc3_runtime_sim__DOT__frame[23U] 
                                      >> 0x00000010U)) 
                                  | ((vlSelfRef.cnc3_runtime_sim__DOT__frame[25U] 
                                      << 0x00000010U) 
                                     | (vlSelfRef.cnc3_runtime_sim__DOT__frame[24U] 
                                        >> 0x00000010U))) 
                                 | (vlSelfRef.cnc3_runtime_sim__DOT__frame[25U] 
                                    >> 0x00000010U)))) 
                      & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__io_config_valid) 
                         | (IData)((0U == (0xffffff00U 
                                           & vlSelfRef.cnc3_runtime_sim__DOT__frame[26U])))))));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__cfg_semantic 
        = ((((((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_latched) 
                 & (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready)) 
                & (~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_changed))) 
               & (0U == (0x0ff0ff00U & vlSelfRef.cnc3_runtime_sim__DOT__frame[11U]))) 
              & (0U == (0x0000ff00U & vlSelfRef.cnc3_runtime_sim__DOT__frame[12U]))) 
             & (0U == (0x00ff0000U & vlSelfRef.cnc3_runtime_sim__DOT__frame[39U]))) 
            & (0U == (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_class))) 
           & ((((0U == (0x00000060U & (vlSelfRef.fault_word 
                                       | vlSelfRef.cnc3_runtime_sim__DOT__runtime_faults))) 
                & (0U != (0x00000fffU & vlSelfRef.cnc3_runtime_sim__DOT__frame[39U]))) 
               & (0U == (0x00000fffU & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__installed_mask)) 
                                        & vlSelfRef.cnc3_runtime_sim__DOT__frame[39U])))) 
              & (0U == (0x00000fffU & ((~ (0x0000000fU 
                                           & (- (IData)((IData)(vlSelfRef.sim_ready))))) 
                                       & (vlSelfRef.cnc3_runtime_sim__DOT__frame[11U] 
                                          >> 0x00000010U))))));
    cnc3_runtime_sim__DOT__effective = ((IData)(vlSelfRef.permit_out_req) 
                                        & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__arming)) 
                                           & (~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__motion_runtime_fault))));
    vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__update_admissible 
        = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__next_sequence) 
           & ((IData)(vlSelfRef.permit_out_req) & (
                                                   (~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__stopping)) 
                                                   & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__motion_runtime_fault)) 
                                                      & ((~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_changed)) 
                                                         & ((0U 
                                                             == vlSelfRef.fault_word) 
                                                            & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__io_payload_ok) 
                                                               & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__frame_rates_good) 
                                                                  & ((IData)(vlSelfRef.armed_mask) 
                                                                     == 
                                                                     (0x00000fffU 
                                                                      & vlSelfRef.cnc3_runtime_sim__DOT__frame[42U]))))))))));
    vlSelfRef.cnc3_runtime_sim__DOT__state = ((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__io) 
                                                << 5U) 
                                               | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__io_config_valid) 
                                                  << 4U)) 
                                              | ((((IData)(vlSelfRef.config_valid) 
                                                   << 3U) 
                                                  | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_latched) 
                                                     << 2U)) 
                                                 | ((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state_machine__DOT__qualification_latched) 
                                                      & (0U 
                                                         == vlSelfRef.fault_word)) 
                                                     << 1U) 
                                                    | (IData)(cnc3_runtime_sim__DOT__effective))));
    vlSelfRef.cnc3_runtime_sim__DOT__gen_enable = ((IData)(vlSelfRef.armed_mask) 
                                                   & (- (IData)((IData)(cnc3_runtime_sim__DOT__effective))));
    vlSelfRef.enable_n = (0x00000fffU & (~ (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable)));
    vlSelfRef.step_out = (((((((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber10) 
                               << 5U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber10) 
                                          << 4U) | 
                                         ((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber10) 
                                          << 3U))) 
                             | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber10) 
                                 << 2U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber10) 
                                            << 1U) 
                                           | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber10)))) 
                            << 6U) | ((((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber10) 
                                        << 5U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber10) 
                                                   << 4U) 
                                                  | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber10) 
                                                     << 3U))) 
                                      | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber10) 
                                          << 2U) | 
                                         (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber10) 
                                           << 1U) | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber10))))) 
                          & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable));
    vlSelfRef.dir_out = (((((((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber11) 
                              << 5U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber11) 
                                         << 4U) | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber11) 
                                                   << 3U))) 
                            | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber11) 
                                << 2U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber11) 
                                           << 1U) | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber11)))) 
                           << 6U) | ((((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber11) 
                                       << 5U) | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber11) 
                                                  << 4U) 
                                                 | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber11) 
                                                    << 3U))) 
                                     | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber11) 
                                         << 2U) | (
                                                   ((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber11) 
                                                    << 1U) 
                                                   | (IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber11))))) 
                         & (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable));
}

extern const VlWide<44>/*1407:0*/ Vcnc3_runtime_sim__ConstPool__CONST_h6c701f5b_0;
extern const VlWide<24>/*767:0*/ Vcnc3_runtime_sim__ConstPool__CONST_h80ba4ede_0;

void Vcnc3_runtime_sim___024root___nba_comb__TOP__0(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___nba_comb__TOP__0\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*23:0*/ cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0;
    cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 = 0;
    IData/*23:0*/ cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0;
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 = 0;
    VlWide<44>/*1391:0*/ cnc3_runtime_sim__DOT__fb;
    VL_ZERO_W(1392, cnc3_runtime_sim__DOT__fb);
    IData/*31:0*/ __Vilp1;
    IData/*31:0*/ __Vilp2;
    // Body
    if (vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__head_valid) {
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[0U] 
            = vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__stored_head[0U];
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[1U] 
            = vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__stored_head[1U];
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[2U] 
            = vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__stored_head[2U];
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[3U] 
            = vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__stored_head[3U];
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[4U] 
            = vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__stored_head[4U];
    } else {
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[0U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[1U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[2U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[3U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__event_head[4U] = 0U;
    }
    vlSelfRef.cnc3_runtime_sim__DOT__safety = vlSelfRef.physical_safety_power_word;
    vlSelfRef.cnc3_runtime_sim__DOT__safety = ((0xff9fffffU 
                                                & vlSelfRef.cnc3_runtime_sim__DOT__safety) 
                                               | ((IData)(vlSelfRef.selftest_passed) 
                                                  << 0x00000015U));
    VL_ASSIGN_W(1392, cnc3_runtime_sim__DOT__fb, Vcnc3_runtime_sim__ConstPool__CONST_h6c701f5b_0);
    cnc3_runtime_sim__DOT__fb[41U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[41U]) 
                                      | ((IData)((0x434e463303000000ULL 
                                                  | (QData)((IData)(
                                                                    (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                                      << 0x00000010U) 
                                                                     | (IData)(vlSelfRef.armed_mask)))))) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[42U] = (((IData)((0x434e463303000000ULL 
                                                | (QData)((IData)(
                                                                  (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                                    << 0x00000010U) 
                                                                   | (IData)(vlSelfRef.armed_mask)))))) 
                                       >> 0x00000010U) 
                                      | ((IData)(((0x434e463303000000ULL 
                                                   | (QData)((IData)(
                                                                     (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                                       << 0x00000010U) 
                                                                      | (IData)(vlSelfRef.armed_mask))))) 
                                                  >> 0x00000020U)) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[43U] = ((IData)(((0x434e463303000000ULL 
                                                | (QData)((IData)(
                                                                  (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                                    << 0x00000010U) 
                                                                   | (IData)(vlSelfRef.armed_mask))))) 
                                               >> 0x00000020U)) 
                                      >> 0x00000010U);
    cnc3_runtime_sim__DOT__fb[37U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[37U]) 
                                      | (vlSelfRef.fault_word 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[38U] = ((vlSelfRef.fault_word 
                                       >> 0x00000010U) 
                                      | (vlSelfRef.cnc3_runtime_sim__DOT__ticks 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[39U] = ((vlSelfRef.cnc3_runtime_sim__DOT__ticks 
                                       >> 0x00000010U) 
                                      | ((IData)((((QData)((IData)(vlSelfRef.session)) 
                                                   << 0x00000020U) 
                                                  | (QData)((IData)(vlSelfRef.last_sequence)))) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[40U] = (((IData)((((QData)((IData)(vlSelfRef.session)) 
                                                 << 0x00000020U) 
                                                | (QData)((IData)(vlSelfRef.last_sequence)))) 
                                       >> 0x00000010U) 
                                      | ((IData)(((
                                                   ((QData)((IData)(vlSelfRef.session)) 
                                                    << 0x00000020U) 
                                                   | (QData)((IData)(vlSelfRef.last_sequence))) 
                                                  >> 0x00000020U)) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[41U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[41U]) 
                                      | ((IData)(((
                                                   ((QData)((IData)(vlSelfRef.session)) 
                                                    << 0x00000020U) 
                                                   | (QData)((IData)(vlSelfRef.last_sequence))) 
                                                  >> 0x00000020U)) 
                                         >> 0x00000010U));
    cnc3_runtime_sim__DOT__fb[36U] = (IData)((((QData)((IData)(
                                                               (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__installed_mask) 
                                                                 << 0x00000010U) 
                                                                | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__timing_latched)))) 
                                               << 0x00000010U) 
                                              | (QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarms))));
    cnc3_runtime_sim__DOT__fb[37U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[37U]) 
                                      | (IData)(((((QData)((IData)(
                                                                   (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__installed_mask) 
                                                                     << 0x00000010U) 
                                                                    | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__timing_latched)))) 
                                                   << 0x00000010U) 
                                                  | (QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarms))) 
                                                 >> 0x00000020U)));
    cnc3_runtime_sim__DOT__fb[34U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[34U]) 
                                      | ((IData)((((QData)((IData)(
                                                                   (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarm_latched) 
                                                                     << 0x00000010U) 
                                                                    | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable)))) 
                                                   << 0x00000010U) 
                                                  | (QData)((IData)(vlSelfRef.pos_continuity)))) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[35U] = (((IData)((((QData)((IData)(
                                                                 (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarm_latched) 
                                                                   << 0x00000010U) 
                                                                  | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable)))) 
                                                 << 0x00000010U) 
                                                | (QData)((IData)(vlSelfRef.pos_continuity)))) 
                                       >> 0x00000010U) 
                                      | ((IData)(((
                                                   ((QData)((IData)(
                                                                    (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__alarm_latched) 
                                                                      << 0x00000010U) 
                                                                     | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__gen_enable)))) 
                                                    << 0x00000010U) 
                                                   | (QData)((IData)(vlSelfRef.pos_continuity))) 
                                                  >> 0x00000020U)) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[0U]);
    cnc3_runtime_sim__DOT__fb[33U] = ((0x00ffffffU 
                                       & cnc3_runtime_sim__DOT__fb[33U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000018U));
    cnc3_runtime_sim__DOT__fb[34U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[34U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[1U]);
    cnc3_runtime_sim__DOT__fb[33U] = ((0xff000000U 
                                       & cnc3_runtime_sim__DOT__fb[33U]) 
                                      | cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0);
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[2U]);
    cnc3_runtime_sim__DOT__fb[32U] = ((0x000000ffU 
                                       & cnc3_runtime_sim__DOT__fb[32U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[3U]);
    cnc3_runtime_sim__DOT__fb[31U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[31U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[32U] = ((0xffffff00U 
                                       & cnc3_runtime_sim__DOT__fb[32U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 0x00000010U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[4U]);
    cnc3_runtime_sim__DOT__fb[30U] = ((0x00ffffffU 
                                       & cnc3_runtime_sim__DOT__fb[30U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000018U));
    cnc3_runtime_sim__DOT__fb[31U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[31U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[5U]);
    cnc3_runtime_sim__DOT__fb[30U] = ((0xff000000U 
                                       & cnc3_runtime_sim__DOT__fb[30U]) 
                                      | cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0);
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[6U]);
    cnc3_runtime_sim__DOT__fb[29U] = ((0x000000ffU 
                                       & cnc3_runtime_sim__DOT__fb[29U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[7U]);
    cnc3_runtime_sim__DOT__fb[28U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[28U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[29U] = ((0xffffff00U 
                                       & cnc3_runtime_sim__DOT__fb[29U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 0x00000010U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[8U]);
    cnc3_runtime_sim__DOT__fb[27U] = ((0x00ffffffU 
                                       & cnc3_runtime_sim__DOT__fb[27U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000018U));
    cnc3_runtime_sim__DOT__fb[28U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[28U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[9U]);
    cnc3_runtime_sim__DOT__fb[27U] = ((0xff000000U 
                                       & cnc3_runtime_sim__DOT__fb[27U]) 
                                      | cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0);
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[10U]);
    cnc3_runtime_sim__DOT__fb[26U] = ((0x000000ffU 
                                       & cnc3_runtime_sim__DOT__fb[26U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
        = (0x00ffffffU & vlSelfRef.cnc3_runtime_sim__DOT__step_counts[11U]);
    cnc3_runtime_sim__DOT__fb[25U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[25U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[26U] = ((0xffffff00U 
                                       & cnc3_runtime_sim__DOT__fb[26U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hcfccde8f__0 
                                         >> 0x00000010U));
    cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
        = ((IData)(vlSelfRef.sim_ready) ? (0x00ffffffU 
                                           & vlSelfRef.cnc3_runtime_sim__DOT__encoder_counts[0U])
            : 0U);
    cnc3_runtime_sim__DOT__fb[24U] = ((0x00ffffffU 
                                       & cnc3_runtime_sim__DOT__fb[24U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
                                         << 0x00000018U));
    cnc3_runtime_sim__DOT__fb[25U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[25U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
                                         >> 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
        = ((IData)(vlSelfRef.sim_ready) ? (0x00ffffffU 
                                           & vlSelfRef.cnc3_runtime_sim__DOT__encoder_counts[1U])
            : 0U);
    cnc3_runtime_sim__DOT__fb[24U] = ((0xff000000U 
                                       & cnc3_runtime_sim__DOT__fb[24U]) 
                                      | cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0);
    cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
        = ((IData)(vlSelfRef.sim_ready) ? (0x00ffffffU 
                                           & vlSelfRef.cnc3_runtime_sim__DOT__encoder_counts[2U])
            : 0U);
    cnc3_runtime_sim__DOT__fb[23U] = ((0x000000ffU 
                                       & cnc3_runtime_sim__DOT__fb[23U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
                                         << 8U));
    cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
        = ((IData)(vlSelfRef.sim_ready) ? (0x00ffffffU 
                                           & vlSelfRef.cnc3_runtime_sim__DOT__encoder_counts[3U])
            : 0U);
    cnc3_runtime_sim__DOT__fb[16U] = (0x0000ffffU & cnc3_runtime_sim__DOT__fb[16U]);
    cnc3_runtime_sim__DOT__fb[17U] = 0U;
    cnc3_runtime_sim__DOT__fb[18U] = 0U;
    cnc3_runtime_sim__DOT__fb[19U] = 0U;
    cnc3_runtime_sim__DOT__fb[20U] = 0U;
    cnc3_runtime_sim__DOT__fb[21U] = 0U;
    cnc3_runtime_sim__DOT__fb[22U] = (cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
                                      << 0x00000010U);
    cnc3_runtime_sim__DOT__fb[23U] = ((0xffffff00U 
                                       & cnc3_runtime_sim__DOT__fb[23U]) 
                                      | (cnc3_runtime_sim__DOT____Vlvbound_hfe05e100__0 
                                         >> 0x00000010U));
    cnc3_runtime_sim__DOT__fb[15U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[15U]) 
                                      | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__encoder_illegal) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[16U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[16U]) 
                                      | (0x0000ffffU 
                                         & ((0x0000ffffU 
                                             & (IData)(vlSelfRef.__VdfgRegularize_h6e95ff9d_0_11)) 
                                            | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__encoder_illegal) 
                                               >> 0x00000010U))));
    cnc3_runtime_sim__DOT__fb[15U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[15U]) 
                                      | (0x0000000fU 
                                         & ((- (IData)((IData)(vlSelfRef.sim_ready))) 
                                            & (~ (IData)(vlSelfRef.encoder_port_valid)))));
    cnc3_runtime_sim__DOT__fb[14U] = ((0x0000ffffU 
                                       & cnc3_runtime_sim__DOT__fb[14U]) 
                                      | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__index_armed) 
                                         << 0x00000010U));
    cnc3_runtime_sim__DOT__fb[13U] = ((0xffff0000U 
                                       & cnc3_runtime_sim__DOT__fb[13U]) 
                                      | ((((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__probe_overrun) 
                                             << 6U) 
                                            | ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__probe_armed) 
                                               << 4U)) 
                                           | (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__probe_sync2) 
                                               << 2U) 
                                              | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__filtered))) 
                                          << 8U) | 
                                         (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__event_overflow) 
                                           << 7U) | 
                                          (0x0000007fU 
                                           & ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__count) 
                                              | (- (IData)(
                                                           (0x007fU 
                                                            < (IData)(vlSelfRef.cnc3_runtime_sim__DOT__events__DOT__count)))))))));
    cnc3_runtime_sim__DOT__fb[8U] = ((0xffff0000U & cnc3_runtime_sim__DOT__fb[8U]) 
                                     | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__applied));
    cnc3_runtime_sim__DOT__fb[8U] = ((0xff00ffffU & cnc3_runtime_sim__DOT__fb[8U]) 
                                     | (0x00ff0000U 
                                        & (((0x0000ffffU 
                                             & VL_DIV_III(16, (IData)(vlSelfRef.cnc3_runtime_sim__DOT__provider__DOT__age_us), (IData)(0x000aU))) 
                                            | (- (IData)(
                                                         (1U 
                                                          & (~ (IData)(vlSelfRef.sim_ready)))))) 
                                           << 0x00000010U)));
    cnc3_runtime_sim__DOT__fb[8U] = ((0x00ffffffU & cnc3_runtime_sim__DOT__fb[8U]) 
                                     | (((IData)(vlSelfRef.sim_ready)
                                          ? vlSelfRef.cnc3_runtime_sim__DOT__din
                                          : 0U) << 0x00000018U));
    cnc3_runtime_sim__DOT__fb[9U] = ((0xffff0000U & cnc3_runtime_sim__DOT__fb[9U]) 
                                     | (((IData)(vlSelfRef.sim_ready)
                                          ? vlSelfRef.cnc3_runtime_sim__DOT__din
                                          : 0U) >> 8U));
    cnc3_runtime_sim__DOT__fb[7U] = ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_faults) 
                                     << 0x00000010U);
    cnc3_runtime_sim__DOT__fb[4U] = (0x00ff0000U | 
                                     (0x0000ffffU & cnc3_runtime_sim__DOT__fb[4U]));
    cnc3_runtime_sim__DOT__fb[1U] = (IData)((((QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__safety)) 
                                              << 0x00000010U) 
                                             | (QData)((IData)(
                                                               (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__config_generation) 
                                                                 << 8U) 
                                                                | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__io_generation))))));
    cnc3_runtime_sim__DOT__fb[2U] = ((0xffff0000U & cnc3_runtime_sim__DOT__fb[2U]) 
                                     | (IData)(((((QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__safety)) 
                                                  << 0x00000010U) 
                                                 | (QData)((IData)(
                                                                   (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__config_generation) 
                                                                     << 8U) 
                                                                    | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__io_generation))))) 
                                                >> 0x00000020U)));
    VL_ASSIGN_W(752, vlSelfRef.cnc3_runtime_sim__DOT__status, Vcnc3_runtime_sim__ConstPool__CONST_h80ba4ede_0);
    vlSelfRef.cnc3_runtime_sim__DOT__status[21U] = 
        ((0x0000ffffU & vlSelfRef.cnc3_runtime_sim__DOT__status[21U]) 
         | ((IData)((0x434e533303000000ULL | (QData)((IData)(
                                                             (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                               << 0x00000010U) 
                                                              | (IData)(vlSelfRef.armed_mask)))))) 
            << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[22U] = 
        (((IData)((0x434e533303000000ULL | (QData)((IData)(
                                                           (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                             << 0x00000010U) 
                                                            | (IData)(vlSelfRef.armed_mask)))))) 
          >> 0x00000010U) | ((IData)(((0x434e533303000000ULL 
                                       | (QData)((IData)(
                                                         (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                           << 0x00000010U) 
                                                          | (IData)(vlSelfRef.armed_mask))))) 
                                      >> 0x00000020U)) 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[23U] = 
        ((IData)(((0x434e533303000000ULL | (QData)((IData)(
                                                           (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__state) 
                                                             << 0x00000010U) 
                                                            | (IData)(vlSelfRef.armed_mask))))) 
                  >> 0x00000020U)) >> 0x00000010U);
    vlSelfRef.cnc3_runtime_sim__DOT__status[17U] = 
        ((0x0000ffffU & vlSelfRef.cnc3_runtime_sim__DOT__status[17U]) 
         | (vlSelfRef.fault_word << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[18U] = 
        ((vlSelfRef.fault_word >> 0x00000010U) | (vlSelfRef.cnc3_runtime_sim__DOT__ticks 
                                                  << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[19U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__ticks >> 0x00000010U) 
         | ((IData)((((QData)((IData)(vlSelfRef.session)) 
                      << 0x00000020U) | (QData)((IData)(vlSelfRef.last_sequence)))) 
            << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[20U] = 
        (((IData)((((QData)((IData)(vlSelfRef.session)) 
                    << 0x00000020U) | (QData)((IData)(vlSelfRef.last_sequence)))) 
          >> 0x00000010U) | ((IData)(((((QData)((IData)(vlSelfRef.session)) 
                                        << 0x00000020U) 
                                       | (QData)((IData)(vlSelfRef.last_sequence))) 
                                      >> 0x00000020U)) 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[21U] = 
        ((0xffff0000U & vlSelfRef.cnc3_runtime_sim__DOT__status[21U]) 
         | ((IData)(((((QData)((IData)(vlSelfRef.session)) 
                       << 0x00000020U) | (QData)((IData)(vlSelfRef.last_sequence))) 
                     >> 0x00000020U)) >> 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[16U] = (IData)(
                                                           (((QData)((IData)(
                                                                             (((IData)(vlSelfRef.cnc3_runtime_sim__DOT__dout_image) 
                                                                               << 0x00000010U) 
                                                                              | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__applied)))) 
                                                             << 0x00000010U) 
                                                            | (QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_faults))));
    vlSelfRef.cnc3_runtime_sim__DOT__status[17U] = 
        ((0xffff0000U & vlSelfRef.cnc3_runtime_sim__DOT__status[17U]) 
         | (IData)(((((QData)((IData)((((IData)(vlSelfRef.cnc3_runtime_sim__DOT__dout_image) 
                                        << 0x00000010U) 
                                       | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__applied)))) 
                      << 0x00000010U) | (QData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT__output_faults))) 
                    >> 0x00000020U)));
    vlSelfRef.cnc3_runtime_sim__DOT__status[9U] = (
                                                   (0x0000ffffU 
                                                    & vlSelfRef.cnc3_runtime_sim__DOT__status[9U]) 
                                                   | (vlSelfRef.cnc3_runtime_sim__DOT__event_head[0U] 
                                                      << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[10U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__event_head[0U] 
          >> 0x00000010U) | (vlSelfRef.cnc3_runtime_sim__DOT__event_head[1U] 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[11U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__event_head[1U] 
          >> 0x00000010U) | (vlSelfRef.cnc3_runtime_sim__DOT__event_head[2U] 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[12U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__event_head[2U] 
          >> 0x00000010U) | (vlSelfRef.cnc3_runtime_sim__DOT__event_head[3U] 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[13U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__event_head[3U] 
          >> 0x00000010U) | (vlSelfRef.cnc3_runtime_sim__DOT__event_head[4U] 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[14U] = 
        ((vlSelfRef.cnc3_runtime_sim__DOT__event_head[4U] 
          >> 0x00000010U) | ((IData)(vlSelfRef.pos_continuity) 
                             << 0x00000010U));
    vlSelfRef.cnc3_runtime_sim__DOT__status[15U] = 
        (((0x0000ffffU & vlSelfRef.cnc3_runtime_sim__DOT__safety) 
          | ((IData)(vlSelfRef.pos_continuity) >> 0x00000010U)) 
         | (0xffff0000U & vlSelfRef.cnc3_runtime_sim__DOT__safety));
    vlSelfRef.cnc3_runtime_sim__DOT__status[9U] = (0x0000ff00U 
                                                   | vlSelfRef.cnc3_runtime_sim__DOT__status[9U]);
    vlSelfRef.cnc3_runtime_sim__DOT__status[8U] = (0xff00ffffU 
                                                   & vlSelfRef.cnc3_runtime_sim__DOT__status[8U]);
    vlSelfRef.cnc3_runtime_sim__DOT__status[0U] = 0U;
    vlSelfRef.cnc3_runtime_sim__DOT__status[1U] = 0U;
    vlSelfRef.cnc3_runtime_sim__DOT__status[3U] = (
                                                   ((IData)(vlSelfRef.cnc3_runtime_sim__DOT__interval) 
                                                    << 0x00000010U) 
                                                   | (IData)(vlSelfRef.cnc3_runtime_sim__DOT__late));
    vlSelfRef.actual_status_payload[0U] = vlSelfRef.cnc3_runtime_sim__DOT__status[0U];
    vlSelfRef.actual_status_payload[1U] = vlSelfRef.cnc3_runtime_sim__DOT__status[1U];
    vlSelfRef.actual_status_payload[2U] = vlSelfRef.cnc3_runtime_sim__DOT__status[2U];
    vlSelfRef.actual_status_payload[3U] = vlSelfRef.cnc3_runtime_sim__DOT__status[3U];
    vlSelfRef.actual_status_payload[4U] = vlSelfRef.cnc3_runtime_sim__DOT__status[4U];
    vlSelfRef.actual_status_payload[5U] = vlSelfRef.cnc3_runtime_sim__DOT__status[5U];
    vlSelfRef.actual_status_payload[6U] = vlSelfRef.cnc3_runtime_sim__DOT__status[6U];
    vlSelfRef.actual_status_payload[7U] = vlSelfRef.cnc3_runtime_sim__DOT__status[7U];
    vlSelfRef.actual_status_payload[8U] = vlSelfRef.cnc3_runtime_sim__DOT__status[8U];
    vlSelfRef.actual_status_payload[9U] = vlSelfRef.cnc3_runtime_sim__DOT__status[9U];
    vlSelfRef.actual_status_payload[10U] = vlSelfRef.cnc3_runtime_sim__DOT__status[10U];
    vlSelfRef.actual_status_payload[11U] = vlSelfRef.cnc3_runtime_sim__DOT__status[11U];
    vlSelfRef.actual_status_payload[12U] = vlSelfRef.cnc3_runtime_sim__DOT__status[12U];
    vlSelfRef.actual_status_payload[13U] = vlSelfRef.cnc3_runtime_sim__DOT__status[13U];
    vlSelfRef.actual_status_payload[14U] = vlSelfRef.cnc3_runtime_sim__DOT__status[14U];
    vlSelfRef.actual_status_payload[15U] = vlSelfRef.cnc3_runtime_sim__DOT__status[15U];
    vlSelfRef.actual_status_payload[16U] = vlSelfRef.cnc3_runtime_sim__DOT__status[16U];
    vlSelfRef.actual_status_payload[17U] = vlSelfRef.cnc3_runtime_sim__DOT__status[17U];
    vlSelfRef.actual_status_payload[18U] = vlSelfRef.cnc3_runtime_sim__DOT__status[18U];
    vlSelfRef.actual_status_payload[19U] = vlSelfRef.cnc3_runtime_sim__DOT__status[19U];
    vlSelfRef.actual_status_payload[20U] = vlSelfRef.cnc3_runtime_sim__DOT__status[20U];
    vlSelfRef.actual_status_payload[21U] = vlSelfRef.cnc3_runtime_sim__DOT__status[21U];
    vlSelfRef.actual_status_payload[22U] = vlSelfRef.cnc3_runtime_sim__DOT__status[22U];
    vlSelfRef.actual_status_payload[23U] = vlSelfRef.cnc3_runtime_sim__DOT__status[23U];
    __Vilp1 = 0U;
    while ((__Vilp1 <= 0x0000002bU)) {
        vlSelfRef.actual_feedback_payload[__Vilp1] 
            = cnc3_runtime_sim__DOT__fb[__Vilp1];
        __Vilp1 = ((IData)(1U) + __Vilp1);
    }
    if (vlSelfRef.cnc3_runtime_sim__DOT__page_pending) {
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[0U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[1U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[2U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[3U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[4U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[5U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[6U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[7U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[8U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[9U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[10U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[11U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[12U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[13U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[14U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[15U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[16U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[17U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[18U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[19U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[20U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[21U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[22U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[23U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[24U] = 0x00000032U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[25U] = 0x4d320100U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[26U] = 0x4d325349U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[27U] = 0x0000d349U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[28U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[29U] = 0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[30U] = 0x00080804U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[31U] = 0x00600802U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[32U] = 0x040000b0U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[33U] = 0xd09001f4U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[34U] = 0x03ff0003U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[35U] = 0x00640064U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[36U] = 0x00640064U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[37U] = 0x00000064U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[38U] = 0xf0800100U;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[39U] = 0x7fff02faU;
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[40U] 
            = (1U | (0x04000000U & ((- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready))) 
                                    << 0x00000018U)));
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[41U] 
            = (0x0404U | ((IData)((0x4341503303000c00ULL 
                                   | (QData)((IData)(
                                                     (0x0cU 
                                                      & (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready)))))))) 
                          << 0x00000010U));
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[42U] 
            = (((IData)((0x4341503303000c00ULL | (QData)((IData)(
                                                                 (0x0cU 
                                                                  & (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready)))))))) 
                >> 0x00000010U) | ((IData)(((0x4341503303000c00ULL 
                                             | (QData)((IData)(
                                                               (0x0cU 
                                                                & (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready))))))) 
                                            >> 0x00000020U)) 
                                   << 0x00000010U));
        vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[43U] 
            = ((IData)(((0x4341503303000c00ULL | (QData)((IData)(
                                                                 (0x0cU 
                                                                  & (- (IData)((IData)(vlSelfRef.cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready))))))) 
                        >> 0x00000020U)) >> 0x00000010U);
    } else {
        __Vilp2 = 0U;
        while ((__Vilp2 <= 0x0000002bU)) {
            vlSelfRef.cnc3_runtime_sim__DOT__transport_feedback_payload[__Vilp2] 
                = cnc3_runtime_sim__DOT__fb[__Vilp2];
            __Vilp2 = ((IData)(1U) + __Vilp2);
        }
    }
}

void Vcnc3_runtime_sim___024root___nba_sequent__TOP__0(Vcnc3_runtime_sim___024root* vlSelf);
void Vcnc3_runtime_sim___024root___nba_sequent__TOP__1(Vcnc3_runtime_sim___024root* vlSelf);

void Vcnc3_runtime_sim___024root___eval_nba(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_nba\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vcnc3_runtime_sim___024root___nba_sequent__TOP__0(vlSelf);
    }
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vcnc3_runtime_sim___024root___nba_sequent__TOP__1(vlSelf);
        Vcnc3_runtime_sim___024root___nba_sequent__TOP__2(vlSelf);
    }
    if ((3ULL & vlSelfRef.__VnbaTriggered[0U])) {
        Vcnc3_runtime_sim___024root___nba_comb__TOP__0(vlSelf);
    }
}

void Vcnc3_runtime_sim___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

void Vcnc3_runtime_sim___024root___eval_triggers_vec__act(Vcnc3_runtime_sim___024root* vlSelf);
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_runtime_sim___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

bool Vcnc3_runtime_sim___024root___eval_phase__act(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_phase__act\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vcnc3_runtime_sim___024root___eval_triggers_vec__act(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcnc3_runtime_sim___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vcnc3_runtime_sim___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

void Vcnc3_runtime_sim___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

bool Vcnc3_runtime_sim___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

bool Vcnc3_runtime_sim___024root___eval_phase__nba(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_phase__nba\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vcnc3_runtime_sim___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        Vcnc3_runtime_sim___024root___eval_nba(vlSelf);
        Vcnc3_runtime_sim___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_runtime_sim___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
bool Vcnc3_runtime_sim___024root___eval_phase__ico(Vcnc3_runtime_sim___024root* vlSelf);

void Vcnc3_runtime_sim___024root___eval(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
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
            Vcnc3_runtime_sim___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
            VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/serialized-candidate-r02/mutation-output-r01/inputs/cnc3_runtime_sim.v", 6, "", "DIDNOTCONVERGE: Input combinational region did not converge after '--converge-limit' of 10000 tries");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        vlSelfRef.__VicoPhaseResult = Vcnc3_runtime_sim___024root___eval_phase__ico(vlSelf);
        vlSelfRef.__VicoFirstIteration = 0U;
    } while (vlSelfRef.__VicoPhaseResult);
    __VnbaIterCount = 0U;
    do {
        if (VL_UNLIKELY(((0x00002710U < __VnbaIterCount)))) {
#ifdef VL_DEBUG
            Vcnc3_runtime_sim___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
            VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/serialized-candidate-r02/mutation-output-r01/inputs/cnc3_runtime_sim.v", 6, "", "DIDNOTCONVERGE: NBA region did not converge after '--converge-limit' of 10000 tries");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        vlSelfRef.__VactIterCount = 0U;
        do {
            if (VL_UNLIKELY(((0x00002710U < vlSelfRef.__VactIterCount)))) {
#ifdef VL_DEBUG
                Vcnc3_runtime_sim___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
                VL_FATAL_MT("/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/deeper-runtime-20261004/rtl/serialized-candidate-r02/mutation-output-r01/inputs/cnc3_runtime_sim.v", 6, "", "DIDNOTCONVERGE: Active region did not converge after '--converge-limit' of 10000 tries");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactPhaseResult = Vcnc3_runtime_sim___024root___eval_phase__act(vlSelf);
        } while (vlSelfRef.__VactPhaseResult);
        vlSelfRef.__VnbaPhaseResult = Vcnc3_runtime_sim___024root___eval_phase__nba(vlSelf);
    } while (vlSelfRef.__VnbaPhaseResult);
}

#ifdef VL_DEBUG
void Vcnc3_runtime_sim___024root___eval_debug_assertions(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_debug_assertions\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
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
    if (VL_UNLIKELY(((vlSelfRef.sim_context & 0xfeU)))) {
        Verilated::overWidthError("sim_context");
    }
    if (VL_UNLIKELY(((vlSelfRef.provider_strobe & 0xfeU)))) {
        Verilated::overWidthError("provider_strobe");
    }
    if (VL_UNLIKELY(((vlSelfRef.di_raw & 0xff000000U)))) {
        Verilated::overWidthError("di_raw");
    }
    if (VL_UNLIKELY(((vlSelfRef.probe_raw & 0xfcU)))) {
        Verilated::overWidthError("probe_raw");
    }
    if (VL_UNLIKELY(((vlSelfRef.home_raw & 0xf000U)))) {
        Verilated::overWidthError("home_raw");
    }
    if (VL_UNLIKELY(((vlSelfRef.limit_low_raw & 0xf000U)))) {
        Verilated::overWidthError("limit_low_raw");
    }
    if (VL_UNLIKELY(((vlSelfRef.limit_high_raw & 0xf000U)))) {
        Verilated::overWidthError("limit_high_raw");
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
    if (VL_UNLIKELY(((vlSelfRef.gate_high & 0xf0U)))) {
        Verilated::overWidthError("gate_high");
    }
    if (VL_UNLIKELY(((vlSelfRef.opi_ok & 0xf0U)))) {
        Verilated::overWidthError("opi_ok");
    }
    if (VL_UNLIKELY(((vlSelfRef.output_gate_high & 0xfeU)))) {
        Verilated::overWidthError("output_gate_high");
    }
    if (VL_UNLIKELY(((vlSelfRef.output_opi_ok & 0xfeU)))) {
        Verilated::overWidthError("output_opi_ok");
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
    if (VL_UNLIKELY(((vlSelfRef.encoder_port_valid 
                      & 0xf0U)))) {
        Verilated::overWidthError("encoder_port_valid");
    }
}
#endif  // VL_DEBUG
