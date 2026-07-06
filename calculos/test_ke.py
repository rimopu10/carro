# -*- coding: utf-8 -*-
"""Verifica la matriz de rigidez del hexaedro por integración de Gauss (SPD, 6 modos rígidos)."""
import numpy as np

LOCAL = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]], dtype=float)

def hex_stiffness(E, nu):
    a = E / ((1 + nu) * (1 - 2 * nu))
    D = a * np.array([
        [1-nu, nu, nu, 0, 0, 0], [nu, 1-nu, nu, 0, 0, 0], [nu, nu, 1-nu, 0, 0, 0],
        [0, 0, 0, (1-2*nu)/2, 0, 0], [0, 0, 0, 0, (1-2*nu)/2, 0], [0, 0, 0, 0, 0, (1-2*nu)/2]])
    gp = np.array([-1, 1]) / np.sqrt(3.0)
    signs = 2 * LOCAL - 1
    KE = np.zeros((24, 24))
    for xi in gp:
        for eta in gp:
            for zeta in gp:
                dN = np.zeros((3, 8))
                for i in range(8):
                    sx, sy, sz = signs[i]
                    dN[0, i] = 0.125 * sx * (1 + sy*eta) * (1 + sz*zeta)
                    dN[1, i] = 0.125 * sy * (1 + sx*xi) * (1 + sz*zeta)
                    dN[2, i] = 0.125 * sz * (1 + sx*xi) * (1 + sy*eta)
                J = dN @ LOCAL
                detJ = np.linalg.det(J)
                dNxyz = np.linalg.solve(J, dN)
                B = np.zeros((6, 24))
                for i in range(8):
                    bx, by, bz = dNxyz[:, i]; c = 3*i
                    B[0,c]=bx; B[1,c+1]=by; B[2,c+2]=bz
                    B[3,c]=by; B[3,c+1]=bx; B[4,c+1]=bz; B[4,c+2]=by; B[5,c]=bz; B[5,c+2]=bx
                KE += (B.T @ D @ B) * detJ
    return KE

KE = hex_stiffness(1.0, 0.3)
w = np.linalg.eigvalsh(KE)
print("simetrica:", np.allclose(KE, KE.T))
print("negativos:", int((w<-1e-9).sum()), " ceros(rigidos):", int((abs(w)<1e-9).sum()),
      " positivos:", int((w>1e-9).sum()))
print("max |suma fila|:", round(abs(KE.sum(1)).max(), 10))
print("traza:", round(np.trace(KE), 4))
