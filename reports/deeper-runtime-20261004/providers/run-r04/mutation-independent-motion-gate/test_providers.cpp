#include "virtual_provider.hpp"
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace cnc3_sim;
static unsigned checks = 0;
static void check(bool value, const char* explanation) {
    ++checks; if (!value) throw std::runtime_error(explanation);
}
template<class F> static void invalid(F operation, const char* explanation) {
    bool refused = false; try { operation(); } catch (const std::invalid_argument&) { refused = true; }
    check(refused, explanation);
}
static SimulationIdentity identity(uint32_t session = 0x11223344) {
    SimulationIdentity result;
    result.allow_disconnected_simulation = true; result.session = session;
    result.config_hash = 0x01020304; result.source_id = 0x10203040;
    result.config_digest.fill(0x31); result.source_digest.fill(0x72);
    return result;
}
static ProviderRecord record(const SimulationIdentity& id, uint32_t sequence = 1, uint64_t tick = 0) {
    ProviderRecord result;
    result.session = id.session; result.config_hash = id.config_hash; result.source_id = id.source_id;
    result.config_digest = id.config_digest; result.source_digest = id.source_digest;
    result.sequence = sequence; result.captured_tick = tick;
    result.valid_mask = required_provider_mask; result.encoder_valid = 15;
    result.seal(); return result;
}
static void ledger_rejection(std::function<void(ProviderRecord&)> change, ProviderError error, const char* why, bool reseal = true) {
    const auto id = identity(); ProviderLedger ledger(id); auto value = record(id);
    change(value); if (reseal) value.seal();
    check(!ledger.accept(value, 0), why);
    check(ledger.error() == error, "record rejection reason differs");
    check(!ledger.has_record(), "bad record was retained as valid");
    check(!ledger.accept(record(id), 0), "valid record revived latched rejection");
    check(!ledger.healthy(0), "latched rejected record became healthy");
}
static void test_identity_and_crc() {
    const uint8_t text[] = {'1','2','3','4','5','6','7','8','9'};
    check(ProviderRecord::crc32c(text, sizeof text) == 0xe3069283u, "CRC32C check vector differs");
    auto id = identity(); auto value = record(id);
    check(value.payload().size() == 117, "canonical record length differs");
    check(value.payload()[0] == 'S' && value.payload()[3] == '2' && value.payload()[4] == 1, "canonical identity bytes differ");
    check(value.checksum() == value.crc, "canonical record CRC differs");
    invalid([] { ProviderPlant plant(SimulationIdentity{}); }, "default context accepted");
    for (unsigned i = 0; i < 6; ++i) {
        auto bad = id;
        if (i == 0) bad.allow_disconnected_simulation = false;
        if (i == 1) bad.session = 0;
        if (i == 2) bad.config_hash = 0;
        if (i == 3) bad.source_id = 0;
        if (i == 4) bad.config_digest = {};
        if (i == 5) bad.source_digest = {};
        invalid([&] { ProviderLedger ledger(bad); }, "missing explicit identity field accepted");
    }
    check(digest_from_hex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")[31] == 31, "full digest parse failed");
    invalid([] { digest_from_hex("12"); }, "short digest accepted");
    invalid([] { digest_from_hex(std::string(64, 'g')); }, "nonhex digest accepted");
    check(!ProviderLedger::physical_authority(), "provider claims physical authority");
    check(!SimInputs::physical_authority && !SimInputs::production_profile_complete, "plant promotes production qualification");
}
static void test_foreign_and_corrupt_records() {
    ledger_rejection([](auto& r) { r.crc ^= 1; }, ProviderError::crc, "corrupt CRC accepted", false);
    ledger_rejection([](auto& r) { r.tag ^= 1; }, ProviderError::identity, "foreign tag accepted");
    ledger_rejection([](auto& r) { r.abi = 2; }, ProviderError::identity, "foreign ABI accepted");
    ledger_rejection([](auto& r) { r.session ^= 1; }, ProviderError::identity, "foreign session accepted");
    ledger_rejection([](auto& r) { r.config_hash ^= 1; }, ProviderError::identity, "foreign config identifier accepted");
    ledger_rejection([](auto& r) { r.source_id ^= 1; }, ProviderError::identity, "foreign source identifier accepted");
    ledger_rejection([](auto& r) { r.config_digest[31] ^= 1; }, ProviderError::identity, "same-short-id foreign full config digest accepted");
    ledger_rejection([](auto& r) { r.source_digest[31] ^= 1; }, ProviderError::identity, "same-short-id foreign full source digest accepted");
    ledger_rejection([](auto& r) { r.sequence = 0; }, ProviderError::sequence, "zero sequence accepted");
    ledger_rejection([](auto& r) { r.sequence = 2; }, ProviderError::sequence, "initial sequence gap accepted");
    ledger_rejection([](auto& r) { r.sequence = UINT32_MAX; }, ProviderError::sequence, "initial wrapped sequence accepted");
    ledger_rejection([](auto& r) { r.captured_tick = 1; }, ProviderError::time, "future capture accepted");
    for (unsigned bit = 0; bit < 5; ++bit)
        ledger_rejection([=](auto& r) { r.valid_mask &= uint8_t(~(1u << bit)); }, ProviderError::incomplete, "missing provider accepted");
    ledger_rejection([](auto& r) { r.valid_mask |= 0x20; }, ProviderError::incomplete, "unknown provider bit accepted");
    for (unsigned i = 0; i < 4; ++i)
        ledger_rejection([=](auto& r) { r.encoder_valid &= uint8_t(~(1u << i)); }, ProviderError::incomplete, "unavailable encoder accepted");
    ledger_rejection([](auto& r) { r.di = 0x1000000; }, ProviderError::field, "25th DI accepted");
    ledger_rejection([](auto& r) { r.probe = 4; }, ProviderError::field, "third probe accepted");
    ledger_rejection([](auto& r) { r.home = 0x1000; }, ProviderError::field, "13th home accepted");
    ledger_rejection([](auto& r) { r.limit_high = 0x1000; }, ProviderError::field, "13th limit accepted");
    ledger_rejection([](auto& r) { r.encoder_a = 16; }, ProviderError::field, "fifth encoder accepted");
    ledger_rejection([](auto& r) { r.faults = 1; }, ProviderError::reported_fault, "reported provider fault accepted");
    ledger_rejection([](auto& r) { r.do_fault = 1; }, ProviderError::reported_fault, "DO application fault accepted");
}
static void test_time_sequence_and_reset() {
    const auto id = identity();
    ProviderLedger ledger(id);
    check(!ledger.healthy(0), "missing record counted healthy");
    check(ledger.accept(record(id), 0), "fresh initial record refused");
    check(ledger.healthy(stale_ticks - 1), "freshness pre-boundary refused");
    check(!ledger.healthy(stale_ticks), "expired exact-boundary provider accepted");
    check(!ledger.healthy(stale_ticks + 1), "expired provider accepted");
    check(ledger.error() == ProviderError::stale, "expiry reason differs");
    check(!ledger.accept(record(id, 2, stale_ticks + 2), stale_ticks + 2), "late record cleared stale latch");
    invalid([&] { ledger.reset_context(id); }, "same-context reset accepted");
    const auto fresh = identity(id.session + 1); ledger.reset_context(fresh);
    check(!ledger.has_record(), "reset invented provider facts");
    check(ledger.accept(record(fresh, 1, stale_ticks + 3), stale_ticks + 3), "new context fresh facts refused");
    ProviderLedger preserved_time(id); check(preserved_time.accept(record(id, 1, 50), 50), "context initial time refused");
    preserved_time.reset_context(fresh);
    check(!preserved_time.accept(record(fresh, 1, 50), 51), "new context reused old captured facts");
    ProviderLedger binding(id); auto foreign_binding = fresh; foreign_binding.config_digest[31] ^= 1;
    invalid([&] { binding.reset_context(foreign_binding); }, "reset rebound old short ID to foreign full configuration");
    foreign_binding = fresh; foreign_binding.source_digest[31] ^= 1;
    invalid([&] { binding.reset_context(foreign_binding); }, "reset rebound old short ID to foreign full source");
    for (unsigned mode = 0; mode < 4; ++mode) {
        ProviderLedger ordered(id); check(ordered.accept(record(id), 0), "ordered initial refused");
        auto next = record(id, 2, 10);
        if (mode == 0) next.sequence = 1;  // Duplicate, even byte-identical facts, is not new authority.
        if (mode == 1) next.sequence = 3;
        if (mode == 2) next.captured_tick = 0;
        if (mode == 3) next.di = 1, next.sequence = 1;  // conflicting duplicate
        next.seal(); check(!ordered.accept(next, 10), "replayed/skipped/conflicting sample accepted");
    }
    ProviderLedger old(id); check(!old.accept(record(id), stale_ticks), "exact-boundary old first record accepted");
    ProviderLedger reversed(id); check(reversed.accept(record(id), 0), "initial clock refused");
    check(reversed.healthy(10), "forward clock refused");
    check(!reversed.healthy(9), "reversed clock accepted");
    check(reversed.error() == ProviderError::time, "reverse clock reason differs");
}
struct Rig {
    ProviderPlant plant;
    RtlOutputs out{};
    uint64_t tick = 0;
    explicit Rig(PlantConfig config = {}) : plant(identity(), config) {}
    SimInputs next() { return plant.tick(tick++, out); }
    SimInputs advance(unsigned n) { SimInputs in; for (unsigned i = 0; i < n; ++i) in = next(); return in; }
    void allow_motion(uint8_t domains = 7) {
        next(); out.motion_request = true; out.opi_rearm = domains; next();
        out.opi_rearm = 0; advance(101); out.enable_n = 0; out.permit_out_req = true;
    }
    void pulse(uint16_t mask) { out.step_out = 0; next(); out.step_out = mask; next(); out.step_out = 0; next(); }
};
static void test_real_pin_mechanics_and_sensors() {
    Rig rig; const auto initial = rig.next();
    check(initial.provider_strobe && initial.provider_sequence == 1 && initial.provider_healthy, "initial sample missing");
    check(initial.gate_high == 0 && !initial.reset_arm_ready && initial.encoder_port_valid == 15, "initial permissions invented");
    const auto start = rig.plant.metrics().position;
    rig.out.step_out = all_motors; rig.next();
    check(rig.plant.metrics().position == start, "inhibited emitted edges moved plant");
    rig.out.step_out = 0; rig.next(); rig.allow_motion();
    check(rig.plant.inputs().gate_high == 7, "observed rearm did not produce delayed gates");
    rig.pulse(all_motors);
    for (unsigned i = 0; i < 12; ++i) {
        check(rig.plant.metrics().position[i] == start[i] + 1, "independent actual STEP missing");
        check(rig.plant.metrics().accepted_rises[i] == 1, "independent accepted edge missing");
        check(rig.plant.metrics().inhibited_rises[i] == 1, "inhibited edge unobserved");
    }
    check(rig.plant.inputs().encoder_b == 15 && rig.plant.inputs().encoder_a == 0, "actual mechanical ABZ differs");
    rig.out.dir_out = all_motors; rig.pulse(all_motors);
    check(rig.plant.metrics().position == start, "direction pins did not reverse mechanics");
    for (unsigned i = 0; i < 4; ++i) check(rig.plant.metrics().encoder_edges[i] == 2, "encoder did not derive emitted motion");
    rig.plant.set_inputs(0xffffff, 2); rig.next();
    check(rig.plant.inputs().di_raw == 0xffffff && rig.plant.inputs().probe_raw == 2, "24 DI/two probe inputs missing");
    invalid([&] { rig.plant.set_inputs(0x1000000); }, "25th external DI accepted");
    invalid([&] { rig.plant.set_inputs(0, 4); }, "third external probe accepted");
    rig.out.motion_request = false; rig.pulse(all_motors);
    check(rig.plant.metrics().position == start, "request-off edges moved mechanics");
    Rig no_gate; no_gate.next(); no_gate.out.motion_request = no_gate.out.permit_out_req = true;
    no_gate.out.enable_n = 0; no_gate.pulse(all_motors);
    for (auto count : no_gate.plant.metrics().accepted_rises) check(count == 0, "enable/permit bypassed independent OPI gate");
    PlantConfig sensor; sensor.initial.fill(1); sensor.maximum.fill(2); sensor.probe_surface = 0;
    Rig limits(sensor); limits.allow_motion(); limits.out.dir_out = all_motors; limits.pulse(all_motors);
    check(limits.plant.inputs().home_raw == all_motors && limits.plant.inputs().limit_low_raw == all_motors, "home/low limit geometry absent");
    check((limits.plant.inputs().probe_raw & 1) != 0, "probe surface acquisition absent");
    limits.out.dir_out = 0; limits.pulse(all_motors); limits.pulse(all_motors);
    check(limits.plant.inputs().limit_high_raw == all_motors, "high limit geometry absent");
    limits.pulse(all_motors);
    for (auto pos : limits.plant.metrics().position) check(pos == 2, "mechanical envelope overrun");
}
static void test_output_application_and_faults() {
    Rig rig; rig.next(); rig.out.dout_request = 0xffff; rig.next();
    check(rig.plant.inputs().do_applied == 0, "unrequested DO applied");
    rig.out.output_request = true; rig.next();
    check(rig.plant.inputs().do_applied == 0, "DO bypassed independent output gate");
    rig.out.opi_rearm = 8; rig.next(); rig.out.opi_rearm = 0; rig.advance(102);
    check(rig.plant.inputs().do_applied == 0xffff, "16 requested DO did not apply");
    for (unsigned bit = 0; bit < 16; ++bit) {
        rig.out.dout_request = uint16_t(1u << bit); rig.next();
        check(rig.plant.inputs().do_applied == (1u << bit), "independent DO application mismatch");
    }
    Faults inhibit; inhibit.inhibit = true; rig.plant.set_faults(inhibit); rig.next();
    check(rig.plant.inputs().do_applied == 0 && rig.plant.inputs().gate_high == 0, "inhibit did not remove output application");
    Rig fault; fault.next(); fault.out.output_request = true; fault.out.dout_request = 0xffff;
    fault.out.opi_rearm = 8; fault.next(); fault.out.opi_rearm = 0; fault.advance(102);
    Faults open; open.do_open = 0x8001; fault.plant.set_faults(open); fault.next();
    check(fault.plant.inputs().do_applied == 0x7ffe && fault.plant.inputs().do_fault == 0x8001, "open DO fault mirrored request");
    fault.advance(5000);
    check(!fault.plant.inputs().provider_healthy && fault.plant.error() == ProviderError::reported_fault, "output fault did not latch acquisition failure");
    check(fault.plant.inputs().do_applied == 0, "latched output fault permitted normal application");
    Rig shorted; shorted.next(); Faults stuck; stuck.do_short = 0x8000; shorted.plant.set_faults(stuck); shorted.next();
    check(shorted.plant.inputs().do_applied == 0x8000 && shorted.plant.inputs().do_fault == 0x8000, "stuck-high output evidence hidden");
}
static void test_freshness_faults_and_deliberate_reset() {
    const std::vector<std::function<void(Faults&)>> errors = {
        [](auto& f) { f.corrupt_crc = true; }, [](auto& f) { f.foreign_session = true; },
        [](auto& f) { f.foreign_config = true; }, [](auto& f) { f.foreign_source = true; },
        [](auto& f) { f.skipped_sequence = true; }, [](auto& f) { f.replay_sequence = true; },
        [](auto& f) { f.reverse_timestamp = true; }, [](auto& f) { f.reported_provider_fault = true; }
    };
    for (const auto& change : errors) {
        Rig rig; rig.allow_motion(); Faults fault; change(fault); rig.plant.set_faults(fault); rig.advance(5001);
        check(!rig.plant.inputs().provider_healthy && !rig.plant.inputs().inhibit_n, "malformed sample did not inhibit provider");
        rig.pulse(all_motors); for (auto count : rig.plant.metrics().accepted_rises) check(count == 0, "bad sample permitted emitted motion");
        rig.plant.set_faults({}); rig.advance(5001);
        check(!rig.plant.inputs().provider_healthy, "fresh sample silently cleared provider rejection");
    }
    Rig stale; stale.next(); Faults stop; stop.pause_heartbeat = true; stale.plant.set_faults(stop);
    stale.advance(unsigned(stale_ticks - 1)); check(stale.plant.inputs().provider_healthy, "freshness pre-boundary failed");
    stale.next(); check(!stale.plant.inputs().provider_healthy && stale.plant.error() == ProviderError::stale, "expired provider survived");
    Rig reset; reset.next(); reset.plant.set_reset_button(true); reset.advance(2500000);
    check(!reset.plant.inputs().reset_arm_ready, "reset debounce bypassed"); reset.next();
    check(reset.plant.inputs().reset_arm_ready && reset.plant.inputs().reset_arm_held, "deliberate reset press absent");
    reset.out.reset_arm_consumed = true; reset.next(); reset.out.reset_arm_consumed = false; reset.advance(2500001);
    check(!reset.plant.inputs().reset_arm_ready, "held consumed reset silently rearmed");
    reset.plant.set_reset_button(false); reset.next(); check(!reset.plant.inputs().reset_arm_ready, "release reused consumed reset");
    reset.plant.set_reset_button(true); reset.advance(2500001); reset.plant.set_reset_button(false); reset.next();
    check(reset.plant.inputs().reset_arm_ready && !reset.plant.inputs().reset_arm_held, "new deliberate reset press refused");
    reset.plant.reset_context(identity(0x11223345)); reset.next();
    check(reset.plant.inputs().provider_sequence == 1 && !reset.plant.inputs().reset_arm_ready, "new context reused old reset/facts");
    invalid([&] { reset.plant.reset_context(identity(0x11223345)); }, "same-context plant reset accepted");
    Rig clock; clock.next(); invalid([&] { clock.plant.tick(3, {}); }, "unobserved clock interval accepted");
}
static void test_timed_watchdog_and_motor_faults() {
    Rig watchdog; watchdog.next(); watchdog.out.motion_request = true; watchdog.next();
    watchdog.advance(549999); check(watchdog.plant.inputs().wd_m_ok, "motion watchdog dropped early");
    watchdog.next(); check(!watchdog.plant.inputs().wd_m_ok, "motion watchdog never dropped");
    watchdog.out.motion_request = false; watchdog.next(); watchdog.advance(99);
    check(!watchdog.plant.inputs().wd_m_ok, "motion watchdog restored early"); watchdog.next();
    check(watchdog.plant.inputs().wd_m_ok && watchdog.plant.metrics().watchdog_m_drops == 1 && watchdog.plant.metrics().watchdog_m_recoveries == 1, "motion watchdog timed recovery absent");
    watchdog.out.output_request = true; watchdog.next(); watchdog.advance(550000);
    check(!watchdog.plant.inputs().wd_o_ok && watchdog.plant.metrics().watchdog_o_drops == 1, "output watchdog drop absent");
    watchdog.out.output_request = false; watchdog.advance(101);
    check(watchdog.plant.inputs().wd_o_ok && watchdog.plant.metrics().watchdog_o_recoveries == 1, "output watchdog recovery absent");
    Rig fed; fed.next(); fed.out.motion_request = true; fed.next();
    for (unsigned block = 0; block < 3; ++block) { fed.advance(400000); fed.out.progress_m = true; fed.next(); fed.out.progress_m = false; fed.next(); }
    check(fed.plant.inputs().wd_m_ok && !fed.plant.metrics().watchdog_m_drops, "actual progress did not feed watchdog");
    Rig faults; faults.allow_motion(); Faults injected; injected.stalled_motors = 1; injected.reverse_motors = 2; injected.alarm_mask = 0x801; faults.plant.set_faults(injected);
    faults.pulse(all_motors);
    check(faults.plant.metrics().position[0] == 10000 && faults.plant.metrics().position[1] == 9999 && faults.plant.metrics().position[11] == 10001, "independent stall/reversal absent");
    check(faults.plant.inputs().alarm_current_raw == 0x801, "individual alarm signals missing");
    for (unsigned encoder = 0; encoder < 4; ++encoder) {
        Rig unplug; unplug.next(); Faults f; f.encoder_unplug = uint8_t(1u << encoder); unplug.plant.set_faults(f); unplug.next();
        check(unplug.plant.inputs().encoder_port_valid == uint8_t(15 & ~(1u << encoder)), "individual encoder loss hidden");
        unplug.advance(5000); check(!unplug.plant.inputs().provider_healthy, "unavailable encoder passed provider qualification");
    }
}
int main() {
    try {
        test_identity_and_crc(); test_foreign_and_corrupt_records(); test_time_sequence_and_reset();
        test_real_pin_mechanics_and_sensors(); test_output_application_and_faults();
        test_freshness_faults_and_deliberate_reset(); test_timed_watchdog_and_motor_faults();
        std::cout << "{\"status\":\"PASS\",\"checks\":" << checks
                  << ",\"groups\":7,\"motors\":12,\"encoders\":4,\"DI\":24,\"DO\":16,\"physical_authority\":false}" << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL after " << checks << " checks: " << error.what() << std::endl;
        return 1;
    }
}
