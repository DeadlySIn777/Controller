#ifndef CNC_MOTHERBOARD_IOL1_READONLY_H
#define CNC_MOTHERBOARD_IOL1_READONLY_H
#include <stdint.h>
#include <stddef.h>
#define IOL1_BYTES 40u
#define IOL1_CLOCKS 320u
enum { IOL1_DIC=0x11, IOL1_DO=0x21, IOL1_ACC=0x31 };
enum { IOL1_INIT=0, IOL1_SYNCED=1, IOL1_FAULT=3 };
typedef struct {
    uint8_t class_id,slot,state,field_good,card_fault;
    uint16_t epoch,sequence;
    uint32_t accepted_us,good,crc_errors,framing_errors,policy_errors;
    uint8_t realtime[16];
} iol1_node;
typedef struct { uint16_t clocks; uint8_t rx_bytes,tx_bytes,overrun,cs_high; } iol1_transport;
uint32_t iol1_crc32c(const uint8_t *p,size_t n);
void iol1_init(iol1_node *n,uint8_t class_id,uint8_t slot);
/* Return 1 only after the complete physical frame AND policy are accepted.
 * Only this result may refresh the target watchdog. Never grants authority. */
int iol1_accept(iol1_node *n,const uint8_t frame[IOL1_BYTES],iol1_transport t,uint32_t now_us);
void iol1_timeout(iol1_node *n,uint32_t now_us);
/* FFFF is unavailable; stale observations saturate, never wrap to fresh. */
uint16_t iol1_observation_age(uint32_t now_us,uint32_t sampled_us,uint8_t valid);
void iol1_reply(const iol1_node *n,uint8_t frame[IOL1_BYTES]);
#endif
