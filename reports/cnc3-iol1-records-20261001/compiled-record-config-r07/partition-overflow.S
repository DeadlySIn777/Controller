.syntax unified
.cpu cortex-m0plus
.thumb
.section .text.factory_overflow_probe,"ax",%progbits
.global factory_overflow_probe
factory_overflow_probe:
.space 61440
