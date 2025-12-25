# sensibilite.py
"""
Module d'analyse de sensibilité paramétrique.
CDC Section 4.1.3
"""

import numpy as np
import pandas as pd
from evaporateurs import EvaporateurMultiple


def sensibilite_pression_vapeur(F=20000.0, xF=0.15, xout=0.65, 
                                T_feed=85.0, n_effets=3,
                                P_min=2.5, P_max=4.5, n_points=10):
    """
    Analyse de sensibilité : Pression vapeur de chauffe (2.5 à 4.5 bar).
    CDC Section 4.1.3
    
    Pour chaque P, calcule :
    - Consommation de vapeur
    - Surfaces d'échange
    - Températures dans chaque effet
    """
    P_range = np.linspace(P_min, P_max, n_points)
    resultats = []
    
    for P_steam in P_range:
        try:
            evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets)
            sim = evap.simuler()
            
            resultats.append({
                "P_steam_bar": float(P_steam),
                "m_steam_kg_h": float(evap.consommation_vapeur()),
                "A_totale_m2": float(sim["A_totale"]),
                "T_effet_1": float(sim["T"][0]),
                "T_effet_2": float(sim["T"][1]) if n_effets >= 2 else 0,
                "T_effet_3": float(sim["T"][2]) if n_effets >= 3 else 0,
                "economie": float(evap.economie_vapeur())
            })
        except:
            pass
    
    return pd.DataFrame(resultats)


def sensibilite_concentration_finale(F=20000.0, xF=0.15, T_feed=85.0,
                                    P_steam=3.5, n_effets=3,
                                    xout_min=0.60, xout_max=0.70, n_points=6):
    """
    Analyse de sensibilité : Concentration finale (60% à 70%).
    CDC Section 4.1.3
    """
    xout_range = np.linspace(xout_min, xout_max, n_points)
    resultats = []
    
    for xout in xout_range:
        try:
            evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets)
            sim = evap.simuler()
            
            resultats.append({
                "xout_pct": float(xout * 100),
                "m_steam_kg_h": float(evap.consommation_vapeur()),
                "A_totale_m2": float(sim["A_totale"]),
                "V_total_kg_h": float(np.sum(sim["V"])),
                "economie": float(evap.economie_vapeur())
            })
        except:
            pass
    
    return pd.DataFrame(resultats)


def sensibilite_debit_alimentation(xF=0.15, xout=0.65, T_feed=85.0,
                                  P_steam=3.5, n_effets=3,
                                  variation_pct=20):
    """
    Analyse de sensibilité : Débit d'alimentation (±20%).
    CDC Section 4.1.3
    """
    F_nominal = 20000.0
    F_min = F_nominal * (1 - variation_pct/100)
    F_max = F_nominal * (1 + variation_pct/100)
    
    F_range = np.linspace(F_min, F_max, 9)
    resultats = []
    
    for F in F_range:
        try:
            evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets)
            sim = evap.simuler()
            
            resultats.append({
                "F_kg_h": float(F),
                "variation_pct": float((F - F_nominal) / F_nominal * 100),
                "m_steam_kg_h": float(evap.consommation_vapeur()),
                "A_totale_m2": float(sim["A_totale"]),
                "economie": float(evap.economie_vapeur())
            })
        except:
            pass
    
    return pd.DataFrame(resultats)


def sensibilite_temperature_alimentation(F=20000.0, xF=0.15, xout=0.65,
                                        P_steam=3.5, n_effets=3,
                                        T_min=75.0, T_max=95.0, n_points=5):
    """
    Analyse de sensibilité : Température d'alimentation (75 à 95°C).
    CDC Section 4.1.3
    """
    T_range = np.linspace(T_min, T_max, n_points)
    resultats = []
    
    for T_feed in T_range:
        try:
            evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets)
            sim = evap.simuler()
            
            resultats.append({
                "T_feed_C": float(T_feed),
                "m_steam_kg_h": float(evap.consommation_vapeur()),
                "A_totale_m2": float(sim["A_totale"]),
                "economie": float(evap.economie_vapeur())
            })
        except:
            pass
    
    return pd.DataFrame(resultats)


def sensibilite_nombre_effets(F=20000.0, xF=0.15, xout=0.65, T_feed=85.0,
                              P_steam=3.5, n_min=2, n_max=6):
    """
    Analyse de sensibilité : Nombre d'effets (pour Streamlit).
    Compatible avec l'interface existante.
    """
    resultats = []
    
    for n in range(n_min, n_max + 1):
        try:
            evap = EvaporateurMultiple(F, xF, xout, T_feed, P_steam, n_effets=n)
            sim = evap.simuler()
            
            resultats.append({
                "Nombre_effets": n,
                "Debit_vapeur_S": float(evap.consommation_vapeur()),
                "Surface_totale_A": float(sim["A_totale"]),
                "Economie": float(evap.economie_vapeur())
            })
        except:
            pass
    
    return pd.DataFrame(resultats)


def analyse_sensibilite_complete():
    """
    Exécute toutes les analyses de sensibilité (CDC Section 4.1.3).
    
    Retourne : dict avec tous les DataFrames
    """
    print("🔄 Analyse de sensibilité paramétrique...")
    
    analyses = {
        "pression_vapeur": sensibilite_pression_vapeur(),
        "concentration_finale": sensibilite_concentration_finale(),
        "debit_alimentation": sensibilite_debit_alimentation(),
        "temperature_alimentation": sensibilite_temperature_alimentation(),
        "nombre_effets": sensibilite_nombre_effets()
    }
    
    print("✅ Analyses terminées")
    
    return analyses


# ========================================
# TESTS
# ========================================

if __name__ == "__main__":
    print("="*70)
    print("TEST ANALYSE DE SENSIBILITÉ - CDC PIC 2024-2025")
    print("="*70)
    
    analyses = analyse_sensibilite_complete()
    
    print("\n📊 SENSIBILITÉ PRESSION VAPEUR (2.5 - 4.5 bar)")
    print(analyses["pression_vapeur"].to_string(index=False))
    
    print("\n📊 SENSIBILITÉ CONCENTRATION FINALE (60 - 70%)")
    print(analyses["concentration_finale"].to_string(index=False))
    
    print("\n📊 SENSIBILITÉ DÉBIT ALIMENTATION (±20%)")
    print(analyses["debit_alimentation"].to_string(index=False))
    
    print("\n📊 SENSIBILITÉ TEMPÉRATURE ALIMENTATION (75 - 95°C)")
    print(analyses["temperature_alimentation"].to_string(index=False))
    
    print("\n📊 SENSIBILITÉ NOMBRE D'EFFETS (2 - 6)")
    print(analyses["nombre_effets"].to_string(index=False))
    
    print("\n✅ Test terminé")