#ifndef CNC3_SIM2_MANIFEST_H
#define CNC3_SIM2_MANIFEST_H
#include "cnc3.h"
#ifdef __cplusplus
extern "C" {
#endif
struct cnc3_sim_manifest {
    struct cnc3_config config;
    double max_velocity[12];
    uint32_t provider_session,source_id;
    uint8_t config_digest[32],source_digest[32];
    uint32_t encoder_steps_per_revolution[4];
};
/* Startup only. Caller verifies full canonical manifest/binding/source hashes
 * through the shared preparation contract before invoking this no-device HAL.
 * This reader separately validates every numeric cyclic-runtime input. */
int cnc3_sim_manifest_read(const char *,struct cnc3_sim_manifest *);
#ifdef __cplusplus
}
#endif
#endif
