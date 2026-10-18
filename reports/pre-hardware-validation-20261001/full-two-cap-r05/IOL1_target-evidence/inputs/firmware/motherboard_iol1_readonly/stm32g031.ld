ENTRY(Reset_Handler)
MEMORY { FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 64K
         RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 8K }
_stack_top = ORIGIN(RAM)+LENGTH(RAM);
SECTIONS {
 .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
 .text : { *(.text*) *(.rodata*) . = ALIGN(4); } > FLASH
 .ARM.exidx : { *(.ARM.exidx*) } > FLASH
 _sidata = LOADADDR(.data);
 .data : { . = ALIGN(4);_sdata = .;*(.data*) . = ALIGN(4);_edata = .; } > RAM AT>FLASH
 .bss(NOLOAD) : { . = ALIGN(4);_sbss = .;*(.bss*) *(COMMON) . = ALIGN(4);_ebss = .; } > RAM
 ASSERT(_ebss <= _stack_top-1024,"at least1KiB stack reserve required")
}
