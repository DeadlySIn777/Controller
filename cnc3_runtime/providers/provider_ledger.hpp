// Disconnected SIM provider facts. This is not a device protocol or authority.
#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace cnc3_sim {
constexpr uint32_t provider_tag = 0x53494d32u;  // SIM2
constexpr uint32_t capability_build = 0xd3494d32u;
constexpr uint8_t provider_abi = 1;
constexpr uint8_t required_provider_mask = 0x1f;
constexpr uint64_t core_hz = 50000000;
constexpr uint64_t heartbeat_ticks = 5000;     // 100 us in virtual core time.
constexpr uint64_t stale_ticks = 22000;        // Frozen 440 us bound.
using Digest = std::array<uint8_t, 32>;
inline Digest digest_from_hex(std::string_view text) {
    if (text.size() != 64) throw std::invalid_argument("SHA256 must have 64 hex digits");
    Digest digest{};
    auto nibble = [](char value) -> uint8_t {
        if (value >= '0' && value <= '9') return uint8_t(value - '0');
        if (value >= 'a' && value <= 'f') return uint8_t(value - 'a' + 10);
        if (value >= 'A' && value <= 'F') return uint8_t(value - 'A' + 10);
        throw std::invalid_argument("invalid SHA256 hex digit");
    };
    for (unsigned i = 0; i < 32; ++i) digest[i] = uint8_t((nibble(text[2 * i]) << 4) | nibble(text[2 * i + 1]));
    return digest;
}

struct SimulationIdentity {
    bool allow_disconnected_simulation = false;
    uint32_t session = 0;
    uint32_t config_hash = 0;
    uint32_t source_id = 0;
    Digest config_digest{}, source_digest{};
    void validate() const {
        if (!allow_disconnected_simulation || !session || !config_hash || !source_id)
            throw std::invalid_argument("explicit disconnected SIM identity required");
        bool have_config = false, have_source = false;
        for (auto byte : config_digest) have_config |= byte != 0;
        for (auto byte : source_digest) have_source |= byte != 0;
        if (!have_config || !have_source) throw std::invalid_argument("full SIM source/configuration digests required");
    }
};

// Explicit encoding excludes C++ padding, host endianness and unbounded text.
// CRC protects an inert provider record; it grants no physical trust.
struct ProviderRecord {
    uint32_t tag = provider_tag;
    uint8_t abi = provider_abi;
    uint32_t session = 0, config_hash = 0, source_id = 0, sequence = 0;
    Digest config_digest{}, source_digest{};
    uint64_t captured_tick = 0;
    uint8_t valid_mask = 0;
    uint32_t faults = 0, di = 0;
    uint16_t do_applied = 0, do_fault = 0, home = 0, limit_low = 0, limit_high = 0;
    uint8_t probe = 0, encoder_a = 0, encoder_b = 0, encoder_z = 0, encoder_valid = 0;
    uint32_t crc = 0;
    std::array<uint8_t, 117> payload() const {
        std::array<uint8_t, 117> bytes{};
        std::size_t at = 0;
        auto put = [&](uint64_t value, unsigned count) {
            for (unsigned i = count; i; --i) bytes[at++] = uint8_t(value >> ((i - 1) * 8));
        };
        put(tag, 4); put(abi, 1); put(session, 4); put(config_hash, 4); put(source_id, 4);
        put(sequence, 4); put(captured_tick, 8); put(valid_mask, 1); put(faults, 4);
        for (auto byte : config_digest) put(byte, 1);
        for (auto byte : source_digest) put(byte, 1);
        put(di, 4); put(do_applied, 2); put(do_fault, 2); put(home, 2);
        put(limit_low, 2); put(limit_high, 2); put(probe, 1); put(encoder_a, 1);
        put(encoder_b, 1); put(encoder_z, 1); put(encoder_valid, 1);
        return bytes;
    }
    static uint32_t crc32c(const uint8_t* data, std::size_t size) {
        uint32_t value = 0xffffffffu;
        for (std::size_t i = 0; i < size; ++i) {
            value ^= data[i];
            for (unsigned bit = 0; bit < 8; ++bit)
                value = (value >> 1) ^ ((value & 1u) ? 0x82f63b78u : 0u);
        }
        return value ^ 0xffffffffu;
    }
    uint32_t checksum() const { const auto bytes = payload(); return crc32c(bytes.data(), bytes.size()); }
    void seal() { crc = checksum(); }
};

enum class ProviderError : uint32_t {
    none = 0, crc = 1, identity = 2, sequence = 4, time = 8,
    stale = 16, incomplete = 32, field = 64, reported_fault = 128
};

class ProviderLedger {
    SimulationIdentity identity_;
    ProviderRecord accepted_{};
    ProviderError error_ = ProviderError::none;
    uint64_t watermark_ = 0, reset_floor_ = 0;
    bool have_record_ = false, have_time_ = false;
    bool have_reset_floor_ = false;
    bool fail(ProviderError error) { error_ = error; return false; }
    bool time(uint64_t now) {
        if (have_time_ && now < watermark_) return fail(ProviderError::time);
        have_time_ = true; watermark_ = now; return true;
    }
public:
    explicit ProviderLedger(SimulationIdentity identity) : identity_(identity) { identity_.validate(); }
    bool accept(const ProviderRecord& record, uint64_t now) {
        if (error_ != ProviderError::none) return false;
        if (!time(now)) return false;
        if (record.crc != record.checksum()) return fail(ProviderError::crc);
        if (record.tag != provider_tag || record.abi != provider_abi ||
            record.session != identity_.session || record.config_hash != identity_.config_hash ||
            record.source_id != identity_.source_id || record.config_digest != identity_.config_digest ||
            record.source_digest != identity_.source_digest) return fail(ProviderError::identity);
        if (!record.sequence || (have_record_ &&
            (accepted_.sequence == std::numeric_limits<uint32_t>::max() ||
             record.sequence != accepted_.sequence + 1)) || (!have_record_ && record.sequence != 1))
            return fail(ProviderError::sequence);
        if (record.captured_tick > now || (have_record_ && record.captured_tick <= accepted_.captured_tick) ||
            (have_reset_floor_ && record.captured_tick <= reset_floor_))
            return fail(ProviderError::time);
        if (now - record.captured_tick >= stale_ticks) return fail(ProviderError::stale);
        if (record.valid_mask != required_provider_mask || record.encoder_valid != 0x0f)
            return fail(ProviderError::incomplete);
        if (record.di & 0xff000000u || (record.home | record.limit_low | record.limit_high) & 0xf000u ||
            record.probe & 0xfcu || (record.encoder_a | record.encoder_b | record.encoder_z) & 0xf0u)
            return fail(ProviderError::field);
        if (record.faults || record.do_fault) return fail(ProviderError::reported_fault);
        accepted_ = record; have_record_ = true; return true;
    }
    bool healthy(uint64_t now) {
        if (error_ != ProviderError::none || !time(now) || !have_record_) return false;
        if (now - accepted_.captured_tick >= stale_ticks) return fail(ProviderError::stale);
        return true;
    }
    // A reset alone cannot revive old facts. A new explicit context must acquire
    // fresh sequence-one facts before any output application is possible.
    void reset_context(SimulationIdentity next) {
        next.validate();
        if (next.session == identity_.session) throw std::invalid_argument("new SIM session required");
        if (next.config_hash != identity_.config_hash || next.source_id != identity_.source_id ||
            next.config_digest != identity_.config_digest || next.source_digest != identity_.source_digest)
            throw std::invalid_argument("cannot rebind immutable SIM source/configuration in place");
        reset_floor_ = watermark_; have_reset_floor_ = have_time_;
        identity_ = next; accepted_ = {}; error_ = ProviderError::none;
        have_record_ = false;
    }
    ProviderError error() const { return error_; }
    const ProviderRecord& accepted() const { return accepted_; }
    const SimulationIdentity& identity() const { return identity_; }
    bool has_record() const { return have_record_; }
    static constexpr bool physical_authority() { return false; }
};
}  // namespace cnc3_sim
