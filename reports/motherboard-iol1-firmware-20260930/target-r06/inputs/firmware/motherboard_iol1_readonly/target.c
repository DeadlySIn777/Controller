/* Disconnected prototype target. No commercial commissioning or motion/output
 * authority. See README and the compiled/physical qualification receipt. */
#include "stm32g031xx.h"
#include "iol1.h"
#ifndef NODE_SLOT
#error NODE_SLOT must be 0 DIC, 1 DOA, 2 DOB or 3 ACC
#endif
#if NODE_SLOT < 0 || NODE_SLOT > 3
#error invalid fitted target
#endif
uint32_t SystemCoreClock=64000000u;
static iol1_node node;
static uint8_t rx[IOL1_BYTES],tx[IOL1_BYTES];
static uint16_t edge_base;
static volatile uint8_t busy;
#if NODE_SLOT == 1 || NODE_SLOT == 2
static uint32_t do_sample_us;
static uint8_t do_data[16],do_valid,do_fault_history[7],spi2_failed;
#elif NODE_SLOT == 0
static uint32_t raw_di,filtered_di,last_di_us;
static uint8_t debounce[24];
#endif
static uint8_t slot_valid;
static uint32_t now_us(void){return TIM2->CNT;}
static unsigned input(GPIO_TypeDef *p,unsigned b){return (p->IDR>>b)&1u;}
static void mode(GPIO_TypeDef *p,unsigned b,unsigned m){p->MODER=(p->MODER&~(3u<<(2u*b)))|(m<<(2u*b));}
static void af(GPIO_TypeDef *p,unsigned b,unsigned a){mode(p,b,2);p->AFR[b/8]=(p->AFR[b/8]&~(15u<<((b%8)*4)))|(a<<((b%8)*4));}
#if NODE_SLOT != 0
static void output(GPIO_TypeDef *p,unsigned b,unsigned v){p->BSRR=1u<<(b+(v?0u:16u));mode(p,b,1);}
#endif
static void safe_outputs(void){
#if NODE_SLOT != 0
    /* Set LOW in BSRR before enabling output mode; never write a HIGH later. */
    output(GPIOA,0,0);output(GPIOA,1,0);
#endif
#if NODE_SLOT == 1 || NODE_SLOT == 2
    /* Real driver CS initialized once, not rewritten during a transaction. */
#elif NODE_SLOT == 3
    output(GPIOA,8,0);output(GPIOA,9,0);
    /* Peripheral chip-selects initialized once, separate from authority. */
#endif
}
static unsigned fitted_slot(void){
#if NODE_SLOT == 0
 return (GPIOB->IDR>>6)&15u;
#elif NODE_SLOT == 3
 return input(GPIOC,14)|(input(GPIOC,15)<<1)|(input(GPIOF,0)<<2)|(input(GPIOF,1)<<3);
#else
 return input(GPIOA,9)|(input(GPIOA,10)<<1)|(input(GPIOA,11)<<2)|(input(GPIOA,12)<<3);
#endif
}
static void clocks(void){
    /* HSI16 / M2 * N16 / R2 =64MHz; range1 reset voltage scale.
     * FLASH LATENCY=2 wait states, not the vendor bitmask LATENCY_2. */
    FLASH->ACR=(FLASH->ACR&~FLASH_ACR_LATENCY)|2u|FLASH_ACR_ICEN;
    RCC->CR|=RCC_CR_HSION;while(!(RCC->CR&RCC_CR_HSIRDY)){}
    RCC->PLLCFGR=RCC_PLLCFGR_PLLSRC_HSI|(1u<<RCC_PLLCFGR_PLLM_Pos)|
       (16u<<RCC_PLLCFGR_PLLN_Pos)|RCC_PLLCFGR_PLLREN|(1u<<RCC_PLLCFGR_PLLR_Pos);
    RCC->CR|=RCC_CR_PLLON;while(!(RCC->CR&RCC_CR_PLLRDY)){}
    RCC->CFGR=(RCC->CFGR&~RCC_CFGR_SW)|RCC_CFGR_SW_PLLRCLK;
    while((RCC->CFGR&RCC_CFGR_SWS)!=(2u<<RCC_CFGR_SWS_Pos)){}
    RCC->IOPENR|=RCC_IOPENR_GPIOAEN|RCC_IOPENR_GPIOBEN|RCC_IOPENR_GPIOCEN|RCC_IOPENR_GPIODEN|RCC_IOPENR_GPIOFEN;
    RCC->AHBENR|=RCC_AHBENR_DMA1EN;
    RCC->APBENR1|=RCC_APBENR1_TIM2EN|RCC_APBENR1_TIM3EN|RCC_APBENR1_SPI2EN;
    RCC->APBENR2|=RCC_APBENR2_SPI1EN;
    /* Do not remap PA11/PA12 onto other pads; preserve SWD PA13/PA14. */
    for(unsigned b=0;b<16;b++){if(b!=13&&b!=14)mode(GPIOA,b,0);mode(GPIOB,b,0);mode(GPIOC,b,0);mode(GPIOD,b,0);}
    mode(GPIOF,0,0);mode(GPIOF,1,0); /* preserve PF2/NRST */
    safe_outputs();
#if NODE_SLOT == 1 || NODE_SLOT == 2
    output(GPIOB,9,1);
#elif NODE_SLOT == 3
    output(GPIOB,12,1);output(GPIOB,3,1);output(GPIOB,4,1);
#endif
    TIM2->PSC=63;TIM2->ARR=0xffffffffu;TIM2->EGR=TIM_EGR_UG;TIM2->CR1=TIM_CR1_CEN;
    /* Proposed real PB5 tap, AF1 TIM3_CH2; no input filtering/prescaler.
     * Continuous counter avoids a late CS-fall interrupt missing early clocks.
     * Parent must adopt/route the four exact taps before hardware use. */
    af(GPIOB,5,1);TIM3->PSC=0;TIM3->ARR=0xffffu;
    TIM3->CCMR1=TIM_CCMR1_CC2S_0;TIM3->CCER=TIM_CCER_CC2E;
    TIM3->SMCR=(7u<<TIM_SMCR_SMS_Pos)|(6u<<TIM_SMCR_TS_Pos);
    TIM3->EGR=TIM_EGR_UG;TIM3->CR1=TIM_CR1_CEN;
}
static void watchdog_start(void){
    /* Never provisions option bytes. Hardware-start/NRST/BOR must be verified
     * independently by the factory fixture before release. */
    RCC->CSR|=RCC_CSR_LSION;while(!(RCC->CSR&RCC_CSR_LSIRDY)){}
    DBGMCU->APBFZ1&=~DBG_APB_FZ1_DBG_IWDG_STOP;
    IWDG->KR=0xcccc;IWDG->KR=0x5555;IWDG->PR=0;IWDG->RLR=9;
    while(IWDG->SR){} IWDG->KR=0xaaaa;
}
static void observe(void){
#if NODE_SLOT != 3
    uint32_t t=now_us();
#endif
    uint8_t *p=node.realtime;
#if NODE_SLOT == 0
    static const uint8_t port[24]={2,2,2,5,5,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,2,2,0,0};
    static const uint8_t bit[24]={13,14,15,0,1,0,1,2,3,0,1,2,10,11,12,13,14,15,8,9,6,7,10,11};
    GPIO_TypeDef *const gp[6]={GPIOA,GPIOB,GPIOC,GPIOD,0,GPIOF};
    if((uint32_t)(t-last_di_us)>=10){
        raw_di=0;for(unsigned i=0;i<24;i++){unsigned v=input(gp[port[i]],bit[i]);raw_di|=v<<i;
          if(v==((filtered_di>>i)&1u))debounce[i]=0;
          else if(++debounce[i]>=5){filtered_di^=1u<<i;debounce[i]=0;}}
        last_di_us=t;
    }
    for(unsigned i=0;i<3;i++){p[i]=(uint8_t)(filtered_di>>(i*8));p[3+i]=(uint8_t)(raw_di>>(i*8));}
    uint16_t age=(uint16_t)(t-last_di_us);p[6]=(uint8_t)(age>>8);p[7]=(uint8_t)age;
    p[8]=(uint8_t)(input(GPIOA,12)|(input(GPIOA,15)<<1)|(input(GPIOD,0)<<2));
    p[9]=(uint8_t)(input(GPIOD,1)|(input(GPIOD,2)<<1));
    for(unsigned i=10;i<16;i++)p[i]=0;
    node.field_good=(p[8]|p[9])==0;
#elif NODE_SLOT == 1 || NODE_SLOT == 2
    for(unsigned i=0;i<16;i++)p[i]=do_data[i];
    uint32_t elapsed=t-do_sample_us;uint16_t age=!do_valid||elapsed>65534u?0xffffu:(uint16_t)elapsed;
    p[8]=(uint8_t)(age>>8);p[9]=(uint8_t)age;
    /* Hardware permit/latch/enabled must all remain LOW in this image. */
    if(input(GPIOA,2)||input(GPIOA,3)||input(GPIOC,6)){node.card_fault=1;node.field_good=0;}
    else node.field_good=do_valid&&input(GPIOB,1);
#else
    /* All actual analog converters are held RESET while OUT_PERMIT is LOW.
     * A healthy powered/clamped reset state is observable; ADC/DAC readback
     * validity is unavailable, age=FFFF. Never manufacture AOstatus0F. */
    for(unsigned i=0;i<16;i++)p[i]=0;
    p[12]=0xff;p[13]=0xff; /* actual ADC sample age unavailable */
    p[14]=0; /* AI valid mask zero */
    p[15]=(uint8_t)(input(GPIOC,6)|(input(GPIOC,7)<<1));
    unsigned unsafe=input(GPIOA,2)|input(GPIOA,3)|input(GPIOB,0)|input(GPIOB,1)|input(GPIOB,2)|input(GPIOB,10);
    unsigned powers=input(GPIOA,10)&input(GPIOA,11)&input(GPIOA,12)&input(GPIOD,0)&input(GPIOD,1);
    node.field_good=!unsafe&&powers&&!input(GPIOD,2)&&p[15]==3;
    if(unsafe)node.card_fault=1;
#endif
}
static void spi1_arm(void){
    /* Must run only with NSS HIGH. Any premature next CS fails unavailable. */
    if(!input(GPIOA,4)){node.card_fault=1;return;}
    SPI1->CR1=0;DMA1_Channel1->CCR=0;DMA1_Channel2->CCR=0;
    while(SPI1->SR&SPI_SR_RXNE){volatile uint8_t z=*(volatile uint8_t *)&SPI1->DR;(void)z;}
    (void)SPI1->SR;DMA1->IFCR=0x0fffu;
    observe();iol1_reply(&node,tx);
    DMA1_Channel1->CPAR=(uint32_t)&SPI1->DR;DMA1_Channel1->CMAR=(uint32_t)rx;DMA1_Channel1->CNDTR=40;
    DMA1_Channel2->CPAR=(uint32_t)&SPI1->DR;DMA1_Channel2->CMAR=(uint32_t)tx;DMA1_Channel2->CNDTR=40;
    DMAMUX1_Channel0->CCR=16;DMAMUX1_Channel1->CCR=17;
    DMA1_Channel1->CCR=DMA_CCR_MINC|DMA_CCR_PL|DMA_CCR_EN;
    DMA1_Channel2->CCR=DMA_CCR_MINC|DMA_CCR_DIR|DMA_CCR_PL|DMA_CCR_EN;
    /* 8-bit, mode0, hardware NSS. No SSM; MISO selected only under NSS LOW. */
    SPI1->CR2=(7u<<SPI_CR2_DS_Pos)|SPI_CR2_FRXTH|SPI_CR2_RXDMAEN|SPI_CR2_TXDMAEN;
    edge_base=(uint16_t)TIM3->CNT;
    SPI1->CR1=SPI_CR1_SPE;busy=0;
}
void EXTI4_15_IRQHandler(void){
    if(!(EXTI->RPR1&EXTI_RPR1_RPIF4))return;
    EXTI->RPR1=EXTI_RPR1_RPIF4;
    uint16_t count=(uint16_t)TIM3->CNT;uint32_t status=SPI1->SR;
    uint8_t r=(uint8_t)(40u-DMA1_Channel1->CNDTR),w=(uint8_t)(40u-DMA1_Channel2->CNDTR);
    DMA1_Channel1->CCR=0;DMA1_Channel2->CCR=0;SPI1->CR1=0;busy=1;
    iol1_transport transport={(uint16_t)(count-edge_base),r,w,
      (uint8_t)((status&(SPI_SR_OVR|SPI_SR_MODF))!=0||((DMA1->ISR&(DMA_ISR_TEIF1|DMA_ISR_TEIF2))!=0)),(uint8_t)input(GPIOA,4)};
    if(slot_valid&&iol1_accept(&node,rx,transport,now_us()))IWDG->KR=0xaaaa;
    safe_outputs();spi1_arm();
}
#if NODE_SLOT == 1 || NODE_SLOT == 2
static uint8_t spi2_byte(uint8_t x){
    uint32_t until=now_us()+100;while(!(SPI2->SR&SPI_SR_TXE))if((int32_t)(now_us()-until)>=0){spi2_failed=1;return 0;}
    *(volatile uint8_t *)&SPI2->DR=x;
    while(!(SPI2->SR&SPI_SR_RXNE))if((int32_t)(now_us()-until)>=0){spi2_failed=1;return 0;}
    return *(volatile uint8_t *)&SPI2->DR;
}
static int driver_read(unsigned address,uint8_t reg,uint8_t *value,uint8_t *fault){
    /* DSPI LOW, reset CRC_CONFIG0:24-clock addressed mode1 read. SPI byte0
     * writes the SW nibble even during a read: it ALWAYS remains zero here. */
    spi2_failed=0;GPIOB->BSRR=1u<<(9+16);uint8_t a=spi2_byte((uint8_t)(address<<5));
    uint8_t f=spi2_byte(reg&0x7fu),v=spi2_byte(0);
    uint32_t until=now_us()+100;while(SPI2->SR&SPI_SR_BSY)if((int32_t)(now_us()-until)>=0){spi2_failed=1;break;}
    GPIOB->BSRR=1u<<9;
    *value=v;*fault=f;
    return !spi2_failed&&!(a&0x10u)&&((a>>1)&7u)==address;
}
static void driver_poll(void){
    /* Save read-to-clear fault evidence in this actual batch before any later
     * accesses. All observations become valid only if BOTH addressed ICs
     * echo their address and all required reads complete. */
    uint8_t batch[16]={0},ok=1;
    for(unsigned a=0;a<2;a++){
        uint8_t sw=0,ft=0,v=0,f=0;
        ok&=(uint8_t)driver_read(a,0x2f,&v,&f);ok&=v==0; /* correct 24-clock state */
        ok&=(uint8_t)driver_read(a,0x1d,&sw,&ft);batch[0]|=(uint8_t)((sw&15u)<<(a*4));
        ok&=(uint8_t)driver_read(a,0x01,&v,&f);batch[1]|=(uint8_t)((v&15u)<<(a*4));
        static const uint8_t regs[5]={6,7,5,4,3};
        for(unsigned k=0;k<5;k++){ok&=(uint8_t)driver_read(a,regs[k],&v,&f);batch[2+k]|=(uint8_t)((v&15u)<<(a*4));}
        ok&=(uint8_t)driver_read(a,0x02,&v,&f);
        if((v&7u)||(ft&0x80u))batch[7]|=(uint8_t)(4u<<a); /* actualVS/VDDUV */
        if(v&0x18u)batch[7]|=(uint8_t)(16u<<a); /* SPI/driverWD */
        if(v&0x3fu)ok=0; /* fresh global supply/interface/thermal fault */
    }
    if(!input(GPIOB,0))batch[7]|=3u;
    /* SW_STATE reports command state, never terminal voltage. Hardware enable
     * LOW means applied authority zero; unexpected command bits invalidate. */
    if(batch[0])ok=0;batch[0]=0;
    /* Preserve every acknowledged read-to-clear observation until reset;
     * readonly firmware has no clear-fault authority. Telemetry is a history
     * latch, never a claim that every former fault is still physically active. */
    for(unsigned i=1;i<8;i++){do_fault_history[i-1]|=batch[i];batch[i]=do_fault_history[i-1];}
    __disable_irq();for(unsigned i=0;i<16;i++)do_data[i]=batch[i];do_valid=ok;do_sample_us=now_us();__enable_irq();
}
#endif
int main(void){
    clocks();iol1_init(&node,NODE_SLOT==0?IOL1_DIC:NODE_SLOT==3?IOL1_ACC:IOL1_DO,NODE_SLOT);
    slot_valid=fitted_slot()==NODE_SLOT;
    if(!slot_valid){node.card_fault=1;node.state=IOL1_FAULT;}
    watchdog_start();
    for(unsigned b=4;b<=7;b++)af(GPIOA,b,0);
    /* EXTI for hardware NSS rising only, PA4 default EXTI mapping. */
    EXTI->EXTICR[1]&=~0xffu;EXTI->RTSR1|=1u<<4;EXTI->IMR1|=1u<<4;
    NVIC_SetPriority(EXTI4_15_IRQn,0);NVIC_EnableIRQ(EXTI4_15_IRQn);
#if NODE_SLOT == 1 || NODE_SLOT == 2
    af(GPIOB,8,1);af(GPIOB,7,1);af(GPIOB,6,4);
    SPI2->CR2=(7u<<SPI_CR2_DS_Pos)|SPI_CR2_FRXTH;
    SPI2->CR1=SPI_CR1_MSTR|SPI_CR1_SSM|SPI_CR1_SSI|SPI_CR1_CPHA|(3u<<SPI_CR1_BR_Pos)|SPI_CR1_SPE;
#endif
    spi1_arm();
    for(;;){
      /* Protect the accepted timestamp/state tuple from IRQ preemption: a
       * pre-IRQ now combined with post-IRQ acceptance must not underflow. */
      __disable_irq();iol1_timeout(&node,now_us());__enable_irq();safe_outputs();
#if NODE_SLOT == 1 || NODE_SLOT == 2
      if(!busy)driver_poll();
#endif
      /* GPIO acquisition happens when the next reply is prepared in IRQ;
       * timeout checking does not refresh IWDG. No production enable code. */
    }
}
