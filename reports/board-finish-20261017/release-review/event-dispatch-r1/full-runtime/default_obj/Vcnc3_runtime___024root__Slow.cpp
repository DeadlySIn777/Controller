// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcnc3_runtime.h for the primary calling header

#include "Vcnc3_runtime__pch.h"

void Vcnc3_runtime___024root___ctor_var_reset(Vcnc3_runtime___024root* vlSelf);

Vcnc3_runtime___024root::Vcnc3_runtime___024root(Vcnc3_runtime__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vcnc3_runtime___024root___ctor_var_reset(this);
}

void Vcnc3_runtime___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vcnc3_runtime___024root::~Vcnc3_runtime___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
