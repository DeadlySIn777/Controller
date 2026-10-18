from pathlib import Path
P=Path(__file__).resolve().parent/'stage-r01'
h=(P/'iol1.h').read_text().replace('uint8_t dic_config[24],dic_config_valid;', 'uint8_t dic_config[24],dic_config_valid;\n    uint8_t hw_major,ident_pending,ident_chunk;\n    const uint8_t *factory_record;')
(P/'iol1.h').write_text(h,newline='\n')
c=(P/'iol1.c').read_text().replace('f[8]!=0x10','f[8]!=0x10 && f[8]!=0x08')
c=c.replace('int config=f[8]==0x10;', 'int config=f[8]==0x10,ident=f[8]==0x08;')
c=c.replace('}else for(unsigned i=10;i<36;i++)', '''}else if(ident){
        /* Proposed IS2 IDENT_READ supplement: payload0 chunk0..63,
         * payload1..25 zero. Telemetry8B chunks preserve realtime16B. */
        if(f[10]>=64){n->policy_errors++;return 0;}
        for(unsigned i=11;i<36;i++)if(f[i]){n->policy_errors++;return 0;}
    }else for(unsigned i=10;i<36;i++)''')
c=c.replace('n->accepted_us=now;n->good++;return 1;', 'n->ident_pending=(uint8_t)ident;\n    n->ident_chunk=ident?f[10]:0;\n    n->accepted_us=now;n->good++;return 1;')
c=c.replace('f[3]=n->slot;', 'f[3]=(uint8_t)(n->slot|(n->hw_major<<4));')
c=c.replace('put32(f+36,iol1_crc32c(f,36));', '''if(n->ident_pending){
        f[9]=(uint8_t)(0x80u|n->ident_chunk);put16(f+26,n->ident_chunk);
        for(unsigned i=0;i<8;i++)f[28+i]=n->factory_record?n->factory_record[(unsigned)n->ident_chunk*8u+i]:0xff;
    }
    put32(f+36,iol1_crc32c(f,36));''')
(P/'iol1.c').write_text(c,newline='\n')
t=(P/'target.c').read_text().replace('/* This result is diagnostic integrity', '''if(record_slot>=0){
        node.factory_record=(const uint8_t *)(record_slot?MB_RECORD_SLOT1:MB_RECORD_SLOT0);
        node.hw_major=node.factory_record[7];
    }
    /* This result is diagnostic integrity''')
(P/'target.c').write_text(t,newline='\n')
