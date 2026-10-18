// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcnc3_motion_spi.h for the primary calling header

#include "Vcnc3_motion_spi__pch.h"

void Vcnc3_motion_spi___024root___ctor_var_reset(Vcnc3_motion_spi___024root* vlSelf);

Vcnc3_motion_spi___024root::Vcnc3_motion_spi___024root(Vcnc3_motion_spi__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vcnc3_motion_spi___024root___ctor_var_reset(this);
}

void Vcnc3_motion_spi___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vcnc3_motion_spi___024root::~Vcnc3_motion_spi___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
