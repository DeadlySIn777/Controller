// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VCNC3_RUNTIME__SYMS_H_
#define VERILATED_VCNC3_RUNTIME__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vcnc3_runtime.h"

// INCLUDE MODULE CLASSES
#include "Vcnc3_runtime___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vcnc3_runtime__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vcnc3_runtime* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vcnc3_runtime___024root        TOP;

    // CONSTRUCTORS
    Vcnc3_runtime__Syms(VerilatedContext* contextp, const char* namep, Vcnc3_runtime* modelp);
    ~Vcnc3_runtime__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
