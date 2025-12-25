"""
optimisation.py
----------------
Module d'optimisation et analyse économique conforme CDC Section 4.3
"""

import numpy as np
import pandas as pd
from evaporateurs import EvaporateurMultiple


def etudier_nombre_effets(F=20000.0, Xf=0.15, Xout=0.65, T_feed=85.0, 
                         P_steam=3.5, min_effets=2, max_effets=5):
    """
    Étudie l'impact du nombre d'effets (CDC Section 4.1.2).
    
    Retourne DataFrame avec :
    - Consommation de vapeur
    - Économie de vapeur
    - Surface totale d'échange
    - Coût d'investissement approximatif
    
    Conforme CDC : étude pour 2, 3, 4, 5 effets
    """
    resultats = []
    
    for n in range(min_effets, max_effets + 1):
        try:
            evap = EvaporateurMultiple(F, Xf, Xout, T_feed, P_steam, n_effets=n)
            sim = evap.simuler()
            
            # Indicateurs CDC
            m_steam = evap.consommation_vapeur()
            economie = evap.economie_vapeur()
            A_tot = sim["A_totale"]
            
            # Coût d'investissement (formule CDC)
            C_evap = 15000.0 * (A_tot ** 0.65)  # €
            
            # Production (kg/h)
            production = F * Xf / Xout
            
            resultats.append({
                "n_effets": n,
                "m_steam_kg_h": float(m_steam),
                "economie": float(economie),
                "A_totale_m2": float(A_tot),
                "Cevap_€": float(C_evap),
                "production_kg_h": float(production),
                "consommation_specifique": float(m_steam / production) if production > 0 else 0
            })
        except Exception as e:
            print(f"⚠️ Erreur pour {n} effets : {e}")
            continue
    
    return pd.DataFrame(resultats)


def couts_exploitation_annuels(m_steam_h, cout_vapeur_t=25.0,
                               eau_m3_h=10.0, cout_eau=0.15,
                               P_elec_kW=50.0, cout_elec=0.12,
                               n_operateurs=3, cout_mo=35.0,
                               h_an=8000.0):
    """
    Calcule les coûts d'exploitation annuels (OPEX) conforme CDC.
    
    Paramètres CDC :
    - Vapeur 3.5 bar : 25 €/tonne
    - Eau de refroidissement : 0.15 €/m³
    - Électricité : 0.12 €/kWh
    - Main d'œuvre : 35 €/h-opérateur
    - Heures fonctionnement : 8000 h/an
    
    Retour : dict avec OPEX_total_€ et détails
    """
    # Vapeur
    vapeur_t_h = m_steam_h / 1000.0  # t/h
    C_vapeur = vapeur_t_h * cout_vapeur_t * h_an
    
    # Eau de refroidissement (estimation basée sur condensats)
    C_eau = eau_m3_h * cout_eau * h_an
    
    # Électricité (agitation, pompes, auxiliaires)
    C_elec = P_elec_kW * cout_elec * h_an
    
    # Main d'œuvre
    C_mo = n_operateurs * cout_mo * h_an
    
    # Coûts totaux
    OPEX_total = C_vapeur + C_eau + C_elec + C_mo
    
    return {
        "OPEX_total_€": OPEX_total,
        "C_vapeur_€": C_vapeur,
        "C_eau_€": C_eau,
        "C_elec_€": C_elec,
        "C_mo_€": C_mo,
        "details": {
            "vapeur_t_an": vapeur_t_h * h_an,
            "eau_m3_an": eau_m3_h * h_an,
            "elec_kWh_an": P_elec_kW * h_an,
            "heures_mo": n_operateurs * h_an
        }
    }


def analyse_economique_globale(Cevap_total, Ccrist, Cech,
                               OPEX_annuel,
                               production_t_an,
                               prix_vente_tonne=800.0,  # Prix vente sucre estimé
                               taux_actualisation=0.1,
                               duree_vie=10):
    """
    Analyse économique simplifiée conforme CDC Section 4.3.2.
    
    Calcule :
    - TCI (Total Capital Investment)
    - OPEX annuel
    - Coût de production par tonne
    - ROI approximatif
    - VAN (Valeur Actuelle Nette) simplifiée
    
    Retour : dict avec indicateurs économiques
    """
    # CORRECTION : Assurer que OPEX_annuel est un nombre, pas un dict
    if isinstance(OPEX_annuel, dict):
        # Si c'est le dict complet de couts_exploitation_annuels
        if "OPEX_total_€" in OPEX_annuel:
            OPEX_value = OPEX_annuel["OPEX_total_€"]
        else:
            # Sinon, prendre la somme des valeurs
            OPEX_value = sum([v for v in OPEX_annuel.values() if isinstance(v, (int, float))])
    else:
        OPEX_value = float(OPEX_annuel)
    
    # Capital total (TCI)
    TCI = float(Cevap_total) + float(Ccrist) + float(Cech)
    
    # Revenus annuels
    revenus_annuels = float(production_t_an) * float(prix_vente_tonne)
    
    # Bénéfice annuel avant amortissement
    benefice_annuel = revenus_annuels - OPEX_value
    
    # Coût de production par tonne
    cout_tonne = OPEX_value / max(float(production_t_an), 1e-6)
    
    # ROI approximatif (simplifié)
    ROI_ans = TCI / max(benefice_annuel, 1e-6)
    
    # VAN simplifiée (actualisation sur durée de vie)
    cash_flows = [benefice_annuel] * duree_vie
    cash_flows[0] -= TCI  # Investissement initial
    
    VAN = sum([cf / ((1 + taux_actualisation) ** (i + 1)) 
              for i, cf in enumerate(cash_flows)])
    
    # Taux de rentabilité interne approximatif
    try:
        TRI_approx = benefice_annuel / TCI if TCI > 0 else 0
    except:
        TRI_approx = 0
    
    return {
        "TCI_€": TCI,
        "OPEX_annuel_€": OPEX_value,
        "revenus_annuels_€": revenus_annuels,
        "benefice_annuel_€": benefice_annuel,
        "cout_tonne_€": cout_tonne,
        "ROI_ans": ROI_ans,
        "VAN_€": VAN,
        "TRI_approx": TRI_approx,
        "prix_vente_tonne_€": prix_vente_tonne,
        "duree_vie_ans": duree_vie,
        "production_t_an": production_t_an
    }


def analyse_scenario_optimal(F=20000.0, xF=0.15, xout=0.65, T_feed=85.0, P_steam=3.5):
    """
    Détermine le scénario optimal (nombre d'effets) basé sur critères économiques.
    
    Combine :
    1. Analyse technique (nombre d'effets)
    2. Analyse économique (TCI, OPEX, ROI)
    3. Recommandation optimale
    """
    # Étude nombre d'effets
    df_effets = etudier_nombre_effets(F, xF, xout, T_feed, P_steam, min_effets=2, max_effets=5)
    
    scenarios = []
    
    for idx, row in df_effets.iterrows():
        # Calcul OPEX pour ce scénario
        opex_details = couts_exploitation_annuels(
            m_steam_h=row["m_steam_kg_h"],
            cout_vapeur_t=25.0,
            eau_m3_h=10.0,
            cout_eau=0.15,
            P_elec_kW=50.0,
            cout_elec=0.12,
            n_operateurs=3,
            cout_mo=35.0
        )
        
        # Estimation coûts autres équipements
        C_crist = 25000.0 * (5.0 ** 0.6)  # Volume cristalliseur approx
        C_ech = 8000.0 * (row["A_totale_m2"] ** 0.7)
        
        # Production annuelle (tonnes/an)
        production_t_an = (row["production_kg_h"] * 8000) / 1000
        
        # Analyse économique complète
        eco = analyse_economique_globale(
            Cevap_total=row["Cevap_€"],
            Ccrist=C_crist,
            Cech=C_ech,
            OPEX_annuel=opex_details["OPEX_total_€"],  # CORRECTION
            production_t_an=production_t_an,
            prix_vente_tonne=800.0
        )
        
        scenarios.append({
            "n_effets": row["n_effets"],
            "m_steam_kg_h": row["m_steam_kg_h"],
            "economie": row["economie"],
            "A_totale_m2": row["A_totale_m2"],
            "Cevap_€": row["Cevap_€"],
            "OPEX_annuel_€": opex_details["OPEX_total_€"],  # CORRECTION
            "cout_tonne_€": eco["cout_tonne_€"],
            "ROI_ans": eco["ROI_ans"],
            "VAN_€": eco["VAN_€"],
            "benefice_annuel_€": eco["benefice_annuel_€"]
        })
    
    df_scenarios = pd.DataFrame(scenarios)
    
    # Recommandation basée sur VAN maximale
    optimal_idx = df_scenarios["VAN_€"].idxmax() if not df_scenarios.empty else 0
    
    return {
        "scenarios": df_scenarios,
        "optimal": df_scenarios.iloc[optimal_idx].to_dict() if not df_scenarios.empty else {},
        "recommendation": f"Configuration optimale : {df_scenarios.iloc[optimal_idx]['n_effets']} effets" if not df_scenarios.empty else "Aucune configuration viable"
    }


# Test du module
if __name__ == "__main__":
    print("="*70)
    print("TEST MODULE OPTIMISATION - CDC PIC 2024-2025")
    print("="*70)
    
    # Test étude nombre d'effets
    print("\n📊 ÉTUDE NOMBRE D'EFFETS (CDC 4.1.2)")
    df_effets = etudier_nombre_effets()
    print(df_effets.to_string(index=False))
    
    # Test analyse économique
    print("\n💰 ANALYSE ÉCONOMIQUE POUR 3 EFFETS")
    opex = couts_exploitation_annuels(m_steam_h=df_effets.iloc[1]["m_steam_kg_h"])
    print(f"OPEX annuel : {opex['OPEX_total_€']:,.0f} €")
    print(f"Détails : Vapeur {opex['C_vapeur_€']:,.0f} €, "
          f"Eau {opex['C_eau_€']:,.0f} €, "
          f"Élec {opex['C_elec_€']:,.0f} €, "
          f"MO {opex['C_mo_€']:,.0f} €")
    
    # Test analyse économique globale
    print("\n📈 ANALYSE ÉCONOMIQUE GLOBALE")
    C_evap = 15000.0 * (df_effets.iloc[1]["A_totale_m2"] ** 0.65)
    eco = analyse_economique_globale(
        Cevap_total=C_evap,
        Ccrist=25000.0 * (5.0 ** 0.6),
        Cech=8000.0 * (df_effets.iloc[1]["A_totale_m2"] ** 0.7),
        OPEX_annuel=opex["OPEX_total_€"],
        production_t_an=(df_effets.iloc[1]["production_kg_h"] * 8000) / 1000
    )
    print(f"TCI : {eco['TCI_€']:,.0f} €")
    print(f"VAN : {eco['VAN_€']:,.0f} €")
    print(f"ROI : {eco['ROI_ans']:.1f} ans")
    print(f"TRI approx : {eco['TRI_approx']:.2%}")
    
    # Test scénario optimal
    print("\n🎯 ANALYSE SCÉNARIO OPTIMAL")
    result = analyse_scenario_optimal()
    print(f"Recommandation : {result['recommendation']}")
    if result['optimal']:
        print(f"VAN optimale : {result['optimal']['VAN_€']:,.0f} €")
        print(f"ROI optimal : {result['optimal']['ROI_ans']:.1f} ans")
    
    print("\n✅ Test terminé")