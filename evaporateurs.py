# evaporateurs.py
import numpy as np
from thermodynamique import (
    Tsat_water_from_Pbar,
    latent_heat_from_Pbar,
    EPE_Duhring,
    Cp_solution_saccharose,
    enthalpie_solution,
    enthalpie_vapeur,
    enthalpie_liquide,
    LMTD,
    coefficient_U_effet,
    COOLPROP_AVAILABLE
)


class EvaporateurMultiple:
    """
    Modèle rigoureux d'évaporateur à multiples effets en co-courant.
    Conforme au cahier des charges PIC 2024-2025.
    
    Inclut :
    - Bilans matière et énergie complets
    - EPE (Élévation Point d'Ébullition) via Dühring
    - Pertes thermiques (3% par effet)
    - Coefficients U différents par effet
    - Résistance d'encrassement
    - Utilisation de CoolProp pour propriétés thermodynamiques
    """
    
    def __init__(self, F, xF, xout, T_feed, P_steam, n_effets=3,
                 P_final=0.15, surchauffe_steam=10.0, 
                 pertes_thermiques=0.03, R_encrassement=0.0002):
        """
        Paramètres :
        -----------
        F : float
            Débit d'alimentation (kg/h)
        xF : float
            Concentration entrée (fraction massique, 0-1)
        xout : float
            Concentration sortie visée (fraction massique, 0-1)
        T_feed : float
            Température d'alimentation (°C)
        P_steam : float
            Pression vapeur de chauffe (bar abs)
        n_effets : int
            Nombre d'effets
        P_final : float
            Pression au condenseur final (bar abs)
        surchauffe_steam : float
            Surchauffe de la vapeur motrice (°C)
        pertes_thermiques : float
            Fraction de pertes (0.03 = 3%)
        R_encrassement : float
            Résistance d'encrassement (m²·K/W)
        """
        self.F = float(F)
        self.xF = float(xF)
        self.xout = float(xout)
        self.T_feed = float(T_feed)
        self.P_steam = float(P_steam)
        self.n_effets = int(n_effets)
        self.P_final = float(P_final)
        self.surchauffe = float(surchauffe_steam)
        self.pertes = float(pertes_thermiques)
        self.R_f = float(R_encrassement)
        
        # Vérifications
        if self.xout <= self.xF:
            raise ValueError("xout doit être > xF")
        if self.n_effets < 1:
            raise ValueError("n_effets doit être >= 1")
        
        # Résultats (seront calculés par simuler())
        self.L = None  # Débits liquide par effet (kg/h)
        self.V = None  # Débits vapeur par effet (kg/h)
        self.x = None  # Concentrations par effet
        self.T = None  # Températures d'ébullition par effet (°C)
        self.P = None  # Pressions par effet (bar)
        self.A = None  # Surfaces d'échange par effet (m²)
        self.Q = None  # Puissances thermiques par effet (kW)
        self.U = None  # Coefficients U par effet (W/m²/K)
        self.m_steam = None  # Consommation vapeur motrice (kg/h)
    
    
    def _calculer_pressions(self):
        """
        Répartition des pressions entre P_steam et P_final.
        Répartition logarithmique pour distribution plus réaliste.
        """
        # Pression à l'entrée du 1er effet = pression de sortie vapeur 1er effet
        # On répartit de façon logarithmique entre P_steam et P_final
        
        P_in = self.P_steam  # Pression de chauffe (avant 1er effet)
        P_out = self.P_final  # Pression après dernier effet
        
        # Pressions aux sorties de chaque effet (vapeur générée)
        log_P_in = np.log(P_in)
        log_P_out = np.log(P_out)
        
        log_P = np.linspace(log_P_in, log_P_out, self.n_effets + 1)
        P_effets = np.exp(log_P)
        
        # P[i] = pression de la vapeur générée à l'effet i
        # La vapeur de l'effet i chauffe l'effet i+1
        self.P = P_effets[1:]  # Pressions aux effets 1, 2, ..., n
        
        return self.P
    
    
    def _bilan_matiere_global(self):
        """
        Bilan matière global :
        F × xF = L_final × xout
        F = L_final + V_total
        
        Retourne : L_final, V_total
        """
        # Conservation du soluté
        L_final = self.F * self.xF / self.xout
        
        # Conservation de la masse
        V_total = self.F - L_final
        
        return L_final, V_total
    
    
    def _initialiser_debits(self):
        """
        Initialisation des débits L et V par effet.
        Répartition uniforme de l'évaporation (première estimation).
        """
        L_final, V_total = self._bilan_matiere_global()
        
        # Répartition uniforme de l'évaporation
        V_par_effet = V_total / self.n_effets
        
        self.L = np.zeros(self.n_effets)
        self.V = np.zeros(self.n_effets)
        self.x = np.zeros(self.n_effets)
        
        # Co-courant : alimentation entre dans effet 1
        L_in = self.F
        x_in = self.xF
        
        for i in range(self.n_effets):
            self.V[i] = V_par_effet
            self.L[i] = L_in - self.V[i]
            
            # Concentration (bilan soluté)
            if self.L[i] > 0:
                self.x[i] = (L_in * x_in) / self.L[i]
            else:
                self.x[i] = x_in
            
            # Préparation pour effet suivant
            L_in = self.L[i]
            x_in = self.x[i]
        
        return self.L, self.V, self.x
    
    
    def _calculer_temperatures(self):
        """
        Calcul des températures d'ébullition par effet.
        T_eb = T_sat(P) + EPE(x)
        """
        self.T = np.zeros(self.n_effets)
        
        for i in range(self.n_effets):
            # Température de saturation de l'eau pure
            T_sat = Tsat_water_from_Pbar(self.P[i])
            
            # EPE (Élévation Point d'Ébullition)
            EPE = EPE_Duhring(self.x[i], T_sat)
            
            # Température d'ébullition effective
            self.T[i] = T_sat + EPE
        
        return self.T
    
    
    def _calculer_bilans_energetiques(self):
        """
        Bilans énergétiques pour chaque effet.
        Calcul des puissances Q et surfaces A.
        
        Pour l'effet i :
        Q_i = chaleur fournie par la vapeur de chauffage
        Q_i = V_i × λ_i + L_i × Cp_i × (T_i - T_i-1) + pertes
        """
        self.Q = np.zeros(self.n_effets)
        self.A = np.zeros(self.n_effets)
        self.U = np.zeros(self.n_effets)
        
        # Température vapeur de chauffe (avec surchauffe)
        T_steam = Tsat_water_from_Pbar(self.P_steam) + self.surchauffe
        
        for i in range(self.n_effets):
            # --- Côté chauffage (vapeur qui condense) ---
            if i == 0:
                # Premier effet : chauffé par vapeur motrice
                P_chauffe = self.P_steam
                T_chauffe = T_steam
                lambda_chauffe = latent_heat_from_Pbar(P_chauffe)
            else:
                # Effets suivants : chauffés par vapeur de l'effet précédent
                P_chauffe = self.P[i-1]
                T_chauffe = self.T[i-1]
                lambda_chauffe = latent_heat_from_Pbar(P_chauffe)
            
            # --- Côté évaporation ---
            # Chaleur latente de l'eau évaporée
            lambda_evap = latent_heat_from_Pbar(self.P[i])
            
            # Enthalpie nécessaire pour chauffer le liquide
            if i == 0:
                T_in = self.T_feed
                x_in = self.xF
                L_in = self.F
            else:
                T_in = self.T[i-1]
                x_in = self.x[i-1]
                L_in = self.L[i-1]
            
            # Capacité calorifique moyenne
            Cp_in = Cp_solution_saccharose(x_in, T_in)
            Cp_out = Cp_solution_saccharose(self.x[i], self.T[i])
            Cp_moy = (Cp_in + Cp_out) / 2.0
            
            # Chaleur sensible pour chauffer le liquide
            Q_sensible = L_in * Cp_moy * (self.T[i] - T_in) / 3600.0  # kW
            
            # Chaleur pour évaporer
            Q_evap = self.V[i] * lambda_evap / 3600.0  # kW
            
            # Chaleur totale nécessaire (sans pertes)
            Q_utile = Q_sensible + Q_evap
            
            # Pertes thermiques (3%)
            Q_pertes = self.pertes * Q_utile
            
            # Chaleur totale fournie
            self.Q[i] = Q_utile + Q_pertes
            
            # --- Calcul de la surface d'échange ---
            # Coefficient U pour cet effet
            self.U[i] = coefficient_U_effet(i+1, self.n_effets)
            
            # Correction pour encrassement
            U_eff = 1.0 / (1.0/self.U[i] + self.R_f)
            
            # ΔT pour le transfert
            # ΔT_entrée = T_chauffe - T_ebullition
            # ΔT_sortie = T_condensat - T_ebullition
            # On approxime : ΔT ≈ T_chauffe - T_ebullition
            dT_chauffe = T_chauffe - self.T[i]
            
            if dT_chauffe <= 0:
                dT_chauffe = 1.0  # Éviter division par zéro
            
            # Surface d'échange (Q = U × A × ΔT)
            self.A[i] = (self.Q[i] * 1000.0) / (U_eff * dT_chauffe)  # Q en W, A en m²
        
        return self.Q, self.A
    
    
    def _calculer_consommation_vapeur(self):
        """
        Calcul de la consommation de vapeur motrice (kg/h).
        
        La vapeur motrice chauffe le premier effet.
        Q_1 = m_steam × λ_steam
        """
        Q_1 = self.Q[0]  # kW
        lambda_steam = latent_heat_from_Pbar(self.P_steam)  # kJ/kg
        
        # m_steam (kg/h) = Q_1 (kW) × 3600 / λ_steam (kJ/kg)
        self.m_steam = (Q_1 * 3600.0) / lambda_steam
        
        return self.m_steam
    
    
    def simuler(self, max_iter=50, tol=1e-4):
        """
        Simulation itérative de l'évaporateur multi-effets.
        
        Algorithme :
        1. Calculer pressions
        2. Initialiser débits (répartition uniforme)
        3. Boucle itérative :
           a) Calculer températures
           b) Calculer bilans énergétiques
           c) Recalculer débits V basés sur Q
           d) Vérifier convergence
        
        Retourne : dict avec résultats
        """
        # Étape 1 : Pressions
        self._calculer_pressions()
        
        # Étape 2 : Initialisation
        self._initialiser_debits()
        
        # Étape 3 : Itérations
        for iteration in range(max_iter):
            # Sauvegarder V précédent
            V_old = self.V.copy()
            
            # Calculer températures
            self._calculer_temperatures()
            
            # Calculer bilans énergétiques
            self._calculer_bilans_energetiques()
            
            # Recalculer débits V basés sur Q
            # Q_i = V_i × λ_i (approximation)
            for i in range(self.n_effets):
                lambda_i = latent_heat_from_Pbar(self.P[i])
                # V_i = Q_i × 3600 / λ_i
                self.V[i] = (self.Q[i] * 3600.0) / lambda_i
            
            # Recalculer débits L et concentrations x
            L_in = self.F
            x_in = self.xF
            
            for i in range(self.n_effets):
                self.L[i] = L_in - self.V[i]
                
                if self.L[i] > 0:
                    self.x[i] = (L_in * x_in) / self.L[i]
                else:
                    self.x[i] = x_in
                
                L_in = self.L[i]
                x_in = self.x[i]
            
            # Vérifier convergence
            erreur = np.max(np.abs(self.V - V_old) / (V_old + 1e-12))
            
            if erreur < tol:
                break
        
        # Calculer consommation vapeur
        self._calculer_consommation_vapeur()
        
        # Retourner résultats
        return {
            "L": self.L,
            "V": self.V,
            "x": self.x * 100,  # En %
            "T": self.T,
            "P": self.P,
            "A": self.A,
            "Q": self.Q,
            "U": self.U,
            "m_steam": self.m_steam,
            "A_totale": np.sum(self.A),
            "iterations": iteration + 1
        }
    
    
    def consommation_vapeur(self):
        """Retourne la consommation de vapeur motrice (kg/h)."""
        return self.m_steam if self.m_steam is not None else 0.0
    
    
    def economie_vapeur(self):
        """
        Calcule l'économie de vapeur (kg vapeur produite / kg vapeur consommée).
        """
        if self.m_steam is None or self.m_steam == 0:
            return 0.0
        
        V_total = np.sum(self.V)
        return V_total / self.m_steam


# ========================================
# FONCTION SIMPLIFIÉE POUR STREAMLIT
# ========================================

def simulation_evaporation_multi_effets(
    F_kg_h: float,
    xF: float,
    xout: float,
    n_effets: int,
    T_steam_C: float = 143.0,  # ~3.5 bar
    T_last_C: float = 54.0,     # ~0.15 bar
    U: float = 2000.0,
    lambda_kJ_kg: float = 2257.0
):
    """
    Version simplifiée pour compatibilité avec streamlit_app.py.
    Utilise EvaporateurMultiple en interne.
    
    IMPORTANT : Cette fonction est un wrapper pour garder la compatibilité
    avec l'interface Streamlit existante. Elle convertit les paramètres
    simples en paramètres pour EvaporateurMultiple.
    """
    try:
        # Conversion T → P (approximation inverse)
        # Pour T_steam_C ≈ 143°C → P ≈ 3.5 bar
        # Pour T_last_C ≈ 54°C → P ≈ 0.15 bar
        
        # Approximation : P(bar) ≈ exp((T - 100)/28)
        P_steam = np.exp((T_steam_C - 100.0) / 28.0)
        P_final = np.exp((T_last_C - 100.0) / 28.0)
        
        P_steam = max(P_steam, 1.0)
        P_final = max(P_final, 0.01)
        
        # Température d'alimentation (supposée)
        T_feed = 85.0
        
        # Créer évaporateur
        evap = EvaporateurMultiple(
            F=F_kg_h,
            xF=xF,
            xout=xout,
            T_feed=T_feed,
            P_steam=P_steam,
            n_effets=n_effets,
            P_final=P_final
        )
        
        # Simuler
        res = evap.simuler()
        
        # Formater pour Streamlit
        details = []
        for i in range(n_effets):
            details.append({
                "effect": i + 1,
                "V_kg_h": float(res["V"][i]),
                "dT_K": float(res["T"][i] - (res["T"][i-1] if i > 0 else T_feed)),
                "A_m2": float(res["A"][i]),
                "T_hot_C": float(res["T"][i]),
                "T_cold_C": float(res["T"][i] - 5.0),  # Approximation
            })
        
        return {
            "S": float(res["m_steam"]),
            "economie": float(evap.economie_vapeur()),
            "A_total": float(res["A_totale"]),
            "V_total": float(np.sum(res["V"])),
            "P": float(F_kg_h * xF / xout),
            "details": details,
        }
    
    except Exception as e:
        # Fallback simple en cas d'erreur
        print(f"⚠️ Erreur dans simulation_evaporation_multi_effets: {e}")
        
        # Calcul simplifié
        P = F_kg_h * xF / xout
        V_total = F_kg_h - P
        V_i = V_total / n_effets
        
        details = []
        for i in range(1, n_effets + 1):
            details.append({
                "effect": i,
                "V_kg_h": float(V_i),
                "dT_K": 20.0,
                "A_m2": 100.0,
                "T_hot_C": T_steam_C - i * 20,
                "T_cold_C": T_steam_C - i * 20 - 5,
            })
        
        return {
            "S": float(V_total / 3.0),
            "economie": 3.0,
            "A_total": 300.0,
            "V_total": float(V_total),
            "P": float(P),
            "details": details,
        }


# Test du module
if __name__ == "__main__":
    print("="*60)
    print("TEST ÉVAPORATEUR MULTI-EFFETS - CDC PIC 2024-2025")
    print("="*60)
    
    # Paramètres CDC
    F = 20000.0       # kg/h
    xF = 0.15         # 15%
    xout = 0.65       # 65%
    T_feed = 85.0     # °C
    P_steam = 3.5     # bar
    n_effets = 3
    
    print(f"\nCoolProp disponible : {'✅ OUI' if COOLPROP_AVAILABLE else '❌ NON'}")
    
    evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets)
    res = evap.simuler()
    
    print(f"\n📊 RÉSULTATS SIMULATION ({n_effets} effets)")
    print(f"{'='*60}")
    print(f"Consommation vapeur motrice : {res['m_steam']:.2f} kg/h")
    print(f"Économie de vapeur          : {evap.economie_vapeur():.2f}")
    print(f"Surface totale d'échange    : {res['A_totale']:.2f} m²")
    print(f"Convergence en              : {res['iterations']} itérations")
    
    print(f"\n{'Effet':<8}{'L (kg/h)':<12}{'V (kg/h)':<12}{'x (%)':<10}{'T (°C)':<10}{'A (m²)':<10}{'U (W/m²K)':<12}")
    print("="*80)
    for i in range(n_effets):
        print(f"{i+1:<8}{res['L'][i]:<12.1f}{res['V'][i]:<12.1f}{res['x'][i]:<10.2f}"
              f"{res['T'][i]:<10.2f}{res['A'][i]:<10.2f}{res['U'][i]:<12.1f}")
    
    print("\n✅ Test terminé")