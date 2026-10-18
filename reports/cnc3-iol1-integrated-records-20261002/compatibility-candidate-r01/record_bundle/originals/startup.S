.syntax unified
.cpu cortex-m0plus
.thumb
.section .isr_vector,"a",%progbits
.global vectors
vectors:
.word _stack_top,Reset_Handler
.word Default_Handler,Default_Handler
.word 0,0,0,0,0,0,0,Default_Handler,0,0,Default_Handler,Default_Handler
/* Exactly32 device vectors; EXTI4_15 is IRQ7. */
.rept 7
.word Default_Handler
.endr
.word EXTI4_15_IRQHandler
.rept 24
.word Default_Handler
.endr
.section .text.Reset_Handler,"ax",%progbits
.thumb_func
.global Reset_Handler
Reset_Handler:
 ldr r0,=_sidata
 ldr r1,=_sdata
 ldr r2,=_edata
1: cmp r1,r2
 bcs 2f
 ldr r3,[r0]
 str r3,[r1]
 adds r0,#4
 adds r1,#4
 b 1b
2: ldr r1,=_sbss
 ldr r2,=_ebss
 movs r3,#0
3: cmp r1,r2
 bcs 4f
 str r3,[r1]
 adds r1,#4
 b 3b
4: bl main
 b Default_Handler
.thumb_func
.global Default_Handler
Default_Handler: b Default_Handler
