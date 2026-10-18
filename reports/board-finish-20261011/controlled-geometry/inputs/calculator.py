"""Provisional controlled-impedance calculator for ROOT104 (PROVISIONAL - FAB STACKUP CONFIRMATION REQUIRED).

Units: lengths in mm, impedances in ohm. Quasi-static (no dispersion, lossless).

Method A - IPC-2141A closed forms (as published in IPC-2141A, 2004, and reproduced in TI/National
           AN-905 and Analog Devices MT-094):
    surface microstrip      Z0 = 87/sqrt(er+1.41) * ln(5.98 h / (0.8 w + t))
    edge-coupled microstrip Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 s/h))
    symmetric stripline     Z0 = 60/sqrt(er) * ln(1.9 b / (0.8 w + t)),  b = plane separation
    asymmetric stripline    Z0 = 80/sqrt(er) * ln(1.9 (2 h1 + t) / (0.8 w + t)) * (1 - h1 / (4 h2)),
                            h1 = trace-to-near-plane, h2 = trace-to-far-plane (reduces exactly to the
                            symmetric form when h1 = h2)
    edge-coupled stripline  Zdiff = 2 Z0 (1 - 0.347 exp(-2.9 s/b))

Method B - Wadell, "Transmission Line Design Handbook" (1991) formulations:
    microstrip              Hammerstad & Jensen (1980) with H&J metal-thickness correction
    coupled microstrip      Kirschning & Jansen (1984) even/odd quasi-static, Jansen thickness correction
    stripline               Cohn (1954/1955) exact zero-thickness conformal mapping (elliptic integrals),
                            single and edge-coupled; finite thickness via Wheeler's (1978) equivalent
                            zero-thickness strip (w' = w + dw in spacing b - t); asymmetric (offset)
                            stripline and mixed prepreg/core dielectric by the parallel-plate capacitance
                            combination of the two half-striplines (C = (C1 + C2)/2 with each half's own
                            er; inductance from the air capacitances).

Method C - 2D quasi-static finite-volume Laplace solver (rectangular conductors, optional conformal
           solder mask). A cross-check and the only method used for the solder-mask effect.
           NOT a substitute for the fabricator's field solver.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

ETA0 = 376.730313668          # free-space wave impedance, ohm
C0_MM_PER_PS = 0.299792458    # speed of light, mm/ps


# ---------------------------------------------------------------- helpers
def ellipk(k: float) -> float:
    """Complete elliptic integral of the first kind K(k) (modulus k) by the AGM."""
    if not 0.0 <= k < 1.0:
        raise ValueError("modulus out of range")
    a, g = 1.0, math.sqrt(1.0 - k * k)
    for _ in range(60):
        a, g = 0.5 * (a + g), math.sqrt(a * g)
        if abs(a - g) < 1e-15:
            break
    return math.pi / (2.0 * a)


def k_ratio(k: float) -> float:
    """K(k)/K(k') with k' = sqrt(1-k^2)."""
    kp = math.sqrt(1.0 - k * k)
    return ellipk(k) / ellipk(kp)


def tpd_ps_per_mm(eeff: float) -> float:
    return math.sqrt(eeff) / C0_MM_PER_PS


# ---------------------------------------------------------------- Method A: IPC-2141A
def ipc_microstrip_z0(w, h, t, er):
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def ipc_microstrip_valid(w, h, t, er):
    return 0.1 < w / h < 2.0 and 1.0 < er < 15.0


def ipc_microstrip_zdiff(w, s, h, t, er):
    return 2.0 * ipc_microstrip_z0(w, h, t, er) * (1.0 - 0.48 * math.exp(-0.96 * s / h))


def ipc_stripline_sym_z0(w, b, t, er):
    return 60.0 / math.sqrt(er) * math.log(1.9 * b / (0.8 * w + t))


def ipc_stripline_asym_z0(w, h1, h2, t, er):
    """h1 = trace surface to near plane, h2 = trace surface to far plane (h1 <= h2)."""
    if h1 > h2:
        h1, h2 = h2, h1
    return 80.0 / math.sqrt(er) * math.log(1.9 * (2.0 * h1 + t) / (0.8 * w + t)) * (1.0 - h1 / (4.0 * h2))


def ipc_stripline_valid(w, h1, h2, t):
    b = h1 + h2 + t
    return w / (b - t) < 0.35 and t / b < 0.25


def ipc_stripline_zdiff(w, s, h1, h2, t, er):
    b = h1 + h2 + t
    return 2.0 * ipc_stripline_asym_z0(w, h1, h2, t, er) * (1.0 - 0.347 * math.exp(-2.9 * s / b))


# ---------------------------------------------------------------- Method B: microstrip (H&J, K&J)
def _hj_z01(u):
    f = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
    return ETA0 / (2.0 * math.pi) * math.log(f / u + math.sqrt(1.0 + (2.0 / u) ** 2))


def _hj_ee(u, er):
    a = 1.0 + math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) / 49.0 + math.log(1.0 + (u / 18.1) ** 3) / 18.7
    b = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (-a * b)


def _hj_du(u, tn, er):
    """H&J thickness correction: returns (du1, dur) normalised to h."""
    if tn <= 0:
        return 0.0, 0.0
    coth2 = (1.0 / math.tanh(math.sqrt(6.517 * u))) ** 2
    du1 = tn / math.pi * math.log(1.0 + 4.0 * math.e / (tn * coth2))
    dur = 0.5 * (1.0 + 1.0 / math.cosh(math.sqrt(er - 1.0))) * du1
    return du1, dur


def hj_microstrip(w, h, t, er):
    """Hammerstad & Jensen microstrip. Returns (Z0, eeff)."""
    u = w / h
    du1, dur = _hj_du(u, t / h, er)
    u1, ur = u + du1, u + dur
    ee_r = _hj_ee(ur, er)
    z01_1, z01_r = _hj_z01(u1), _hj_z01(ur)
    z0 = z01_r / math.sqrt(ee_r)
    eeff = ee_r * (z01_1 / z01_r) ** 2
    return z0, eeff


def _kj_zero_thickness(u, g, er):
    """Kirschning & Jansen (1984) quasi-static coupled microstrip, zero thickness.
    Returns (Z0e, Z0o, ee_e, ee_o)."""
    # single line (zero thickness, H&J)
    ee = _hj_ee(u, er)
    z0 = _hj_z01(u) / math.sqrt(ee)
    # even-mode effective permittivity
    v = u * (20.0 + g * g) / (10.0 + g * g) + g * math.exp(-g)
    ae = 1.0 + math.log((v ** 4 + (v / 52.0) ** 2) / (v ** 4 + 0.432)) / 49.0 + math.log(1.0 + (v / 18.1) ** 3) / 18.7
    be = 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053
    ee_e = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / v) ** (-ae * be)
    # odd-mode effective permittivity
    ao = 0.7287 * (ee - (er + 1.0) / 2.0) * (1.0 - math.exp(-0.179 * u))
    bo = 0.747 * er / (0.15 + er)
    co = bo - (bo - 0.207) * math.exp(-0.414 * u)
    do = 0.593 + 0.694 * math.exp(-0.562 * u)
    ee_o = ((er + 1.0) / 2.0 + ao - ee) * math.exp(-co * g ** do) + ee
    # even-mode impedance
    q1 = 0.8695 * u ** 0.194
    q2 = 1.0 + 0.7519 * g + 0.189 * g ** 2.31
    q3 = 0.1975 + (16.6 + (8.4 / g) ** 6) ** (-0.387) + math.log(g ** 10 / (1.0 + (g / 3.4) ** 10)) / 241.0
    q4 = (2.0 * q1 / q2) / (math.exp(-g) * u ** q3 + (2.0 - math.exp(-g)) * u ** (-q3))
    z0e = z0 * math.sqrt(ee / ee_e) / (1.0 - (z0 / ETA0) * math.sqrt(ee) * q4)
    # odd-mode impedance
    q5 = 1.794 + 1.14 * math.log(1.0 + 0.638 / (g + 0.517 * g ** 2.43))
    q6 = 0.2305 + math.log(g ** 10 / (1.0 + (g / 5.8) ** 10)) / 281.3 + math.log(1.0 + 0.598 * g ** 1.154) / 5.1
    q7 = (10.0 + 190.0 * g * g) / (1.0 + 82.3 * g ** 3)
    q8 = math.exp(-6.5 - 0.95 * math.log(g) - (g / 0.15) ** 5)
    q9 = math.log(q7) * (q8 + 1.0 / 16.5)
    q10 = (q2 * q4 - q5 * math.exp(math.log(u) * q6 * u ** (-q9))) / q2
    z0o = z0 * math.sqrt(ee / ee_o) / (1.0 - (z0 / ETA0) * math.sqrt(ee) * q10)
    return z0e, z0o, ee_e, ee_o


def kj_coupled_microstrip(w, s, h, t, er):
    """Kirschning & Jansen coupled microstrip with Jansen's thickness correction
    (w_e = w + dw (1 - 0.5 exp(-0.69 dw/dt)), w_o = w_e + dt, dt = t h/(er s), dw from H&J).
    Returns dict with z0e, z0o, ee_e, ee_o, zdiff, zcm."""
    g = s / h
    if t > 0:
        du1, dur = _hj_du(w / h, t / h, er)
        dw = dur * h
        dt = t * h / (er * s)
        we = w + dw * (1.0 - 0.5 * math.exp(-0.69 * dw / dt))
        wo = we + dt
    else:
        we = wo = w
    z0e, _, ee_e, _ = _kj_zero_thickness(we / h, g, er)
    _, z0o, _, ee_o = _kj_zero_thickness(wo / h, g, er)
    return {"z0e": z0e, "z0o": z0o, "ee_e": ee_e, "ee_o": ee_o, "zdiff": 2.0 * z0o, "zcm": z0e / 2.0}


def kj_valid(w, s, h, er):
    u, g = w / h, s / h
    return 0.1 <= u <= 10.0 and 0.1 <= g <= 10.0 and 1.0 <= er <= 18.0


# ---------------------------------------------------------------- Method B: stripline (Cohn + Wheeler)
def cohn_stripline_z0_air(w, b):
    """Cohn exact zero-thickness symmetric stripline in air: 30*pi*K(k)/K(k'), k = sech(pi w / 2b)."""
    k = 1.0 / math.cosh(math.pi * w / (2.0 * b))
    return 30.0 * math.pi * k_ratio(k)


def cohn_coupled_air(w, s, b):
    """Cohn exact zero-thickness edge-coupled symmetric stripline in air. Returns (Z0e, Z0o)."""
    ta = math.tanh(math.pi * w / (2.0 * b))
    tb = math.tanh(math.pi * (w + s) / (2.0 * b))
    ke, ko = ta * tb, ta / tb
    z0e = 30.0 * math.pi / k_ratio(ke)
    z0o = 30.0 * math.pi / k_ratio(ko)
    return z0e, z0o


def wheeler_dw(w, b, t):
    """Wheeler (1978) thickness correction: equivalent zero-thickness width increase dw for spacing b - t."""
    if t <= 0:
        return 0.0
    x = t / b
    m = 2.0 / (1.0 + (2.0 / 3.0) * x / (1.0 - x))
    dw_over = x / (math.pi * (1.0 - x)) * (1.0 - 0.5 * math.log((x / (2.0 - x)) ** 2 + (0.0796 * x / (w / b + 1.1 * x)) ** m))
    return dw_over * (b - t)


def wheeler_stripline_z0(w, b, t, er):
    """Wheeler (1978) closed form for symmetric thick stripline (used only as a test reference)."""
    dw = wheeler_dw(w, b, t)
    mm = (w + dw) / (b - t)
    a = 8.0 / (math.pi * mm)
    return 30.0 / math.sqrt(er) * math.log(1.0 + 4.0 / (math.pi * mm) * (a + math.sqrt(a * a + 6.27)))


def _sym_air(w, b, t):
    """Thick symmetric stripline in air via Cohn exact + Wheeler equivalent strip."""
    dw = wheeler_dw(w, b, t)
    return cohn_stripline_z0_air(w + dw, b - t)


def _sym_air_coupled(w, s, b, t):
    dw = wheeler_dw(w, b, t)
    return cohn_coupled_air(w + dw, max(s - dw, 1e-6), b - t)


def _combine(za1, za2, er1, er2):
    """Offset stripline from two half-striplines (air impedances za1, za2 of the symmetric striplines
    with spacing 2h1+t and 2h2+t) and their dielectrics. Returns (Z0, eeff)."""
    ca = 1.0 / za1 + 1.0 / za2            # proportional to 2 c C_air
    cd = er1 / za1 + er2 / za2            # proportional to 2 c C
    z0 = 2.0 / math.sqrt(ca * cd)
    return z0, cd / ca


def cohn_stripline(w, h1, h2, t, er1, er2=None):
    """Offset stripline: h1/er1 = trace surface to plane 1, h2/er2 = trace surface to plane 2.
    Returns (Z0, eeff)."""
    er2 = er1 if er2 is None else er2
    za1 = _sym_air(w, 2.0 * h1 + t, t)
    za2 = _sym_air(w, 2.0 * h2 + t, t)
    return _combine(za1, za2, er1, er2)


def cohn_coupled_stripline(w, s, h1, h2, t, er1, er2=None):
    """Offset edge-coupled stripline. Returns dict z0e, z0o, ee, zdiff, zcm."""
    er2 = er1 if er2 is None else er2
    e1, o1 = _sym_air_coupled(w, s, 2.0 * h1 + t, t)
    e2, o2 = _sym_air_coupled(w, s, 2.0 * h2 + t, t)
    z0e, ee = _combine(e1, e2, er1, er2)
    z0o, ee_o = _combine(o1, o2, er1, er2)
    return {"z0e": z0e, "z0o": z0o, "ee": ee_o, "zdiff": 2.0 * z0o, "zcm": z0e / 2.0}


# ---------------------------------------------------------------- Method C: 2D finite-volume Laplace
@dataclass
class Rect:
    x0: float
    x1: float
    y0: float
    y1: float


def _graded(points, dmin, dmax, ratio, lo, hi):
    """1D grid through all key points, spacing dmin at key points growing by `ratio` up to dmax."""
    pts = sorted(set([lo, hi] + [p for p in points if lo <= p <= hi]))
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = b - a
        if L <= 0:
            continue
        # symmetric grading from both ends
        steps = []
        d = dmin
        while sum(steps) * 2 < L and d < dmax:
            steps.append(d)
            d *= ratio
        left = []
        acc = 0.0
        for d in steps:
            if acc + d > L / 2:
                break
            left.append(d)
            acc += d
        mid = L - 2 * acc
        nmid = max(1, int(math.ceil(mid / dmax))) if mid > 1e-12 else 0
        seg = left + ([mid / nmid] * nmid if nmid else []) + left[::-1]
        x = a
        for d in seg:
            x += d
            out.append(x)
        out[-1] = b
    return sorted(set(round(v, 9) for v in out))


def fd_solve(conductors, dielectric_rects, plane_y=(0.0,), top_plane=None, xspan=None, ytop=None,
             dmin=None, dmax=None, ratio=1.25):
    """Quasi-static FV solve.
    conductors: list of (Rect, volts) for signal conductors (zero-height rects allowed).
    dielectric_rects: list of (Rect, er) painted in order (later wins); background er = 1.
    Ground: plane at y = 0 (and at y = top_plane if given). Box walls at x = +-xspan and y = ytop are 0 V.
    Returns (charges per conductor [C/m scaled by 1/eps0], ) via energy-consistent residuals."""
    import numpy as np
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla

    keyx = [0.0]
    keyy = [0.0]
    for r, _ in conductors:
        keyx += [r.x0, r.x1]
        keyy += [r.y0, r.y1]
    for r, _ in dielectric_rects:
        keyx += [r.x0, r.x1]
        keyy += [r.y0, r.y1]
    if top_plane is not None:
        keyy.append(top_plane)
    ylo = 0.0
    yhi = top_plane if top_plane is not None else ytop
    xs = np.array(_graded(keyx, dmin, dmax, ratio, -xspan, xspan))
    ys = np.array(_graded(keyy, dmin, dmax, ratio, ylo, yhi))
    nx, ny = len(xs), len(ys)
    # cell permittivity (cells between nodes)
    cx = 0.5 * (xs[:-1] + xs[1:])
    cy = 0.5 * (ys[:-1] + ys[1:])
    eps = np.ones((nx - 1, ny - 1))
    for r, er in dielectric_rects:
        mx = (cx > r.x0) & (cx < r.x1)
        my = (cy > r.y0) & (cy < r.y1)
        eps[np.ix_(mx, my)] = er
    dx = np.diff(xs)
    dy = np.diff(ys)
    idx = lambda i, j: i * ny + j
    N = nx * ny
    fixed = np.zeros(N, dtype=bool)
    val = np.zeros(N)
    # boundaries
    for i in range(nx):
        for j in (0, ny - 1):
            fixed[idx(i, j)] = True
    for j in range(ny):
        for i in (0, nx - 1):
            fixed[idx(i, j)] = True
    cond_id = -np.ones(N, dtype=int)
    tol = 1e-9
    for k, (r, v) in enumerate(conductors):
        mi = np.where((xs >= r.x0 - tol) & (xs <= r.x1 + tol))[0]
        mj = np.where((ys >= r.y0 - tol) & (ys <= r.y1 + tol))[0]
        for i in mi:
            for j in mj:
                fixed[idx(i, j)] = True
                val[idx(i, j)] = v
                cond_id[idx(i, j)] = k
    # edge conductances
    rows, cols, data = [], [], []
    gx = np.zeros((nx - 1, ny))   # between (i,j) and (i+1,j)
    for j in range(ny):
        e_lo = eps[:, j - 1] * dy[j - 1] / 2.0 if j > 0 else 0.0
        e_hi = eps[:, j] * dy[j] / 2.0 if j < ny - 1 else 0.0
        gx[:, j] = (e_lo + e_hi) / dx
    gy = np.zeros((nx, ny - 1))
    for i in range(nx):
        e_lo = eps[i - 1, :] * dx[i - 1] / 2.0 if i > 0 else 0.0
        e_hi = eps[i, :] * dx[i] / 2.0 if i < nx - 1 else 0.0
        gy[i, :] = (e_lo + e_hi) / dy
    diag = np.zeros(N)
    I = np.arange(nx)[:, None] * ny + np.arange(ny)[None, :]
    a = I[:-1, :].ravel(); b = I[1:, :].ravel(); g = gx.ravel()
    a2 = I[:, :-1].ravel(); b2 = I[:, 1:].ravel(); g2 = gy.ravel()
    A_ = np.concatenate([a, a2]); B_ = np.concatenate([b, b2]); G_ = np.concatenate([g, g2])
    np.add.at(diag, A_, G_)
    np.add.at(diag, B_, G_)
    L = sp.coo_matrix((np.concatenate([-G_, -G_, diag]),
                       (np.concatenate([A_, B_, np.arange(N)]), np.concatenate([B_, A_, np.arange(N)]))),
                      shape=(N, N)).tocsr()
    free = ~fixed
    Lff = L[free][:, free]
    rhs = -L[free][:, fixed] @ val[fixed]
    phi = val.copy()
    phi[free] = spla.spsolve(Lff.tocsc(), rhs)
    res = L @ phi
    charges = [float(res[cond_id == k].sum()) for k in range(len(conductors))]
    return charges


def _neighbours(xs, gnd_gap, gnd_w):
    """Grounded coplanar strips of width gnd_w at clearance gnd_gap on both sides of the signal group."""
    if gnd_gap is None:
        return []
    lo, hi = min(x0 for x0, _ in xs), max(x1 for _, x1 in xs)
    return [(lo - gnd_gap - gnd_w, lo - gnd_gap), (hi + gnd_gap, hi + gnd_gap + gnd_w)]


def fd_microstrip(w, h, t, er, s=None, mask_t=0.0, mask_er=1.0, cells=None, gnd_gap=None, gnd_w=1.0):
    """FD single (s=None) or coupled microstrip over a plane at y=0. Conformal mask of thickness mask_t.
    gnd_gap: optional grounded coplanar strips (width gnd_w) at that clearance on both sides (pour model).
    Returns dict: single -> z0, eeff ; coupled -> z0e, z0o, zdiff, ee_e, ee_o."""
    span = 20.0 * h + (2 * w + (s or 0)) * 2 + (2.0 * (gnd_gap + gnd_w) if gnd_gap is not None else 0.0)
    ytop = h + t + 20.0 * h
    feat = min([v for v in (t, w, s, mask_t) if v and v > 0])
    dmin = feat / 20.0 if t > 0 else min(w, s or w) / 1000.0
    dmax = h / 8.0
    xs = [(-w / 2.0, w / 2.0)] if s is None else [(-s / 2.0 - w, -s / 2.0), (s / 2.0, s / 2.0 + w)]
    die = [(Rect(-span, span, 0.0, h), er)]
    if mask_t > 0:
        die.append((Rect(-span, span, h, h + mask_t), mask_er))
        for x0, x1 in xs:
            die.append((Rect(x0 - mask_t, x1 + mask_t, h, h + t + mask_t), mask_er))

    gnds = _neighbours(xs, gnd_gap, gnd_w)

    def solve(volts, with_die):
        conds = [(Rect(x0, x1, h, h + t), v) for (x0, x1), v in zip(xs, volts)]
        conds += [(Rect(x0, x1, h, h + t), 0.0) for x0, x1 in gnds]
        q = fd_solve(conds, die if with_die else [], xspan=span, ytop=ytop, dmin=dmin, dmax=dmax, ratio=1.2)
        return q[0]

    if s is None:
        q = solve([1.0], True)
        q0 = solve([1.0], False)
        z0 = ETA0 / math.sqrt(q * q0)   # Z0 = 1/(c sqrt(C C0)), C = eps0 q  ->  eta0 / sqrt(q q0)
        return {"z0": z0, "eeff": q / q0}
    qe, qe0 = solve([1.0, 1.0], True), solve([1.0, 1.0], False)
    qo, qo0 = solve([1.0, -1.0], True), solve([1.0, -1.0], False)
    z0e, z0o = ETA0 / math.sqrt(qe * qe0), ETA0 / math.sqrt(qo * qo0)
    return {"z0e": z0e, "z0o": z0o, "zdiff": 2.0 * z0o, "zcm": z0e / 2.0, "ee_e": qe / qe0, "ee_o": qo / qo0}


def fd_stripline(w, h1, h2, t, er1, er2=None, s=None, gnd_gap=None, gnd_w=1.0):
    """FD offset stripline: plane at y=0 and y=h1+t+h2; trace bottom at y=h2 (er2 below, er1 above).
    gnd_gap: optional grounded coplanar strips (width gnd_w) at that clearance on both sides."""
    er2 = er1 if er2 is None else er2
    b = h1 + h2 + t
    span = 10.0 * b + (2 * w + (s or 0)) * 2 + (2.0 * (gnd_gap + gnd_w) if gnd_gap is not None else 0.0)
    dmin = min([v for v in (t, w, s) if v and v > 0]) / 20.0 if t > 0 else min(w, s or w) / 1000.0
    dmax = b / 16.0
    xs = [(-w / 2.0, w / 2.0)] if s is None else [(-s / 2.0 - w, -s / 2.0), (s / 2.0, s / 2.0 + w)]
    die = [(Rect(-span, span, 0.0, h2), er2), (Rect(-span, span, h2, b), er1)]

    gnds = _neighbours(xs, gnd_gap, gnd_w)

    def solve(volts, with_die):
        conds = [(Rect(x0, x1, h2, h2 + t), v) for (x0, x1), v in zip(xs, volts)]
        conds += [(Rect(x0, x1, h2, h2 + t), 0.0) for x0, x1 in gnds]
        return fd_solve(conds, die if with_die else [], top_plane=b, xspan=span, dmin=dmin, dmax=dmax, ratio=1.2)[0]

    if s is None:
        q, q0 = solve([1.0], True), solve([1.0], False)
        return {"z0": ETA0 / math.sqrt(q * q0), "eeff": q / q0}
    qe, qe0 = solve([1.0, 1.0], True), solve([1.0, 1.0], False)
    qo, qo0 = solve([1.0, -1.0], True), solve([1.0, -1.0], False)
    z0e, z0o = ETA0 / math.sqrt(qe * qe0), ETA0 / math.sqrt(qo * qo0)
    return {"z0e": z0e, "z0o": z0o, "zdiff": 2.0 * z0o, "zcm": z0e / 2.0, "ee_e": qe / qe0, "ee_o": qo / qo0}


# ---------------------------------------------------------------- critical length
def critical_length_mm(tr_ps: float, tpd: float, fraction: float = 6.0) -> float:
    """Length above which a line is treated as a transmission line: one-way delay > tr/fraction."""
    return tr_ps / (fraction * tpd)


# ---------------------------------------------------------------- solvers
def bisect(f, lo, hi, target, tol=1e-6, increasing=None):
    """Find x in [lo, hi] with f(x) = target (f monotonic)."""
    flo, fhi = f(lo) - target, f(hi) - target
    if flo * fhi > 0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = f(mid) - target
        if abs(hi - lo) < tol:
            return mid
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass
class Layer:
    """Routing layer model. kind 'microstrip': h/er of the dielectric to the reference plane.
    kind 'stripline': h1/er1 to plane 1, h2/er2 to plane 2."""
    name: str
    kind: str
    t: float
    h: float = 0.0
    er: float = 0.0
    h1: float = 0.0
    er1: float = 0.0
    h2: float = 0.0
    er2: float = 0.0

    @property
    def er_avg(self):
        """Thickness-weighted dielectric constant (used for the single-er IPC formulas)."""
        if self.kind == "microstrip":
            return self.er
        return (self.h1 * self.er1 + self.t * self.er1 + self.h2 * self.er2) / (self.h1 + self.t + self.h2)


def se_methods(layer: Layer, w: float):
    """(method A Z0, method B Z0, method B eeff)."""
    if layer.kind == "microstrip":
        a = ipc_microstrip_z0(w, layer.h, layer.t, layer.er)
        b, ee = hj_microstrip(w, layer.h, layer.t, layer.er)
    else:
        a = ipc_stripline_asym_z0(w, layer.h1, layer.h2, layer.t, layer.er_avg)
        b, ee = cohn_stripline(w, layer.h1, layer.h2, layer.t, layer.er1, layer.er2)
    return a, b, ee


def diff_methods(layer: Layer, w: float, s: float):
    """(method A Zdiff, method B dict)."""
    if layer.kind == "microstrip":
        a = ipc_microstrip_zdiff(w, s, layer.h, layer.t, layer.er)
        b = kj_coupled_microstrip(w, s, layer.h, layer.t, layer.er)
        b["ee"] = b["ee_o"]
    else:
        a = ipc_stripline_zdiff(w, s, layer.h1, layer.h2, layer.t, layer.er_avg)
        b = cohn_coupled_stripline(w, s, layer.h1, layer.h2, layer.t, layer.er1, layer.er2)
    return a, b


def fd_se(layer: Layer, w: float, mask_t=0.0, mask_er=1.0, gnd_gap=None):
    if layer.kind == "microstrip":
        return fd_microstrip(w, layer.h, layer.t, layer.er, mask_t=mask_t, mask_er=mask_er, gnd_gap=gnd_gap)
    return fd_stripline(w, layer.h1, layer.h2, layer.t, layer.er1, layer.er2, gnd_gap=gnd_gap)


def fd_diff(layer: Layer, w: float, s: float, mask_t=0.0, mask_er=1.0, gnd_gap=None):
    if layer.kind == "microstrip":
        return fd_microstrip(w, layer.h, layer.t, layer.er, s=s, mask_t=mask_t, mask_er=mask_er, gnd_gap=gnd_gap)
    return fd_stripline(w, layer.h1, layer.h2, layer.t, layer.er1, layer.er2, s=s, gnd_gap=gnd_gap)
