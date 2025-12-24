# evaporateurs.py
import numpy as np

# ============================================================
# FONCTION EXISTANTE (NE PAS MODIFIER)
# ============================================================
def simulation_evaporation_multi_effets(
    F_kg_h: float,
    xF: float,
    xout: float,
    n_effets: int,
    T_steam_C: float = 120.0,
    T_last_C: float = 60.0,
    U: float = 1500.0,
    lambda_kJ_kg: float = 2257.0
):
    """
    Modèle pédagogique (scalaire + valeurs par effet) pour évaporation multiple.
    """
    F_kg_h = float(F_kg_h)
    xF = float(xF)
    xout = float(xout)
    n = int(n_effets)
    T_steam_C = float(T_steam_C)
    T_last_C = float(T_last_C)
    U = float(U)
    lambda_kJ_kg = float(lambda_kJ_kg)

    if n < 1:
        raise ValueError("n_effets doit être >= 1")
    if xF <= 0 or xout <= 0 or xout <= xF:
        raise ValueError("Vérifier xF et xout")
    if T_steam_C <= T_last_C:
        raise ValueError("T_steam_C doit être > T_last_C")

    P = F_kg_h * xF / xout
    V_total = max(F_kg_h - P, 0.0)
    V_i = V_total / n

    economie = min(float(n), 6.0)
    S = V_total / max(economie, 1e-12)

    dT_total = T_steam_C - T_last_C
    dT_i = dT_total / n

    T_hot = [T_steam_C - (i - 1) * dT_i for i in range(1, n + 1)]
    T_cold = [th - dT_i for th in T_hot]

    Q_i_W = (V_i * lambda_kJ_kg) / 3.6
    A_i = Q_i_W / (U * max(dT_i, 1e-9))
    A_total = A_i * n

    details = []
    for i in range(1, n + 1):
        details.append({
            "effect": i,
            "V_kg_h": V_i,
            "A_m2": A_i,
            "T_hot_C": T_hot[i - 1],
            "T_cold_C": T_cold[i - 1],
        })

    return {
        "S": S,
        "economie": economie,
        "A_total": A_total,
        "V_total": V_total,
        "P": P,
        "details": details,
    }


# ============================================================
# CLASSE AJOUTÉE (ADAPTATEUR) — NOUVEAU
# ============================================================
class EvaporateurMultiple:
    """
    Classe adaptatrice pour compatibilité avec main.py,
    streamlit_app.py, optimisation.py, etc.
    """

    def __init__(self, F, xF, xout, Tfeed, Psteam, n_effets):
        self.F = float(F)
        self.xF = float(xF)
        self.xout = float(xout)
        self.Tfeed = float(Tfeed)
        self.Psteam = float(Psteam)
        self.n_effets = int(n_effets)

    def simuler(self):
        return simulation_evaporation_multi_effets(
            F_kg_h=self.F,
            xF=self.xF,
            xout=self.xout,
            n_effets=self.n_effets,
            T_steam_C=120.0,
            T_last_C=60.0
        )

    def consommation_vapeur(self):
        return self.simuler()["S"]

    def economie_vapeur(self):
        return self.simuler()["economie"]
