// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcnc3_runtime_sim.h for the primary calling header

#include "Vcnc3_runtime_sim__pch.h"

VL_ATTR_COLD void Vcnc3_runtime_sim___024root___stl_sequent__TOP__0(Vcnc3_runtime_sim___024root* vlSelf);

VL_ATTR_COLD void Vcnc3_runtime_sim___024root___eval_stl(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_stl\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VstlTriggered[0U])) {
        Vcnc3_runtime_sim___024root___stl_sequent__TOP__0(vlSelf);
    }
}

VL_ATTR_COLD void Vcnc3_runtime_sim___024root___eval_triggers_vec__stl(Vcnc3_runtime_sim___024root* vlSelf);
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_runtime_sim___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vcnc3_runtime_sim___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);

VL_ATTR_COLD bool Vcnc3_runtime_sim___024root___eval_phase__stl(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___eval_phase__stl\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    Vcnc3_runtime_sim___024root___eval_triggers_vec__stl(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcnc3_runtime_sim___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vcnc3_runtime_sim___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        Vcnc3_runtime_sim___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

bool Vcnc3_runtime_sim___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_runtime_sim___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(Vcnc3_runtime_sim___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vcnc3_runtime_sim___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcnc3_runtime_sim___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vcnc3_runtime_sim___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @(negedge rst_n)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcnc3_runtime_sim___024root___ctor_var_reset(Vcnc3_runtime_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcnc3_runtime_sim___024root___ctor_var_reset\n"); );
    Vcnc3_runtime_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->rst_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1638864771569018232ull);
    vlSelf->spi_cs_fb_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12402125856891848400ull);
    vlSelf->spi_cs_cmd_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8267288456392658202ull);
    vlSelf->spi_sclk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11093002469780296933ull);
    vlSelf->spi_mosi = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 852284730959930751ull);
    vlSelf->spi_miso = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12140560756394917646ull);
    vlSelf->spi_miso_oe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7161913650131418674ull);
    vlSelf->sim_context = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3564425237286677219ull);
    vlSelf->sim_expected_session = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18035592848842279469ull);
    vlSelf->sim_expected_config_hash = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1963256621378598834ull);
    vlSelf->provider_strobe = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7371214688724182424ull);
    vlSelf->provider_tag = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16237049599251940266ull);
    vlSelf->provider_abi = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10174807540974389551ull);
    vlSelf->provider_session = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2029720990475806081ull);
    vlSelf->provider_config_hash = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15305910242388479736ull);
    vlSelf->provider_sequence = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5224022334564188856ull);
    vlSelf->provider_valid_mask = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 18369300864523448639ull);
    vlSelf->provider_faults = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18265583171730266525ull);
    vlSelf->di_raw = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 8279511557399104915ull);
    vlSelf->do_applied = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7783184326681510850ull);
    vlSelf->do_fault = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6919399983736766205ull);
    vlSelf->probe_raw = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 2566187738228366198ull);
    vlSelf->home_raw = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 15002287295149308592ull);
    vlSelf->limit_low_raw = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 6979328745078019651ull);
    vlSelf->limit_high_raw = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 16734137214271490759ull);
    vlSelf->inhibit_n = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17922934547812235931ull);
    vlSelf->wd_m_ok = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8843158948610480284ull);
    vlSelf->wd_o_ok = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17185550837271212109ull);
    vlSelf->reset_arm_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7817442604510828507ull);
    vlSelf->reset_arm_held = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9435734089677533524ull);
    vlSelf->contactor_deenergized = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4180277191379024323ull);
    vlSelf->sto_arm_expected = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4676158747831420222ull);
    vlSelf->gate_high = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4357042599060383773ull);
    vlSelf->opi_ok = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 3341170628593505360ull);
    vlSelf->alarm_current_raw = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 10078793961331296989ull);
    vlSelf->encoder_a = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 11441612648063742052ull);
    vlSelf->encoder_b = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 10954839163455977060ull);
    vlSelf->encoder_z = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 1622390592918392565ull);
    vlSelf->encoder_port_valid = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12303493907207305655ull);
    vlSelf->external_fault_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17231804601830245761ull);
    vlSelf->physical_safety_power_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17494359224779184386ull);
    vlSelf->step_out = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 2315470991822109059ull);
    vlSelf->dir_out = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 14357377092237351796ull);
    vlSelf->enable_n = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 6340464297242035440ull);
    vlSelf->motion_request = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8490418686795920815ull);
    vlSelf->output_request = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8244958568752421464ull);
    vlSelf->permit_out_req = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1096651371111284805ull);
    vlSelf->progress_m = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16741145116543310227ull);
    vlSelf->progress_o = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3779790157687271023ull);
    vlSelf->opi_rearm = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 300197147906394393ull);
    vlSelf->reset_arm_consumed = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2617849503668556017ull);
    vlSelf->session = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1117903709415574426ull);
    vlSelf->last_sequence = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3162154947711375904ull);
    vlSelf->fault_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1594482061587469707ull);
    vlSelf->armed_mask = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 10705487113170001815ull);
    vlSelf->pos_continuity = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 16426309159459675050ull);
    vlSelf->config_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5256005406248715760ull);
    vlSelf->selftest_passed = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 9735905300398791137ull);
    vlSelf->selftest_state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12186094684055071849ull);
    vlSelf->accepted_pulse = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6583947118193181030ull);
    vlSelf->last_reject = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 6428145810319889110ull);
    VL_SCOPED_RAND_RESET_W(1392, vlSelf->actual_feedback_payload, __VscopeHash, 13392937803645269664ull);
    VL_SCOPED_RAND_RESET_W(752, vlSelf->actual_status_payload, __VscopeHash, 1189043595014072130ull);
    vlSelf->dout_request = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 2775575176118635034ull);
    vlSelf->sim_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2054740604188468831ull);
    vlSelf->provider_error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16825307828198224960ull);
    vlSelf->provider_accepted_sequence = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9494804597982205656ull);
    vlSelf->physical_authority = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9794424533926034032ull);
    vlSelf->production_profile_complete = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1236753053505789140ull);
    vlSelf->cnc3_runtime_sim__DOT__din = VL_SCOPED_RAND_RESET_I(24, __VscopeHash, 3760539286962959647ull);
    vlSelf->cnc3_runtime_sim__DOT__applied = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3197824680036297937ull);
    vlSelf->cnc3_runtime_sim__DOT__output_faults = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12118363557300987978ull);
    vlSelf->cnc3_runtime_sim__DOT__dout_image = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8139113738582578732ull);
    vlSelf->cnc3_runtime_sim__DOT__dout_enable_mask = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5611736545668075411ull);
    vlSelf->cnc3_runtime_sim__DOT__din_limit = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4525325630058466360ull);
    vlSelf->cnc3_runtime_sim__DOT__limit_low = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 15422055946501277924ull);
    vlSelf->cnc3_runtime_sim__DOT__limit_high = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 2205208133638941882ull);
    vlSelf->cnc3_runtime_sim__DOT__io_generation = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10499618578835181477ull);
    vlSelf->cnc3_runtime_sim__DOT__io_config_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12672951951538795492ull);
    VL_SCOPED_RAND_RESET_W(432, vlSelf->cnc3_runtime_sim__DOT__io_page1, __VscopeHash, 15663201104368437700ull);
    vlSelf->cnc3_runtime_sim__DOT__event_overflow = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1346240431817893600ull);
    vlSelf->cnc3_runtime_sim__DOT__index_armed = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 17155665551117593048ull);
    vlSelf->cnc3_runtime_sim__DOT__output_mismatch = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8892763172603481103ull);
    vlSelf->cnc3_runtime_sim__DOT__mismatch_age = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14279137230707199712ull);
    vlSelf->cnc3_runtime_sim__DOT__runtime_faults = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7453270497209062107ull);
    vlSelf->cnc3_runtime_sim__DOT__page_request_accepted = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2280157447851110427ull);
    vlSelf->cnc3_runtime_sim__DOT__page_pending = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2427200368931068859ull);
    vlSelf->cnc3_runtime_sim__DOT__page_in_flight = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17918170221838304020ull);
    VL_SCOPED_RAND_RESET_W(1392, vlSelf->cnc3_runtime_sim__DOT__transport_feedback_payload, __VscopeHash, 3164959266871575170ull);
    VL_SCOPED_RAND_RESET_W(1408, vlSelf->cnc3_runtime_sim__DOT__frame, __VscopeHash, 1873808312832265475ull);
    vlSelf->cnc3_runtime_sim__DOT__frame_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9739417755621895532ull);
    vlSelf->cnc3_runtime_sim__DOT__frame_bad = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2524158554011683348ull);
    vlSelf->cnc3_runtime_sim__DOT__frame_fb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14025344947017613062ull);
    vlSelf->cnc3_runtime_sim__DOT__innergood = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17583577567640880833ull);
    vlSelf->cnc3_runtime_sim__DOT__validation_result = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 3210305216122975997ull);
    vlSelf->cnc3_runtime_sim__DOT__snapshot_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8938090783552802177ull);
    vlSelf->cnc3_runtime_sim__DOT__snapshot_fb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11550564567930543237ull);
    vlSelf->cnc3_runtime_sim__DOT__frame_rates_good = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15122947040259265471ull);
    vlSelf->cnc3_runtime_sim__DOT__rx_rate_word_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1427421463628408943ull);
    vlSelf->cnc3_runtime_sim__DOT__rate_busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10379922308327566027ull);
    vlSelf->cnc3_runtime_sim__DOT__rate_poisoned = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14278155189675805804ull);
    vlSelf->cnc3_runtime_sim__DOT__rx_rate_channel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12272512480804089137ull);
    vlSelf->cnc3_runtime_sim__DOT__rx_rate_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13064076333352711261ull);
    vlSelf->cnc3_runtime_sim__DOT__rate_channel_good = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 8027349950900505364ull);
    vlSelf->cnc3_runtime_sim__DOT__rejection_header_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 546909926017099234ull);
    vlSelf->cnc3_runtime_sim__DOT__rejection_header = VL_SCOPED_RAND_RESET_Q(48, __VscopeHash, 7251420138351985141ull);
    vlSelf->cnc3_runtime_sim__DOT__req_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18170534323224826582ull);
    vlSelf->cnc3_runtime_sim__DOT__installed_mask = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 7789602712076794197ull);
    vlSelf->cnc3_runtime_sim__DOT__required_mask = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 14871548779172525583ull);
    vlSelf->cnc3_runtime_sim__DOT__timing_latched = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 17494056816304409942ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_latched = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 2696813413026803589ull);
    vlSelf->cnc3_runtime_sim__DOT__required_encoders = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 203557332869216085ull);
    vlSelf->cnc3_runtime_sim__DOT__gen_enable = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 4150637935630602329ull);
    vlSelf->cnc3_runtime_sim__DOT__timing_fault = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 10641501612353475674ull);
    vlSelf->cnc3_runtime_sim__DOT__alarms = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 1970244072076016434ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10872672465559742956ull);
    vlSelf->cnc3_runtime_sim__DOT__stop = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7428848803958577386ull);
    vlSelf->cnc3_runtime_sim__DOT__sync_clear = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16219726079670945317ull);
    vlSelf->cnc3_runtime_sim__DOT__io = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17221138241572802209ull);
    vlSelf->cnc3_runtime_sim__DOT__ticks = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8203118965351021781ull);
    vlSelf->cnc3_runtime_sim__DOT__config_hash = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9797958396246423130ull);
    vlSelf->cnc3_runtime_sim__DOT__servo_period = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14528631006053517ull);
    vlSelf->cnc3_runtime_sim__DOT__interval = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16498366326447228128ull);
    vlSelf->cnc3_runtime_sim__DOT__late = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9611937862564621288ull);
    vlSelf->cnc3_runtime_sim__DOT__config_generation = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10859853203641981379ull);
    vlSelf->cnc3_runtime_sim__DOT__encoder_filter = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 14713684556971931501ull);
    VL_SCOPED_RAND_RESET_W(192, vlSelf->cnc3_runtime_sim__DOT__high, __VscopeHash, 8500363294839122868ull);
    VL_SCOPED_RAND_RESET_W(192, vlSelf->cnc3_runtime_sim__DOT__low, __VscopeHash, 16651744356051860690ull);
    VL_SCOPED_RAND_RESET_W(192, vlSelf->cnc3_runtime_sim__DOT__setup, __VscopeHash, 9842785465426037909ull);
    VL_SCOPED_RAND_RESET_W(192, vlSelf->cnc3_runtime_sim__DOT__hold, __VscopeHash, 9684361646552394833ull);
    VL_SCOPED_RAND_RESET_W(384, vlSelf->cnc3_runtime_sim__DOT__rates, __VscopeHash, 7986522713067196985ull);
    for (int __Vi0 = 0; __Vi0 < 12; ++__Vi0) {
        vlSelf->cnc3_runtime_sim__DOT__step_counts[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14065805218875544276ull);
    }
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->cnc3_runtime_sim__DOT__encoder_counts[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5892257741096732949ull);
    }
    vlSelf->cnc3_runtime_sim__DOT__encoder_illegal = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 9179670094810746858ull);
    vlSelf->cnc3_runtime_sim__DOT__index_pulse = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4925332035846317228ull);
    vlSelf->cnc3_runtime_sim__DOT____Vcellinp__state_machine__limit_active = 0;
    vlSelf->cnc3_runtime_sim__DOT__read_session = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2307688212474527336ull);
    vlSelf->cnc3_runtime_sim__DOT____Vcellinp__capabilities__ready = 0;
    VL_SCOPED_RAND_RESET_W(288, vlSelf->cnc3_runtime_sim__DOT__event_steps, __VscopeHash, 5704648321125113032ull);
    VL_SCOPED_RAND_RESET_W(96, vlSelf->cnc3_runtime_sim__DOT__event_encoders, __VscopeHash, 4153041444335077988ull);
    VL_SCOPED_RAND_RESET_W(96, vlSelf->cnc3_runtime_sim__DOT__event_indices, __VscopeHash, 7795772657377167547ull);
    vlSelf->cnc3_runtime_sim__DOT____Vcellinp__events__arm_commit = 0;
    VL_SCOPED_RAND_RESET_W(752, vlSelf->cnc3_runtime_sim__DOT__status, __VscopeHash, 3042491709504348774ull);
    vlSelf->cnc3_runtime_sim__DOT__safety = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 531880164416158169ull);
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__0__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__1__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__2__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__3__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__4__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__5__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__6__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__7__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__8__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__9__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__10__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber13 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__motors__BRA__11__KET____DOT__generator____pinNumber10 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__0__KET____DOT__encoder____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__0__KET____DOT__encoder____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__0__KET____DOT__encoder____pinNumber9 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__0__KET____DOT__encoder____pinNumber8 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__1__KET____DOT__encoder____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__1__KET____DOT__encoder____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__1__KET____DOT__encoder____pinNumber9 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__1__KET____DOT__encoder____pinNumber8 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__2__KET____DOT__encoder____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__2__KET____DOT__encoder____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__2__KET____DOT__encoder____pinNumber9 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__2__KET____DOT__encoder____pinNumber8 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__3__KET____DOT__encoder____pinNumber12 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__3__KET____DOT__encoder____pinNumber11 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__3__KET____DOT__encoder____pinNumber9 = 0;
    vlSelf->cnc3_runtime_sim__DOT____Vcellout__encoders__BRA__3__KET____DOT__encoder____pinNumber8 = 0;
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__seen = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12077026451119158306ull);
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__age_us = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9697976656324108273ull);
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__subtick = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 8471122926861496962ull);
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__bound_session = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11612335153880654988ull);
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__bound_hash = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 18172419629081049584ull);
    vlSelf->cnc3_runtime_sim__DOT__provider__DOT__stale = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11667032472373220753ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__fb_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17975920332110503258ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__cmd_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12657917399341263106ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__sck_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 6328457524889221546ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__mosi_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 16384502189638309680ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__fb_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6776089874187966ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__cmd_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16862673094892052844ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__sck_rise = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8317130915549772332ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__sck_fall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15436354425321456854ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__both_low = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4374383613825459401ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__active = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1465754625089011806ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__selected_fb = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6928840137400618092ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__invalid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3925058909869779028ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__rise_d = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4031784569438951203ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__bit_count = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 13091760078026402581ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__expected_bits = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 10528213502496157635ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__body_bits = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 2539676218025330079ull);
    VL_SCOPED_RAND_RESET_W(1408, vlSelf->cnc3_runtime_sim__DOT__transport__DOT__rx_shift, __VscopeHash, 1800245489400428961ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__rx_header = VL_SCOPED_RAND_RESET_Q(48, __VscopeHash, 7285735828401787750ull);
    VL_SCOPED_RAND_RESET_W(1392, vlSelf->cnc3_runtime_sim__DOT__transport__DOT__tx_shift, __VscopeHash, 6506435264363953863ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__rx_crc = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9999418232102279201ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__tx_crc = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11933463129836872936ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__inner_crc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4376632582473176322ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__ticks = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6801829323587495819ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__start_tick = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6020580883654415325ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__last_rise_tick = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1748802804067426575ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__last_fall_tick = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4794415371818171022ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__last_end_tick = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3468100581709655940ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__seen_rise = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3993959157720195039ull);
    vlSelf->cnc3_runtime_sim__DOT__transport__DOT__seen_fall = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11550860977994478595ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT____Vlvbound_h12f7ff73__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__expected_channel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 1116922464443108732ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__active_channel = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 17790055138619873024ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__iteration = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 661735154105845773ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__multiplier = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 889198030299445739ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__multiplicand = VL_SCOPED_RAND_RESET_Q(36, __VscopeHash, 3454148865012525263ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__accumulator = VL_SCOPED_RAND_RESET_Q(36, __VscopeHash, 17216825473457280357ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__base_good = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14096112016324020182ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__magnitude = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7118803986447732455ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__high_value = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13393342854097410467ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__low_value = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3930155225940291384ull);
    vlSelf->cnc3_runtime_sim__DOT__admission__DOT__product_next = VL_SCOPED_RAND_RESET_Q(36, __VscopeHash, 8491261124356007346ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT____Vlvbound_h6de1313f__3 = 0;
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT____Vlvbound_h11e7cfda__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT____Vlvbound_ha44c8868__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__s0 = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 17588662520224683400ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__s1 = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 2501556767053370686ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__s2 = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 7969043841902386673ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__candidate = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 15630616003201911019ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__sample_age = VL_SCOPED_RAND_RESET_I(9, __VscopeHash, 9981257161786698545ull);
    vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__samples_seen = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 13959752191466768429ull);
    for (int __Vi0 = 0; __Vi0 < 12; ++__Vi0) {
        vlSelf->cnc3_runtime_sim__DOT__alarm_filter__DOT__stable[__Vi0] = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 11126178840302278861ull);
    }
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT____Vlvbound_h830afaea__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT____Vlvbound_h727ddc32__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT____Vlvbound_hee0ba6e2__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT____Vlvbound_ha25ef3ae__0 = 0;
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__cycle_faults = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2901631073533926050ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__alarm_trip_mask = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 4794039458108213762ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__alarm_on_no_current = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 6058225959909817346ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__expected_module_class = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 4946978060340386864ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__qualification_latched = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8198456689064921189ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__qualification_class = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 4479020100290544099ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__arming = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 894363092583002080ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__arming_rearmed = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9426020779199054619ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__stopping = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15189208198721138942ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__disarm_proof = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6433322092166541710ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__arming_age = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 12208045282516838938ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__disarm_age = VL_SCOPED_RAND_RESET_I(10, __VscopeHash, 16997541016957742840ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__proof_domains = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 8616218288118739386ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__watchdog_age = VL_SCOPED_RAND_RESET_I(18, __VscopeHash, 4448944091870657731ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__test_age = VL_SCOPED_RAND_RESET_I(20, __VscopeHash, 6128932417429495025ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__progress_left = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 1139043944617134809ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__output_progress_left = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 6227037755260502958ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__io_watchdog_age = VL_SCOPED_RAND_RESET_I(18, __VscopeHash, 4594403816952736950ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__io_page1_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3533302318400066290ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__io_payload_ok = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9059208838801248630ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__output_conditions = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6991520312818185449ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__capture_sources_supported = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16251380399454972118ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__last_update_tick = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7338264845923633994ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__update_us_age = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4348227995409724291ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__update_subtick = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 2170623237058711577ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__next_sequence = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12213918790827102249ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__active_domains = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6263805614105281122ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__asserted_alarm = VL_SCOPED_RAND_RESET_I(12, __VscopeHash, 14502483799599702712ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__cfg_session = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9254195190340390727ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__idle = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1412970660482994338ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__qualification_changed = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1597679288110745766ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__cfg_semantic = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8598207526751718314ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__motion_runtime_fault = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12931721879313057232ull);
    vlSelf->cnc3_runtime_sim__DOT__state_machine__DOT__update_admissible = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13090486343038717451ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT____Vlvbound_hdb641091__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 256; ++__Vi0) {
        VL_SCOPED_RAND_RESET_W(160, vlSelf->cnc3_runtime_sim__DOT__events__DOT__records[__Vi0], __VscopeHash, 5728312650028963672ull);
    }
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__rd = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5475370720866065371ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__wr = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1470180367469880994ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__next_sequence = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 4801401417546860514ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__count = VL_SCOPED_RAND_RESET_I(9, __VscopeHash, 16343250385900206966ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__index_level = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4150548740603770195ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__probe_level = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 13174563552987174404ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__probe_armed = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1975499322150295921ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__probe_overrun = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1279290458372936380ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__probe_sync1 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 13525617888031825990ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__probe_sync2 = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 14047335933729020280ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__filtered = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1554771354827712266ull);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->cnc3_runtime_sim__DOT__events__DOT__stable[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 4886566574685568552ull);
    }
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__previous_fault = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 676153729075966844ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__temp_count = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15298755718443516770ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__temp_wr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16921712909356638063ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__temp_sequence = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8585081951018635623ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__next_filtered = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 15889893910271209046ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__edges = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 453370809072183894ull);
    VL_SCOPED_RAND_RESET_W(96, vlSelf->cnc3_runtime_sim__DOT__events__DOT__values, __VscopeHash, 16522117618433330547ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__source = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5609542710296836881ull);
    vlSelf->cnc3_runtime_sim__DOT__events__DOT__newly_set = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4422082531922906299ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7305758354673140606ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4268669416606866789ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8443297064307145312ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 557179300174967359ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15143513996080078016ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__0__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 1549351266957118292ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13555489671405640378ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12048925049045495326ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3727273350174167739ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13852720087437891060ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8842388849657796492ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__1__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 5881703263615477008ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14167635689596536931ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7933564708891872911ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15097162263459718891ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9326685844505858236ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5100533046528888107ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__2__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 10856385865655553594ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3074898715151906711ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 18317725293070413365ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1834252850552143413ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11224331248891926501ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15610440445257245298ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__3__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 3881382255136236790ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7532634646617820404ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17951256008717069669ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1569580329596825507ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11272987155220485710ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7152979583472862553ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__4__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 262572055130869495ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12463263591587901941ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15296460910359392058ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1863577936642123658ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16377323190538904021ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1415037178581493192ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__5__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 15479215548604281855ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5241961165441982507ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12397308895208717091ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15480923103789328659ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13846980559473261148ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12925293538061088981ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__6__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 7457011655931992646ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12812498185285694576ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4708173335034648767ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4208221257233176676ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 10093386688391642008ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3576045603550692909ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__7__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 7490047004927611480ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3279379647993074352ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 18291296559326430414ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 17050022343957273366ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16226390188817913533ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 11432373269766925080ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__8__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 15320903745414652133ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 401264055885670839ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13734921308661492373ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 4446601231595612564ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6692676804482067053ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3275530516922243521ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__9__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 17506803750217370388ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15985492912642436135ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14783888473018329542ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14952754353970117412ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15117565364569499208ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9218154614961545639ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__10__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 907465694130465602ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__phase = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14648983330729049658ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__high_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15705267545954803730ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__low_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12674707676487678285ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__setup_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 9516453259588719455ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__hold_left = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 15373969267033015788ull);
    vlSelf->cnc3_runtime_sim__DOT__motors__BRA__11__KET____DOT__generator__DOT__sum = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 10484909095245495458ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__a_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12168881057348252018ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__b_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 4576977677995089428ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__z_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 5667088482026465270ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__filtered = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3593811471072094814ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__stable_a = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6527914768312834502ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__stable_b = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 9135750884366859969ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__stable_z = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 5367255919181850529ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__sampled = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12454648313893292667ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__observed = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17240544895354641737ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__previous_ab = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 11566026110240526125ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__previous_z = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2724645938314063828ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__0__KET____DOT__encoder__DOT__next_count = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13755306861858125694ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__a_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 1899099835882782232ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__b_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 342489580109025296ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__z_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 4734217181690220669ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__filtered = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 15024350654221321718ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__stable_a = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 9234847068243844463ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__stable_b = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 2795690794863052023ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__stable_z = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 4555255768805553363ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__sampled = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 1551547621109272901ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__observed = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12155364023100573909ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__previous_ab = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 3502551332703502521ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__previous_z = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9503418239017394230ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__1__KET____DOT__encoder__DOT__next_count = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2498050996344711793ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__a_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17164141465052224694ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__b_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3190519254812791056ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__z_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 4753255040591565563ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__filtered = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 11946142407442231187ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__stable_a = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6505193705493284190ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__stable_b = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 16633389549781313151ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__stable_z = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 236013295205186119ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__sampled = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 740627056542105073ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__observed = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 5434600854628897675ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__previous_ab = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 7868112894480097270ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__previous_z = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 406875785136453562ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__2__KET____DOT__encoder__DOT__next_count = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10057897552574231719ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__a_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3417250374690655480ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__b_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 11191711397073486010ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__z_sync = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 8617824274710393306ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__filtered = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 17092765941150740591ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__stable_a = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 6370812601223966395ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__stable_b = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 9239085254009466379ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__stable_z = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12345706182231303089ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__sampled = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 2264752765390469814ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__observed = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 12037863101834878850ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__previous_ab = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 15885226384286094430ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__previous_z = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16256686923229421251ull);
    vlSelf->cnc3_runtime_sim__DOT__encoders__BRA__3__KET____DOT__encoder__DOT__next_count = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 563400227382297974ull);
    vlSelf->__VdfgRegularize_h6e95ff9d_0_1 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_10 = 0;
    vlSelf->__VdfgRegularize_h6e95ff9d_0_11 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rst_n__0 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
