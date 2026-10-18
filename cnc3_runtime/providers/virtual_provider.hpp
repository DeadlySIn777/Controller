// Explicitly disconnected virtual mechanics and providers for CNC3 SIM2.
// Inputs come from actual RTL pins. No OS/device/network transport exists here.
#pragma once
#include "provider_ledger.hpp"
#include <array>
#include <cstdint>
#include <limits>
#include <stdexcept>

namespace cnc3_sim {
constexpr uint16_t all_motors = 0x0fff;
struct PlantConfig {
    // Integer electrical-step coordinates avoid floating point drift. Scale to
    // machine units belongs the host's explicitly configured simulation profile.
    std::array<int64_t, 12> initial{};
    std::array<int64_t, 12> minimum{};
    std::array<int64_t, 12> maximum{};
    std::array<int64_t, 12> home{};
    std::array<uint32_t, 4> encoder_edges_per_rev{{3200,3200,3200,3200}};
    std::array<uint32_t, 4> motor_steps_per_rev{{3200,3200,3200,3200}};
    uint16_t alarm_on_no_current = 0;
    int64_t probe_surface = 0;
    unsigned probe_joint = 2;
    uint64_t watchdog_timeout = 550000;  // 11 ms virtual core; no electrical claim.
    uint64_t watchdog_recovery = 100;
    uint64_t reset_debounce = 2500000;  // Frozen chosen IO profile: 50 ms press.
    uint64_t reset_press_max = 250000000, reset_window = 250000000; // 5 s.
    uint64_t gate_delay = 100;
    PlantConfig() { initial.fill(10000); maximum.fill(100000); }
    void validate() const {
        if (probe_joint >= 12 || alarm_on_no_current & ~all_motors || watchdog_timeout < 453000 || watchdog_timeout > 668500 ||
            !watchdog_recovery || reset_debounce < 2500000 || reset_debounce > reset_press_max ||
            reset_press_max > 250000000 || !reset_window || reset_window > 250000000 || !gate_delay)
            throw std::invalid_argument("invalid virtual provider timing/probe");
        for (unsigned i = 0; i < 12; ++i)
            if (minimum[i] >= maximum[i] || initial[i] < minimum[i] || initial[i] > maximum[i] ||
                home[i] < minimum[i] || home[i] > maximum[i])
                throw std::invalid_argument("invalid integer plant geometry");
        for (unsigned i = 0; i < 4; ++i) if (encoder_edges_per_rev[i] < 4 || encoder_edges_per_rev[i] != motor_steps_per_rev[i])
            throw std::invalid_argument("only explicit one-encoder-edge-per-STEP fixture is supported");
    }
};

struct RtlOutputs {
    uint16_t step_out = 0, dir_out = 0, enable_n = all_motors, armed_mask = 0;
    uint16_t dout_request = 0;
    bool motion_request = false, output_request = false, permit_out_req = false;
    bool progress_m = false, progress_o = false, reset_arm_consumed = false, output_opi_rearm = false;
    uint8_t opi_rearm = 0, selftest_state = 0;
};
struct SimInputs {
    bool sim_context = false;
    uint32_t sim_expected_session = 0, sim_expected_config_hash = 0;
    bool provider_strobe = false;
    uint32_t provider_tag = cnc3_sim::provider_tag;
    uint8_t provider_abi = cnc3_sim::provider_abi;
    uint32_t provider_session = 0, provider_config_hash = 0, provider_sequence = 0;
    uint8_t provider_valid_mask = 0;
    uint32_t provider_faults = 0, di_raw = 0;
    uint16_t do_applied = 0, do_fault = 0;
    uint8_t probe_raw = 0, encoder_a = 0, encoder_b = 0, encoder_z = 0, encoder_port_valid = 0;
    uint16_t home_raw = 0, limit_low_raw = 0, limit_high_raw = 0, alarm_current_raw = 0;
    bool inhibit_n = false, wd_m_ok = true, wd_o_ok = true;
    bool reset_arm_ready = false, reset_arm_held = false, contactor_deenergized = true;
    bool sto_arm_expected = true;
    uint8_t gate_high = 0, opi_ok = 0;
    bool output_gate_high = false, output_opi_ok = false;
    bool provider_healthy = false;
    uint64_t provider_age_ticks = std::numeric_limits<uint64_t>::max();
    static constexpr bool physical_authority = false;
    static constexpr bool production_profile_complete = false;
};
struct Faults {
    uint16_t stalled_motors = 0, reverse_motors = 0, alarm_mask = 0;
    uint16_t do_open = 0, do_short = 0;
    uint16_t limit_low_mask = 0, limit_high_mask = 0;
    uint8_t encoder_unplug = 0;
    bool inhibit = false, watchdog_m = false, watchdog_o = false;
    bool motor_gate_stuck_off = false, output_gate_stuck_off = false;
    bool pause_heartbeat = false, corrupt_crc = false, foreign_session = false;
    bool foreign_config = false, foreign_source = false, skipped_sequence = false;
    bool replay_sequence = false, reverse_timestamp = false, reported_provider_fault = false;
    void validate() const {
        if ((stalled_motors | reverse_motors | alarm_mask | limit_low_mask | limit_high_mask) & ~all_motors || encoder_unplug & 0xf0u)
            throw std::invalid_argument("unsupported virtual fault bit");
    }
};
struct PlantMetrics {
    std::array<int64_t, 12> position{};
    std::array<uint64_t, 12> observed_rises{}, accepted_rises{}, inhibited_rises{};
    std::array<int64_t, 4> encoder_count{};
    std::array<uint64_t, 4> encoder_edges{}, index_rises{};
    uint64_t accepted_provider_records = 0, rejected_provider_records = 0;
    uint64_t applied_output_changes = 0, watchdog_m_drops = 0, watchdog_o_drops = 0;
    uint64_t watchdog_m_recoveries = 0, watchdog_o_recoveries = 0;
    uint64_t reset_press_events = 0;
    uint16_t applied_outputs = 0;
    uint32_t provider_sequence = 0;
};

class VirtualWatchdog {
    uint64_t timeout_, recovery_, feed_ = 0, idle_since_ = 0;
    bool previous_request_ = false, previous_progress_ = false, previous_forced_fault_ = false, healthy_ = true;
public:
    VirtualWatchdog(uint64_t timeout, uint64_t recovery) : timeout_(timeout), recovery_(recovery) {}
    bool tick(uint64_t now, bool request, bool progress, bool forced_fault) {
        if (request && (!previous_request_ || (progress && !previous_progress_))) feed_ = now;
        if (!request && (previous_request_ || (previous_forced_fault_ && !forced_fault))) idle_since_ = now;
        if (forced_fault) healthy_ = false;
        else if (request) { if (now - feed_ >= timeout_) healthy_ = false; }
        else if (now - idle_since_ >= recovery_) healthy_ = true;
        previous_request_ = request; previous_progress_ = progress; previous_forced_fault_ = forced_fault;
        return healthy_;
    }
    void reset() { feed_ = idle_since_ = 0; previous_request_ = previous_progress_ = previous_forced_fault_ = false; healthy_ = true; }
};

class ProviderPlant {
    SimulationIdentity identity_;
    PlantConfig config_;
    ProviderLedger ledger_;
    VirtualWatchdog watchdog_m_, watchdog_o_;
    PlantMetrics metrics_{};
    Faults faults_{};
    SimInputs inputs_{};
    uint64_t last_tick_ = 0, last_sample_ = 0, press_start_ = 0, ready_since_ = 0;
    std::array<uint64_t, 4> rearm_tick_{};
    uint64_t motor_gate_start_ = 0, output_gate_start_ = 0, output_rearm_tick_ = 0;
    uint16_t previous_step_ = 0;
    uint8_t previous_index_ = 0, rearmed_ = 0;
    bool started_ = false, have_sample_ = false, reset_button_ = false;
    bool previous_button_ = false, ready_ = false, press_consumed_ = false;
    bool previous_motor_request_ = false, previous_output_request_ = false, output_rearmed_ = false;
    uint32_t next_sequence_ = 1;
    static int64_t mod(int64_t value, int64_t period) { auto result = value % period; return result < 0 ? result + period : result; }
    void acquire_sensors(SimInputs& result) {
        for (unsigned i = 0; i < 12; ++i) {
            const uint16_t bit = uint16_t(1u << i);
            if (metrics_.position[i] == config_.home[i]) result.home_raw |= bit;
            if (metrics_.position[i] <= config_.minimum[i]) result.limit_low_raw |= bit;
            if (metrics_.position[i] >= config_.maximum[i]) result.limit_high_raw |= bit;
        }
        result.limit_low_raw |= faults_.limit_low_mask;
        result.limit_high_raw |= faults_.limit_high_mask;
        // General DI has its own explicit stimulus. Geometry-derived home and
        // limit observations use separate provider ports; no pin allocation is
        // silently inferred from their existence.
        result.di_raw = manual_di_;
        result.probe_raw = manual_probe_;
        if (metrics_.position[config_.probe_joint] <= config_.probe_surface) result.probe_raw |= 1;
        result.encoder_port_valid = uint8_t(0x0f & ~faults_.encoder_unplug);
        static constexpr uint8_t gray[] = {0, 1, 3, 2};
        for (unsigned i = 0; i < 4; ++i) {
            if (!(result.encoder_port_valid & (1u << i))) continue;
            const auto count = metrics_.position[i];
            const auto code = gray[mod(count, 4)];
            if (code & 2) result.encoder_a |= uint8_t(1u << i);
            if (code & 1) result.encoder_b |= uint8_t(1u << i);
            if (mod(count, config_.encoder_edges_per_rev[i]) == 0) result.encoder_z |= uint8_t(1u << i);
            metrics_.encoder_count[i] = count;
        }
        const uint8_t index_rises = uint8_t(result.encoder_z & ~previous_index_);
        for (unsigned i = 0; i < 4; ++i) if (index_rises & (1u << i)) ++metrics_.index_rises[i];
        previous_index_ = result.encoder_z;
    }
    uint32_t manual_di_ = 0;
    uint8_t manual_probe_ = 0;
public:
    explicit ProviderPlant(SimulationIdentity identity, PlantConfig config = {})
        : identity_(identity), config_(config), ledger_(identity),
          watchdog_m_(config.watchdog_timeout, config.watchdog_recovery),
          watchdog_o_(config.watchdog_timeout, config.watchdog_recovery) {
        identity_.validate(); config_.validate(); metrics_.position = config_.initial;
    }
    void set_faults(Faults faults) { faults.validate(); faults_ = faults; }
    void set_inputs(uint32_t di, uint8_t probe = 0) {
        if (di & 0xff000000u || probe & 0xfcu) throw std::invalid_argument("unsupported DI/probe bit");
        manual_di_ = di; manual_probe_ = probe;
    }
    void set_reset_button(bool pressed) { reset_button_ = pressed; }
    void reset_context(SimulationIdentity next) {
        ledger_.reset_context(next); identity_ = next;
        have_sample_ = false; next_sequence_ = 1; ready_ = false;
        previous_button_ = reset_button_; press_consumed_ = reset_button_; rearmed_ = 0;
        previous_motor_request_ = previous_output_request_ = output_rearmed_ = false;
        metrics_.applied_outputs = 0; inputs_ = {};
    }
    const SimulationIdentity& identity() const { return identity_; }
    const PlantMetrics& metrics() const { return metrics_; }
    const SimInputs& inputs() const { return inputs_; }
    ProviderError error() const { return ledger_.error(); }
    SimInputs tick(uint64_t tick, RtlOutputs outputs) {
        if (started_ && (last_tick_ == std::numeric_limits<uint64_t>::max() || tick != last_tick_ + 1))
            throw std::invalid_argument("provider must observe every monotonically increasing core tick");
        if ((outputs.step_out | outputs.dir_out | outputs.enable_n | outputs.armed_mask) & ~all_motors || outputs.opi_rearm & 0xf0u || outputs.selftest_state > 4)
            throw std::invalid_argument("unsupported runtime pin/state");
        started_ = true; last_tick_ = tick;
        SimInputs result;
        result.sim_context = identity_.allow_disconnected_simulation;
        result.sim_expected_session = result.provider_session = identity_.session;
        result.sim_expected_config_hash = result.provider_config_hash = identity_.config_hash;
        const bool previous_wm = inputs_.wd_m_ok, previous_wo = inputs_.wd_o_ok;
        result.wd_m_ok = watchdog_m_.tick(tick, outputs.motion_request, outputs.progress_m, faults_.watchdog_m);
        result.wd_o_ok = watchdog_o_.tick(tick, outputs.output_request, outputs.progress_o, faults_.watchdog_o);
        if (previous_wm && !result.wd_m_ok) ++metrics_.watchdog_m_drops;
        if (!previous_wm && result.wd_m_ok) ++metrics_.watchdog_m_recoveries;
        if (previous_wo && !result.wd_o_ok) ++metrics_.watchdog_o_drops;
        if (!previous_wo && result.wd_o_ok) ++metrics_.watchdog_o_recoveries;
        if (reset_button_ && !previous_button_) { press_start_ = tick; press_consumed_ = false; ++metrics_.reset_press_events; }
        if (reset_button_ && !press_consumed_ && tick - press_start_ >= config_.reset_debounce) ready_ = true;
        if (reset_button_ && tick - press_start_ > config_.reset_press_max) { ready_ = false; press_consumed_ = true; }
        if (!reset_button_ && previous_button_ && ready_) ready_since_ = tick;
        if (!reset_button_ && ready_ && tick - ready_since_ > config_.reset_window) ready_ = false;
        if (outputs.reset_arm_consumed) { ready_ = false; press_consumed_ = true; }
        previous_button_ = reset_button_;
        result.reset_arm_ready = ready_; result.reset_arm_held = reset_button_;

        const uint16_t rises = uint16_t(outputs.step_out & ~previous_step_);
        previous_step_ = outputs.step_out;
        // Mechanical movement follows emitted STEP, the actual simulated
        // permission chain, and individual enables. Commands never move it.
        const bool was_healthy = ledger_.has_record() && ledger_.healthy(tick);
        const bool motion_allowed = was_healthy && !faults_.inhibit && !faults_.motor_gate_stuck_off &&
            result.wd_m_ok && outputs.permit_out_req && outputs.motion_request && outputs.armed_mask != 0;
        for (unsigned i = 0; i < 12; ++i) if (rises & (1u << i)) {
            ++metrics_.observed_rises[i];
            const uint8_t needed = i < 8 ? 3 : 15;
            if (!motion_allowed || !(outputs.armed_mask & (1u << i)) || (inputs_.gate_high & needed) != needed || (inputs_.opi_ok & needed) != needed || outputs.enable_n & (1u << i)) {
                ++metrics_.inhibited_rises[i]; continue;
            }
            ++metrics_.accepted_rises[i];
            if (faults_.stalled_motors & (1u << i)) continue;
            int step = outputs.dir_out & (1u << i) ? -1 : 1;
            if (faults_.reverse_motors & (1u << i)) step = -step;
            auto& position = metrics_.position[i];
            if ((step > 0 && position < config_.maximum[i]) || (step < 0 && position > config_.minimum[i])) {
                position += step;
                if (i < 4) ++metrics_.encoder_edges[i];
            }
        }
        acquire_sensors(result);
        result.alarm_current_raw = uint16_t(faults_.alarm_mask ^ config_.alarm_on_no_current);
        result.do_fault = uint16_t(faults_.do_open | faults_.do_short);
        // The applied image is feedback from this separate device model. An
        // open/short injection is observable independently of the request.
        const bool io_allowed = was_healthy && !faults_.inhibit && !faults_.output_gate_stuck_off && result.wd_o_ok &&
            outputs.output_request && inputs_.output_gate_high && inputs_.output_opi_ok;
        result.do_applied = io_allowed ? uint16_t(outputs.dout_request & ~faults_.do_open) : 0;
        result.do_applied |= faults_.do_short;
        if (result.do_applied != metrics_.applied_outputs) ++metrics_.applied_output_changes;
        metrics_.applied_outputs = result.do_applied;

        if ((!have_sample_ || tick - last_sample_ >= heartbeat_ticks) && !faults_.pause_heartbeat) {
            ProviderRecord record;
            record.session = identity_.session; record.config_hash = identity_.config_hash; record.source_id = identity_.source_id;
            record.config_digest = identity_.config_digest; record.source_digest = identity_.source_digest;
            record.sequence = next_sequence_; record.captured_tick = tick;
            record.valid_mask = required_provider_mask; record.di = result.di_raw;
            record.do_applied = result.do_applied; record.do_fault = result.do_fault;
            record.home = result.home_raw; record.limit_low = result.limit_low_raw; record.limit_high = result.limit_high_raw;
            record.probe = result.probe_raw; record.encoder_a = result.encoder_a; record.encoder_b = result.encoder_b;
            record.encoder_z = result.encoder_z; record.encoder_valid = result.encoder_port_valid;
            if (faults_.foreign_session) record.session ^= 1;
            if (faults_.foreign_config) record.config_hash ^= 1;
            if (faults_.foreign_source) record.source_id ^= 1;
            if (faults_.skipped_sequence) ++record.sequence;
            if (faults_.replay_sequence) record.sequence = ledger_.accepted().sequence;
            if (faults_.reverse_timestamp && have_sample_) record.captured_tick = last_sample_;
            if (faults_.reported_provider_fault) record.faults = 1;
            record.seal(); if (faults_.corrupt_crc) record.crc ^= 1;
            result.provider_strobe = true; last_sample_ = tick; have_sample_ = true;
            if (ledger_.accept(record, tick)) {
                ++metrics_.accepted_provider_records;
                if (next_sequence_ != std::numeric_limits<uint32_t>::max()) ++next_sequence_;
            } else ++metrics_.rejected_provider_records;
        }
        result.provider_healthy = ledger_.healthy(tick);
        result.provider_sequence = ledger_.accepted().sequence;
        metrics_.provider_sequence = result.provider_sequence;
        result.provider_valid_mask = result.provider_healthy ? required_provider_mask : 0;
        result.provider_faults = static_cast<uint32_t>(ledger_.error());
        if (ledger_.has_record()) result.provider_age_ticks = tick - ledger_.accepted().captured_tick;
        result.inhibit_n = result.provider_healthy && !faults_.inhibit;
        if (!result.provider_healthy) result.encoder_port_valid = 0;
        // Independent causal observations: requested gate first rises after a
        // delay. Only a later runtime rearm pulse can restore that gate's OPI.
        // All four retained motor domains are distinct from the general OUT gate.
        const bool motor_requested = outputs.motion_request && outputs.permit_out_req && outputs.armed_mask != 0 &&
            result.inhibit_n && result.wd_m_ok && !faults_.motor_gate_stuck_off;
        if (motor_requested && !previous_motor_request_) motor_gate_start_ = tick;
        const uint8_t motor_domains = outputs.armed_mask & 0xf00 ? 15 : 3;
        if (motor_requested && tick - motor_gate_start_ >= config_.gate_delay) result.gate_high = motor_domains;
        for (unsigned domain = 0; domain < 4; ++domain) {
            const uint8_t bit = uint8_t(1u << domain);
            if (!(result.gate_high & bit)) rearmed_ &= uint8_t(~bit);
            if ((outputs.opi_rearm & bit) && (inputs_.gate_high & bit) && (result.gate_high & bit)) {
                rearmed_ |= bit; rearm_tick_[domain] = tick;
            }
            if ((rearmed_ & bit) && tick - rearm_tick_[domain] >= config_.gate_delay) result.opi_ok |= bit;
        }
        previous_motor_request_ = motor_requested;
        const bool output_requested = outputs.output_request && result.inhibit_n && result.wd_o_ok && !faults_.output_gate_stuck_off;
        if (output_requested && !previous_output_request_) output_gate_start_ = tick;
        result.output_gate_high = output_requested && tick - output_gate_start_ >= config_.gate_delay;
        if (!result.output_gate_high) output_rearmed_ = false;
        if (outputs.output_opi_rearm && inputs_.output_gate_high && result.output_gate_high) {
            output_rearmed_ = true; output_rearm_tick_ = tick;
        }
        result.output_opi_ok = output_rearmed_ && tick - output_rearm_tick_ >= config_.gate_delay;
        previous_output_request_ = output_requested;
        result.contactor_deenergized = result.gate_high == 0;
        inputs_ = result; return result;
    }
};

// Single agreed port mapping. It does not open a device or substitute response
// bytes; transport must shift the actual compiled RTL SPI pins separately.
template<class Top> inline void drive_inputs(Top& top, const SimInputs& in) {
    top.sim_context = in.sim_context;
    top.sim_expected_session = in.sim_expected_session;
    top.sim_expected_config_hash = in.sim_expected_config_hash;
    top.provider_strobe = in.provider_strobe; top.provider_tag = in.provider_tag; top.provider_abi = in.provider_abi;
    top.provider_session = in.provider_session; top.provider_config_hash = in.provider_config_hash;
    top.provider_sequence = in.provider_sequence; top.provider_valid_mask = in.provider_valid_mask;
    top.provider_faults = in.provider_faults; top.di_raw = in.di_raw;
    top.do_applied = in.do_applied; top.do_fault = in.do_fault; top.probe_raw = in.probe_raw;
    top.home_raw = in.home_raw; top.limit_low_raw = in.limit_low_raw; top.limit_high_raw = in.limit_high_raw;
    top.encoder_a = in.encoder_a; top.encoder_b = in.encoder_b; top.encoder_z = in.encoder_z;
    top.encoder_port_valid = in.encoder_port_valid; top.alarm_current_raw = in.alarm_current_raw;
    top.inhibit_n = in.inhibit_n; top.wd_m_ok = in.wd_m_ok; top.wd_o_ok = in.wd_o_ok;
    top.reset_arm_ready = in.reset_arm_ready; top.reset_arm_held = in.reset_arm_held;
    top.contactor_deenergized = in.contactor_deenergized; top.sto_arm_expected = in.sto_arm_expected;
    top.gate_high = in.gate_high; top.opi_ok = in.opi_ok;
    top.output_gate_high = in.output_gate_high; top.output_opi_ok = in.output_opi_ok;
}
template<class Top> inline RtlOutputs observe_outputs(const Top& top) {
    RtlOutputs out;
    out.step_out = top.step_out; out.dir_out = top.dir_out; out.enable_n = top.enable_n;
    out.armed_mask = top.armed_mask;
    out.dout_request = top.dout_request; out.motion_request = top.motion_request;
    out.output_request = top.output_request; out.permit_out_req = top.permit_out_req;
    out.progress_m = top.progress_m; out.progress_o = top.progress_o;
    out.opi_rearm = top.opi_rearm; out.reset_arm_consumed = top.reset_arm_consumed;
    out.selftest_state = top.selftest_state;
    out.output_opi_rearm = top.output_opi_rearm;
    return out;
}
}  // namespace cnc3_sim
