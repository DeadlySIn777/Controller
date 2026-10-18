/* SPDX-License-Identifier: LicenseRef-Proprietary */
/* Rule-table types shared by the generated cnc3_rules.h and cnc3_proto.c. */
#ifndef CNC3_PROTO_TYPES_H
#define CNC3_PROTO_TYPES_H
#include <stdint.h>

struct cnc3_range { uint32_t lo, hi; };

/* One field's machine-checkable IS-1 rules (see protocol_v3.derive_field_rules). */
struct cnc3_field_rule {
    const char *name;
    uint16_t offset;          /* relative to the layout's base */
    uint8_t size;             /* bytes */
    uint8_t count;            /* elements (arrays such as "4 x u16"), 1 for scalars */
    uint8_t elem_size;        /* 0 = bytes/ascii (only the zero rule applies) */
    uint8_t is_signed;
    uint8_t zero;             /* every byte must be zero */
    uint8_t nonzero;          /* value must be nonzero */
    uint8_t range_count;      /* 0 = unrestricted */
    struct cnc3_range ranges[4];
    uint32_t zero_bits;       /* bits that must be clear */
    uint32_t only_opcodes;    /* bit n: nonzero allowed only for opcode n; 0 = any opcode */
    uint8_t relation;         /* 0 none, 1 disjoint with, 2 subset of, 3 bits need other != 0, 4 bits need other == value */
    uint16_t rel_offset;
    uint8_t rel_size;
    uint32_t rel_bits;
    uint32_t rel_value;
};

struct cnc3_layout_rules {
    const char *name;
    uint16_t length;
    unsigned field_count;
    const struct cnc3_field_rule *fields;
};

/* One opcode's structural rules from the section 3.4 table (see protocol_v3.derive_opcode_rules). */
struct cnc3_opcode_rule {
    const char *name;
    uint8_t code;
    uint8_t chip_select;      /* 0 CS_FB, 1 CS_CMD */
    uint8_t sequence;         /* 0 any, 1 must be zero, 2 must be nonzero */
    uint8_t session_nonzero;
    uint8_t paired;           /* session 0 exactly when sequence 0 */
    uint8_t mask_zero;
    uint8_t mask_nonzero;
    uint8_t rest_zero;        /* payload bytes not owned by byte16/embedded must be zero */
    uint8_t zero_range_count;
    struct { uint16_t lo, hi; } zero_ranges[2];
    uint8_t byte16_count;     /* 0 = byte 16 not owned by the opcode */
    struct cnc3_range byte16[4];
    uint8_t embedded;         /* an IOL1 command frame is carried in [emb_lo, emb_hi] */
    uint16_t emb_lo, emb_hi;
    uint8_t emb_control_bit;
    int8_t payload_layout;    /* index into cnc3_layouts, -1 none */
    uint8_t page_layout_count;
    int8_t page_layouts[4];
};
#endif
