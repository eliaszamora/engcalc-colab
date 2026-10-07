import numpy as np

CASES = {}
rng = np.random.default_rng(7)

# A. two DOFs tied by a stiff spring P, member stiffness 1, mass identity
for P in (1e10, 1e11, 1e12, 1e13, 1e14, 1e16):
    K = np.array([[1 + P, -P], [-P, 1 + P]])
    CASES[f"A_tie_{P:g}"] = {"K": K, "G": np.eye(2)}
    # same with a third free dof and a grounded spring P (support as spring)
    K3 = np.array([[1 + P, -1, 0], [-1, 2, -1], [0, -1, 1]])
    CASES[f"A_support_{P:g}"] = {"K": K3, "G": np.eye(3)}

# B. K = 2G with G nearly but genuinely full rank
for d in (1e-6, 1e-9, 1e-11, 1e-13):
    G = np.array([[1, 1], [1, 1 + d]])
    CASES[f"B_K2G_{d:g}"] = {"K": 2 * G, "G": G}
    Q = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    G2 = Q @ np.diag([1, d]) @ Q.T
    K2 = Q @ np.diag([1, 3 * d]) @ Q.T
    CASES[f"B_rot_{d:g}"] = {"K": K2, "G": G2}

# C. defective symmetric indefinite pencil, lambda = 3 double
CASES["C_defective"] = {"K": np.array([[1, 3], [3, 0]]), "G": np.array([[0, 1], [1, 0]])}
# D. zero diagonal G
CASES["D_offdiag"] = {"K": np.eye(2), "G": np.array([[0, 1], [1, 0]])}
CASES["D_offdiag3"] = {"K": np.diag([2.0, 3, 5]), "G": np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])}
CASES["D_offdiag_small"] = {"K": np.eye(2), "G": np.array([[0, 1e-8], [1e-8, 1]])}

# E/F. SPD K, negative semidefinite / indefinite G
for n in (4, 6, 9):
    A = rng.standard_normal((n, n))
    K = A @ A.T + n * np.eye(n)
    B = rng.standard_normal((n, n - 2))
    CASES[f"E_negsemidef_{n}"] = {"K": K, "G": -(B @ B.T)}
    s = np.diag([1.0] * (n - 3) + [-1.0])
    C = rng.standard_normal((n, n - 2))
    CASES[f"F_indef_{n}"] = {"K": K, "G": C @ np.diag([1.0] * (n - 4) + [-1.0, -2.0]) @ C.T}

# G. non-symmetric pencils with real eigenvalues (Weierstrass), singular B
for n, finite in ((4, 2), (5, 3), (6, 6)):
    W = rng.standard_normal((n, n))
    Z = rng.standard_normal((n, n))
    lam = np.array([1.5, -2.0, 7.0, 0.25, 11.0, 3.0][:finite])
    A = W @ np.diag(list(lam) + [1.0] * (n - finite)) @ Z
    Bm = W @ np.diag([1.0] * finite + [0.0] * (n - finite)) @ Z
    CASES[f"G_nonsym_{n}_{finite}"] = {"K": A, "G": Bm}
# clustered non-symmetric
for gap in (1e-3, 1e-6, 1e-9):
    n = 4
    W = rng.standard_normal((n, n))
    Z = rng.standard_normal((n, n))
    A = W @ np.diag([1.0, 1 + gap, 5.0, 1.0]) @ Z
    Bm = W @ np.diag([1.0, 1.0, 1.0, 0.0]) @ Z
    CASES[f"G_cluster_ns_{gap:g}"] = {"K": A, "G": Bm}
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    CASES[f"H_cluster_sym_{gap:g}"] = {"K": Q @ np.diag([1.0, 1 + gap, 1 + 2 * gap, 9]) @ Q.T, "G": np.eye(n)}
    Gs = Q @ np.diag([1.0, 1.0, 1.0, 0.0]) @ Q.T
    CASES[f"H_cluster_symsing_{gap:g}"] = {"K": Q @ np.diag([2.0, 2 + 2 * gap, 3.0, 4]) @ Q.T, "G": Gs}

# I. mechanisms
L = np.array([[1, -1, 0, 0], [-1, 2, -1, 0], [0, -1, 2, -1], [0, 0, -1, 1.0]])
CASES["I_chain_mass"] = {"K": L, "G": np.eye(4)}
CASES["I_chain_Gsing"] = {"K": L, "G": np.diag([1.0, 1, 1, 0])}
CASES["I_chain_scaled"] = {"K": 1e5 * L, "G": np.diag([2.0, 1, 1, 3])}
CASES["I_two"] = {"K": np.array([[1.0, -1], [-1, 1]]), "G": np.eye(2)}
CASES["I_two_0.1"] = {"K": np.array([[0.1, -0.1], [-0.1, 0.1]]), "G": np.eye(2)}
CASES["I_third"] = {"K": np.array([[1 / 3, -1 / 3], [-1 / 3, 1 / 3]]), "G": np.eye(2)}
# singular pencil to round-off: common null vector
K = np.array([[1 / 3, -1 / 3, 0], [-1 / 3, 1 / 3, 0], [0, 0, 1.0]])
CASES["I_singular_pencil"] = {"K": K, "G": np.array([[0.7, -0.7, 0], [-0.7, 0.7, 0], [0, 0, 2.0]])}
CASES["I_singular_pencil_b"] = {"K": np.diag([1.0, 2, 0]), "G": np.diag([1.0, 0, 0])}

# M. mixed decades G
CASES["M_G_decades"] = {"K": np.diag([1.0, 1, 1]), "G": np.diag([1e-12, 1, 1e12])}
CASES["M_G_decades_off"] = {"K": np.eye(3), "G": np.array([[2e-12, 1e-6, 0], [1e-6, 1, 1e3], [0, 1e3, 2e6]])}
