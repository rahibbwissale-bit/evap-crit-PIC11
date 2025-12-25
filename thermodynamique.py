# thermodynamique.py
import numpy as np

# Import CoolProp (obligatoire selon CDC)
try:
    from CoolProp.CoolProp import PropsSI
    COOLPROP_AVAILABLE = True
except ImportError:
    print("⚠️ CoolProp non installé. Installer avec : pip install CoolProp")
    COOLPROP_AVAILABLE = False


def to_float(x, default=0.0):
    """Force un scalaire float même si x est un tableau numpy."""
    try:
        a = np.asarray(x)
        if a.size == 0:
            return float(default)
        return float(a.reshape(-1)[0])
    except Exception:
        return float(default)


def Tsat_water_from_Pbar(Pbar):
    """
    Température de saturation de l'eau en fonction de la pression (bar).
    Utilise CoolProp pour des valeurs exactes.
    
    Pbar : pression en bar (absolu)
    Retourne : température de saturation en °C
    """
    P = max(to_float(Pbar), 0.01)
    P_Pa = P * 1e5  # Conversion bar → Pa
    
    if COOLPROP_AVAILABLE:
        try:
            T_K = PropsSI('T', 'P', P_Pa, 'Q', 0, 'Water')  # Q=0 : liquide saturé
            return float(T_K - 273.15)  # K → °C
        except:
            pass
    
    # Fallback si CoolProp échoue
    return 100.0 + 28.0 * np.log(P)


def latent_heat_kJkg(Tc):
    """
    Chaleur latente de vaporisation de l'eau (kJ/kg) à température T(°C).
    Utilise CoolProp.
    
    Tc : température en °C
    Retourne : chaleur latente en kJ/kg
    """
    T = to_float(Tc, 100.0)
    T_K = T + 273.15  # °C → K
    
    if COOLPROP_AVAILABLE:
        try:
            # Enthalpie vapeur saturée
            h_vap = PropsSI('H', 'T', T_K, 'Q', 1, 'Water')  # Q=1 : vapeur saturée
            # Enthalpie liquide saturé
            h_liq = PropsSI('H', 'T', T_K, 'Q', 0, 'Water')  # Q=0 : liquide saturé
            # Chaleur latente
            L_vap = (h_vap - h_liq) / 1000.0  # J/kg → kJ/kg
            return float(L_vap)
        except:
            pass
    
    # Fallback : corrélation empirique
    return max(2500.0 - 2.42 * T, 100.0)


def latent_heat_from_Pbar(Pbar):
    """
    Chaleur latente à une pression donnée (bar).
    """
    P = max(to_float(Pbar), 0.01)
    P_Pa = P * 1e5
    
    if COOLPROP_AVAILABLE:
        try:
            h_vap = PropsSI('H', 'P', P_Pa, 'Q', 1, 'Water')
            h_liq = PropsSI('H', 'P', P_Pa, 'Q', 0, 'Water')
            return float((h_vap - h_liq) / 1000.0)  # kJ/kg
        except:
            pass
    
    # Fallback
    T = Tsat_water_from_Pbar(Pbar)
    return latent_heat_kJkg(T)


def EPE_Duhring(x_saccharose, T_water):
    """
    Élévation du Point d'Ébullition (EPE) par corrélation de Dühring.
    
    x_saccharose : fraction massique (0-1)
    T_water : température d'ébullition de l'eau pure (°C)
    
    Retourne : ΔT_epe (°C)
    
    Corrélation CDC : EPE dépend de la concentration et de T
    """
    x = to_float(x_saccharose)
    T = to_float(T_water)
    
    if x <= 0:
        return 0.0
    
    # Corrélation Dühring pour saccharose (empirique)
    # EPE ≈ K(T) × x^n
    # Source : Perry's Handbook, Mullin
    K = 0.08 * (1.0 + 0.004 * T)  # Coefficient dépendant de T
    n = 1.2  # Exposant empirique
    
    EPE = K * (x ** n) * 100  # x en fraction → EPE en °C
    
    return float(max(EPE, 0.0))


def Cp_solution_saccharose(x_saccharose, T_C):
    """
    Capacité calorifique de la solution de saccharose (kJ/kg/K).
    
    x_saccharose : fraction massique (0-1)
    T_C : température (°C)
    
    Mélange idéal : Cp_mix = x×Cp_saccharose + (1-x)×Cp_eau
    """
    x = to_float(x_saccharose)
    T = to_float(T_C)
    T_K = T + 273.15
    
    # Cp eau (CoolProp)
    if COOLPROP_AVAILABLE:
        try:
            Cp_water_J = PropsSI('C', 'T', T_K, 'P', 101325, 'Water')  # J/kg/K
            Cp_water = Cp_water_J / 1000.0  # kJ/kg/K
        except:
            Cp_water = 4.18  # Fallback
    else:
        Cp_water = 4.18
    
    # Cp saccharose (données littérature)
    Cp_sucre = 1.25  # kJ/kg/K (approximation)
    
    # Mélange idéal
    Cp_mix = x * Cp_sucre + (1 - x) * Cp_water
    
    return float(Cp_mix)


def enthalpie_solution(x, T_C, T_ref=25.0):
    """
    Enthalpie de la solution (kJ/kg) par rapport à T_ref.
    
    H = ∫(T_ref → T) Cp(T) dT
    
    Approximation : H ≈ Cp_moy × (T - T_ref)
    """
    Cp = Cp_solution_saccharose(x, T_C)
    dT = to_float(T_C) - to_float(T_ref)
    return float(Cp * dT)


def enthalpie_vapeur(P_bar):
    """
    Enthalpie de la vapeur saturée (kJ/kg) à pression P (bar).
    Utilise CoolProp.
    """
    P = max(to_float(P_bar), 0.01)
    P_Pa = P * 1e5
    
    if COOLPROP_AVAILABLE:
        try:
            h_vap = PropsSI('H', 'P', P_Pa, 'Q', 1, 'Water')
            return float(h_vap / 1000.0)  # J/kg → kJ/kg
        except:
            pass
    
    # Fallback
    T = Tsat_water_from_Pbar(P_bar)
    lambda_v = latent_heat_kJkg(T)
    h_liq = Cp_solution_saccharose(0.0, T) * T
    return float(h_liq + lambda_v)


def enthalpie_liquide(P_bar):
    """
    Enthalpie du liquide saturé (kJ/kg) à pression P (bar).
    """
    P = max(to_float(P_bar), 0.01)
    P_Pa = P * 1e5
    
    if COOLPROP_AVAILABLE:
        try:
            h_liq = PropsSI('H', 'P', P_Pa, 'Q', 0, 'Water')
            return float(h_liq / 1000.0)  # kJ/kg
        except:
            pass
    
    # Fallback
    T = Tsat_water_from_Pbar(P_bar)
    return float(Cp_solution_saccharose(0.0, T) * T)


def LMTD(dT1, dT2):
    """
    Différence de température logarithmique moyenne (LMTD).
    
    dT1 : ΔT à l'entrée (K ou °C)
    dT2 : ΔT à la sortie (K ou °C)
    """
    dT1 = to_float(dT1)
    dT2 = to_float(dT2)
    
    if dT1 <= 0.0 or dT2 <= 0.0:
        return 0.0
    if abs(dT1 - dT2) < 1e-9:
        return float(dT1)
    
    return float((dT1 - dT2) / np.log(dT1 / dT2))


def coefficient_U_effet(effet_num, n_total):
    """
    Coefficient global de transfert thermique U (W/m²/K) pour chaque effet.
    
    CDC spécifie : U₁ = 2500, U₂ = 2200, U₃ = 1800 W/m²·K
    
    Pour n effets, interpolation/extrapolation linéaire.
    """
    effet = int(effet_num)
    
    # Valeurs CDC pour 3 effets
    if n_total == 3:
        U_map = {1: 2500, 2: 2200, 3: 1800}
        return float(U_map.get(effet, 1800))
    
    # Interpolation linéaire pour autres nombres d'effets
    U_start = 2500
    U_end = 1800
    
    if effet <= 1:
        return float(U_start)
    if effet >= n_total:
        return float(U_end)
    
    # Interpolation
    U = U_start - (U_start - U_end) * (effet - 1) / max(n_total - 1, 1)
    return float(U)


# Test CoolProp au chargement du module
if __name__ == "__main__":
    if COOLPROP_AVAILABLE:
        print("✅ CoolProp disponible")
        print(f"Tsat(3.5 bar) = {Tsat_water_from_Pbar(3.5):.2f} °C")
        print(f"λ(120°C) = {latent_heat_kJkg(120):.2f} kJ/kg")
    else:
        print("❌ CoolProp NON disponible - utilisation des fallbacks")