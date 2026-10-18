"""Unit tests for impedance_calc.py.

Published worked examples used:
  [P35] D. M. Pozar, Microwave Engineering, 4th ed. (Wiley, 2012), Example 3.5 (stripline design):
        b = 0.32 cm, er = 2.20, Z0 = 50 ohm  ->  W = 0.266 cm.
  [P37] Pozar, Example 3.7 (microstrip design): d = 0.127 cm, er = 2.20, Z0 = 50 ohm
        ->  W/d = 3.081, W = 0.391 cm, eps_e = 1.87.
  [W78] H. A. Wheeler, "Transmission-line properties of a strip line between parallel planes",
        IEEE Trans. MTT-26, 1978 (closed form for thick stripline, stated accuracy 0.5 %).
IPC-2141A tests are hand evaluations of the published equations (each step in the docstring).
FD (method C) is checked against the exact Cohn result and the H&J result.
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import impedance_calc as ic  # noqa: E402


def rel(a, b):
    return abs(a - b) / abs(b)


# ------------------------------------------------------------------ helpers
@pytest.mark.parametrize("k", [0.0, 0.1, 0.5, 0.9, 0.99])
def test_ellipk_matches_scipy(k):
    sp = pytest.importorskip("scipy.special")
    assert ic.ellipk(k) == pytest.approx(float(sp.ellipk(k * k)), rel=1e-12)


# ------------------------------------------------------------------ Method A: IPC-2141A (worked)
def test_ipc_microstrip_worked_example():
    """W=0.30, H=0.20, T=0.035 mm, er=4.3:
    87/sqrt(4.3+1.41) = 36.40837; 5.98*0.20/(0.8*0.30+0.035) = 4.349091; ln = 1.469967;
    Z0 = 36.40837*1.469967 = 53.519 ohm."""
    assert ic.ipc_microstrip_z0(0.30, 0.20, 0.035, 4.3) == pytest.approx(53.519, abs=0.001)


def test_ipc_microstrip_diff_worked_example():
    """Same line, S = 0.20: 1 - 0.48*exp(-0.96*0.20/0.20) = 0.816211; Zdiff = 2*53.519*0.816211 = 87.366."""
    assert ic.ipc_microstrip_zdiff(0.30, 0.20, 0.20, 0.035, 4.3) == pytest.approx(87.366, abs=0.001)


def test_ipc_symmetric_stripline_worked_example():
    """W=0.15, B=0.50, T=0.035, er=4.0: 60/2 = 30; 1.9*0.5/(0.12+0.035) = 6.129032; ln = 1.813037;
    Z0 = 54.391 ohm."""
    assert ic.ipc_stripline_sym_z0(0.15, 0.50, 0.035, 4.0) == pytest.approx(54.391, abs=0.001)


def test_ipc_asymmetric_stripline_worked_example():
    """W=0.15, H1=0.20, H2=0.30, T=0.035, er=4.0: 80/2 = 40; 1.9*(0.4+0.035)/(0.155) = 5.332258;
    ln = 1.673775; (1 - 0.2/(4*0.3)) = 0.833333; Z0 = 55.792 ohm."""
    assert ic.ipc_stripline_asym_z0(0.15, 0.20, 0.30, 0.035, 4.0) == pytest.approx(55.792, abs=0.001)


def test_ipc_asymmetric_reduces_to_symmetric():
    """With H1 = H2 = H the asymmetric form equals the symmetric form with B = 2H + T."""
    for w, h, t, er in [(0.1, 0.2, 0.035, 4.2), (0.2, 0.3, 0.018, 3.8)]:
        assert ic.ipc_stripline_asym_z0(w, h, h, t, er) == pytest.approx(
            ic.ipc_stripline_sym_z0(w, 2 * h + t, t, er), rel=1e-12)


def test_ipc_stripline_diff_worked_example():
    """Line above, S = 0.20, B = 0.535: 1 - 0.347*exp(-2.9*0.2/0.535) = 0.882644; Zdiff = 98.490."""
    assert ic.ipc_stripline_zdiff(0.15, 0.20, 0.20, 0.30, 0.035, 4.0) == pytest.approx(98.490, abs=0.001)


# ------------------------------------------------------------------ Method B: published examples
def test_hj_microstrip_pozar_example_3_7():
    """[P37] W = 0.391 cm on d = 0.127 cm, er = 2.20 -> 50 ohm, eps_e = 1.87 (zero thickness)."""
    z0, ee = ic.hj_microstrip(3.91, 1.27, 0.0, 2.20)
    assert rel(z0, 50.0) < 0.01
    assert rel(ee, 1.87) < 0.01


def test_cohn_stripline_pozar_example_3_5():
    """[P35] W = 0.266 cm, b = 0.32 cm, er = 2.20 -> 50 ohm (Cohn exact, zero thickness)."""
    z0, ee = ic.cohn_stripline(2.66, 1.60, 1.60, 0.0, 2.20)
    assert rel(z0, 50.0) < 0.005
    assert ee == pytest.approx(2.20)


@pytest.mark.parametrize("w,b,t,er", [(0.2, 0.6, 0.035, 4.0), (1.0, 2.0, 0.1, 1.0), (0.15, 0.585, 0.035, 4.5)])
def test_cohn_wheeler_thickness_matches_wheeler_1978(w, b, t, er):
    """[W78] thick symmetric stripline: Cohn exact on Wheeler's equivalent strip vs Wheeler's closed form."""
    h = (b - t) / 2.0
    assert rel(ic.cohn_stripline(w, h, h, t, er)[0], ic.wheeler_stripline_z0(w, b, t, er)) < 0.01


def test_cohn_coupled_stripline_limits():
    """Far-apart coupled strips -> even = odd = single-line impedance; close strips -> Z0e > Z0 > Z0o."""
    z_single = ic.cohn_stripline_z0_air(0.3, 1.0)
    ze, zo = ic.cohn_coupled_air(0.3, 10.0, 1.0)
    assert rel(ze, z_single) < 1e-6 and rel(zo, z_single) < 1e-6
    ze, zo = ic.cohn_coupled_air(0.3, 0.1, 1.0)
    assert ze > z_single > zo


def test_kj_coupled_microstrip_limit_is_single_line():
    """Wide spacing: K&J even/odd impedances approach the H&J single-line value (zero thickness)."""
    z0, _ = ic.hj_microstrip(0.3, 0.2, 0.0, 4.4)
    d = ic.kj_coupled_microstrip(0.3, 2.0, 0.2, 0.0, 4.4)   # g = 10 (validity limit)
    assert rel(d["z0e"], z0) < 0.01 and rel(d["z0o"], z0) < 0.01


def test_offset_stripline_combination_symmetric_case():
    """Parallel-capacitance combination of two identical halves returns the symmetric value."""
    z_sym, _ = ic.cohn_stripline(0.2, 0.25, 0.25, 0.035, 4.4)
    z_air = ic._sym_air(0.2, 0.535, 0.035)
    assert z_sym == pytest.approx(z_air / math.sqrt(4.4), rel=1e-12)


# ------------------------------------------------------------------ Method C: FD solver cross-checks
def test_fd_stripline_vs_cohn_exact():
    """FD (zero-thickness strip) vs [P35] Cohn exact: within 1 %."""
    fd = ic.fd_stripline(2.66, 1.60, 1.60, 0.0, 2.20)
    assert rel(fd["z0"], ic.cohn_stripline(2.66, 1.60, 1.60, 0.0, 2.20)[0]) < 0.01


def test_fd_microstrip_vs_pozar_example_3_7():
    fd = ic.fd_microstrip(3.91, 1.27, 0.0, 2.20)
    assert rel(fd["z0"], 50.0) < 0.01 and rel(fd["eeff"], 1.87) < 0.01


def test_fd_microstrip_thick_vs_hj():
    """70 um copper on 0.22 mm (the ROOT104 outer layer): FD vs H&J within 1.5 %."""
    fd = ic.fd_microstrip(0.33, 0.22, 0.07, 4.45)
    assert rel(fd["z0"], ic.hj_microstrip(0.33, 0.22, 0.07, 4.45)[0]) < 0.015


@pytest.mark.parametrize("w,s", [(0.2, 0.25), (0.25, 0.2), (0.15, 0.15)])
def test_fd_coupled_microstrip_vs_kj_zero_thickness(w, s):
    """Zero-thickness coupled microstrip: K&J closed form vs FD within 1 % (odd and even)."""
    kj = ic.kj_coupled_microstrip(w, s, 0.22, 0.0, 4.45)
    fd = ic.fd_microstrip(w, 0.22, 0.0, 4.45, s=s)
    assert rel(kj["z0o"], fd["z0o"]) < 0.01 and rel(kj["z0e"], fd["z0e"]) < 0.01


def test_fd_coupled_stripline_vs_cohn_zero_thickness():
    d = ic.cohn_coupled_stripline(0.3, 0.2, 0.4, 0.4, 0.0, 4.0)
    fd = ic.fd_stripline(0.3, 0.4, 0.4, 0.0, 4.0, s=0.2)
    assert rel(d["z0o"], fd["z0o"]) < 0.01 and rel(d["z0e"], fd["z0e"]) < 0.01


def test_solder_mask_lowers_microstrip_impedance():
    a = ic.fd_microstrip(0.3, 0.22, 0.07, 4.45)
    b = ic.fd_microstrip(0.3, 0.22, 0.07, 4.45, mask_t=0.01, mask_er=3.3)
    assert b["z0"] < a["z0"] and b["eeff"] > a["eeff"]


@pytest.mark.parametrize("kind", ["microstrip", "stripline"])
def test_fd_grounded_neighbour_limits(kind):
    """Coplanar grounded strips: far away -> no effect (< 0.5 %); close -> lower Z (CPW loading)."""
    if kind == "microstrip":
        base = ic.fd_microstrip(0.30, 0.22, 0.07, 4.45)["z0"]
        far = ic.fd_microstrip(0.30, 0.22, 0.07, 4.45, gnd_gap=3.0)["z0"]
        near = ic.fd_microstrip(0.30, 0.22, 0.07, 4.45, gnd_gap=0.15)["z0"]
    else:
        base = ic.fd_stripline(0.20, 0.22, 0.33, 0.035, 4.45, 4.6)["z0"]
        far = ic.fd_stripline(0.20, 0.22, 0.33, 0.035, 4.45, 4.6, gnd_gap=3.0)["z0"]
        near = ic.fd_stripline(0.20, 0.22, 0.33, 0.035, 4.45, 4.6, gnd_gap=0.15)["z0"]
    assert rel(far, base) < 0.005
    assert near < 0.97 * base


def test_fd_coupled_neighbour_odd_mode_lowered():
    base = ic.fd_stripline(0.15, 0.22, 0.33, 0.035, 4.45, 4.6, s=0.30)["zdiff"]
    near = ic.fd_stripline(0.15, 0.22, 0.33, 0.035, 4.45, 4.6, s=0.30, gnd_gap=0.15)["zdiff"]
    assert near < base


# ------------------------------------------------------------------ critical length
def test_critical_length():
    """tr = 1000 ps, tpd = 6 ps/mm, one-sixth rule -> 27.78 mm."""
    assert ic.critical_length_mm(1000.0, 6.0) == pytest.approx(27.777, abs=0.001)
    assert ic.tpd_ps_per_mm(1.0) == pytest.approx(1 / 0.299792458, rel=1e-12)
