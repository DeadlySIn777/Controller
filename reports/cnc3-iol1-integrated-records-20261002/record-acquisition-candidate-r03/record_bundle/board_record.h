#ifndef CNC_BOARD_RECORD_H
#define CNC_BOARD_RECORD_H
#include <stdint.h>
#define MB_RECORD_BYTES 512u
#define MB_PAGE_BYTES 2048u
#define MB_RECORD_SLOT0 0x0800f000u
#define MB_RECORD_SLOT1 0x0800f800u
/* Proposed IS2 motherboard/region descriptor. No removable-card identity.
 * Target checks integrity and UID only; it CANNOT authenticate a signature. */
int mb_record_integrity(const uint8_t p[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]);
int mb_record_select(const uint8_t a[MB_RECORD_BYTES],const uint8_t b[MB_RECORD_BYTES],uint8_t class_id,uint8_t slot,const uint8_t uid[12]);
#endif
