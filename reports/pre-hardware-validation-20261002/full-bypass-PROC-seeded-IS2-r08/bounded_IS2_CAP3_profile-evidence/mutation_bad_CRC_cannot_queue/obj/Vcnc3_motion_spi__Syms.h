// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VCNC3_MOTION_SPI__SYMS_H_
#define VERILATED_VCNC3_MOTION_SPI__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vcnc3_motion_spi.h"

// INCLUDE MODULE CLASSES
#include "Vcnc3_motion_spi___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vcnc3_motion_spi__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vcnc3_motion_spi* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vcnc3_motion_spi___024root     TOP;

    // CONSTRUCTORS
    Vcnc3_motion_spi__Syms(VerilatedContext* contextp, const char* namep, Vcnc3_motion_spi* modelp);
    ~Vcnc3_motion_spi__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
