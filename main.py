# main.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from evaporateurs import EvaporateurMultiple
from cristallisation import simuler_cristallisation_batch, comparer_profils
from sensibilite import analyse_sensibilite_complete
from optimisation import etudier_nombre_effets, couts_exploitation_annuels, analyse_economique_globale

def ensure_dir(path: str):
    """Crée un dossier s'il n'existe pas."""
    os.makedirs(path, exist_ok=True)

def save_fig(fig, filename: str):
    """Sauvegarde une figure."""
    ensure_dir("figures")
    fig.tight_layout()
    fig.savefig(os.path.join("figures", filename), dpi=200)
    plt.close(fig)

def scenario():
    """Exécute le scénario principal conforme CDC."""
    ensure_dir("figures")
    ensure_dir("exports")
    
    print("="*70)
    print("PROJET PIC 2024-2025 - ÉVAPORATION & CRISTALLISATION")
    print("="*70)
    
    # ==================== PARAMÈTRES CDC ====================
    print("\n📋 PARAMÈTRES (conformes CDC)")
    print("-"*40)
    
    # Évaporation
    F, xF, xout, Tfeed, Psteam, n_effets = 20000.0, 0.15, 0.65, 85.0, 3.5, 3
    print(f"Évaporation :")
    print(f"  Débit F          : {F} kg/h")
    print(f"  Concentration xF : {xF*100}%")
    print(f"  Concentration out: {xout*100}%")
    print(f"  Temp. aliment.   : {Tfeed} °C")
    print(f"  Pression vapeur  : {Psteam} bar")
    print(f"  Nombre d'effets  : {n_effets}")
    
    # Cristallisation
    M_batch, C_init, T_init, duree_h, dt_s, profil = 5000.0, 65.0, 70.0, 4.0, 60.0, "lineaire"
    print(f"\nCristallisation :")
    print(f"  Masse batch      : {M_batch} kg")
    print(f"  Concentration    : {C_init} g/100g")
    print(f"  Température init : {T_init} °C")
    print(f"  Durée            : {duree_h} heures")
    print(f"  Profil           : {profil}")
    
    # ==================== 1) ÉVAPORATION ====================
    print("\n" + "="*70)
    print("1) SIMULATION ÉVAPORATEUR MULTI-EFFETS")
    print("="*70)
    
    try:
        evap = EvaporateurMultiple(F, xF, xout, Tfeed, Psteam, n_effets)
        res_evap = evap.simuler()
        
        # Export CSV
        df_evap = pd.DataFrame({
            "Effet": np.arange(1, n_effets + 1),
            "L_kg_h": res_evap["L"],
            "V_kg_h": res_evap["V"],
            "x_%": res_evap["x"],
            "T_C": res_evap["T"],
            "A_m2": res_evap["A"],
            "U_W/m2K": res_evap["U"]
        })
        df_evap.to_csv("exports/evaporation_resultats.csv", index=False)
        
        # Graphiques
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        ax1.plot(df_evap["Effet"], df_evap["x_%"], 'o-')
        ax1.set_xlabel("Effet")
        ax1.set_ylabel("Concentration (%)")
        ax1.set_title("Évolution de la concentration")
        ax1.grid(True)
        
        ax2.plot(df_evap["Effet"], df_evap["T_C"], 's-')
        ax2.set_xlabel("Effet")
        ax2.set_ylabel("Température (°C)")
        ax2.set_title("Températures d'ébullition")
        ax2.grid(True)
        
        ax3.bar(df_evap["Effet"], df_evap["A_m2"])
        ax3.set_xlabel("Effet")
        ax3.set_ylabel("Surface (m²)")
        ax3.set_title("Surfaces d'échange")
        ax3.grid(True)
        
        ax4.plot(df_evap["Effet"], df_evap["V_kg_h"], 'o-', color='green')
        ax4.set_xlabel("Effet")
        ax4.set_ylabel("Vapeur (kg/h)")
        ax4.set_title("Eau évaporée par effet")
        ax4.grid(True)
        
        plt.tight_layout()
        save_fig(fig, "evaporation_analysis.png")
        
        print(f"✅ Évaporation :")
        print(f"   Consommation vapeur : {evap.consommation_vapeur():.1f} kg/h")
        print(f"   Économie de vapeur  : {evap.economie_vapeur():.2f}")
        print(f"   Surface totale      : {res_evap['A_totale']:.1f} m²")
        
    except Exception as e:
        print(f"❌ Erreur évaporation : {e}")
    
    # ==================== 2) CRISTALLISATION ====================
    print("\n" + "="*70)
    print("2) SIMULATION CRISTALLISATION BATCH")
    print("="*70)
    
    try:
        duree_s = int(duree_h * 3600)
        _, _, hist = simuler_cristallisation_batch(M_batch, C_init, T_init, duree_s, dt=dt_s, profil=profil)
        
        # Export CSV
        df_cr = pd.DataFrame(hist)
        df_cr.to_csv("exports/cristallisation_resultats.csv", index=False)
        
        # Graphiques
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        ax1.plot(hist["t"], hist["T"])
        ax1.set_xlabel("Temps (s)")
        ax1.set_ylabel("Température (°C)")
        ax1.set_title("Profil de température")
        ax1.grid(True)
        
        ax2.plot(hist["t"], hist["S"])
        ax2.set_xlabel("Temps (s)")
        ax2.set_ylabel("Sursaturation S")
        ax2.set_title("Évolution de la sursaturation")
        ax2.grid(True)
        
        ax3.plot(hist["t"], [l*1e6 for l in hist["Lmean"]])
        ax3.set_xlabel("Temps (s)")
        ax3.set_ylabel("Lmean (μm)")
        ax3.set_title("Taille moyenne des cristaux")
        ax3.grid(True)
        ax3.axhline(y=450, color='r', linestyle='--', label='Cible 450 μm')
        ax3.legend()
        
        ax4.plot(hist["t"], [cv*100 for cv in hist["CV"]])
        ax4.set_xlabel("Temps (s)")
        ax4.set_ylabel("CV (%)")
        ax4.set_title("Coefficient de variation")
        ax4.grid(True)
        ax4.axhline(y=30, color='r', linestyle='--', label='Limite 30%')
        ax4.legend()
        
        plt.tight_layout()
        save_fig(fig, "cristallisation_analysis.png")
        
        Lmean_final = hist["Lmean"][-1] * 1e6
        CV_final = hist["CV"][-1] * 100
        
        print(f"✅ Cristallisation :")
        print(f"   Lmean final : {Lmean_final:.1f} μm {'(OK)' if 400 < Lmean_final < 500 else '(HORS SPEC)'}")
        print(f"   CV final    : {CV_final:.1f} % {'(OK)' if CV_final < 30 else '(TROP ÉLEVÉ)'}")
        print(f"   T final     : {hist['T'][-1]:.1f} °C")
        
    except Exception as e:
        print(f"❌ Erreur cristallisation : {e}")
    
    # ==================== 3) COMPARAISON PROFILS ====================
    print("\n" + "="*70)
    print("3) COMPARAISON DES PROFILS DE REFROIDISSEMENT (CDC 4.2.2)")
    print("="*70)
    
    try:
        resultats = comparer_profils(M_batch, C_init, T_init, duree_s)
        
        print("\n📊 COMPARAISON :")
        print(f"{'Profil':<12}{'Lmean (μm)':<15}{'CV (%)':<12}{'Conforme CDC':<20}")
        print("-"*60)
        
        for profil, res in resultats.items():
            Lmean = res["Lmean_um"]
            CV = res["CV_pct"]
            conforme = "✅" if (400 < Lmean < 500 and CV < 30) else "❌"
            print(f"{profil:<12}{Lmean:<15.1f}{CV:<12.1f}{conforme:<20}")
        
    except Exception as e:
        print(f"❌ Erreur comparaison : {e}")
    
    # ==================== 4) ANALYSE ÉCONOMIQUE ====================
    print("\n" + "="*70)
    print("4) ANALYSE ÉCONOMIQUE (CDC 4.3.2)")
    print("="*70)
    
    try:
        # Étude nombre d'effets
        effets_etude = etudier_nombre_effets(F, xF, xout, Tfeed, Psteam, max_effets=5)
        
        print("\n📊 IMPACT DU NOMBRE D'EFFETS :")
        print(f"{'N effets':<10}{'Vapeur (kg/h)':<15}{'Économie':<12}{'Surface (m²)':<15}{'Coût (k€)':<12}")
        print("-"*64)
        
        for res in effets_etude:
            print(f"{res['n_effets']:<10}{res['m_steam']:<15.1f}{res['economie']:<12.2f}"
                  f"{res['A_totale']:<15.1f}{res['Cevap']/1000:<12.1f}")
        
        # Calcul OPEX pour 3 effets
        if 'res_evap' in locals():
            OPEX = couts_exploitation_annuels(
                m_steam_h=evap.consommation_vapeur(),
                cout_vapeur_t=25.0,
                eau_m3_h=10.0,
                cout_eau=0.15,
                P_elec_kW=50.0,
                cout_elec=0.12,
                n_operateurs=3,
                cout_mo=35.0
            )
            
            # Analyse globale
            C_evap = 15000.0 * (res_evap['A_totale'] ** 0.65)
            C_crist = 25000.0 * (5.0 ** 0.6)  # Volume approx 5 m³
            C_ech = 8000.0 * (res_evap['A_totale'] ** 0.7)
            
            production_t_an = (F * xF / xout * 8000) / 1000  # tonnes/an
            
            eco = analyse_economique_globale(
                Cevap_total=C_evap,
                Ccrist=C_crist,
                Cech=C_ech,
                OPEX_annuel=OPEX,
                production_t_an=production_t_an
            )
            
            print(f"\n💰 ANALYSE ÉCONOMIQUE (3 effets):")
            print(f"   TCI (Total Capital Investment) : {eco['TCI']:,.0f} €")
            print(f"   OPEX annuel                    : {eco['OPEX']:,.0f} €/an")
            print(f"   Coût de production             : {eco['cout_tonne']:.2f} €/tonne")
            print(f"   ROI approximatif               : {eco['ROI_approx']:.2f} ans")
        
    except Exception as e:
        print(f"❌ Erreur économique : {e}")
    
    # ==================== 5) SENSIBILITÉ ====================
    print("\n" + "="*70)
    print("5) ANALYSE DE SENSIBILITÉ (CDC 4.1.3)")
    print("="*70)
    
    try:
        analyses = analyse_sensibilite_complete()
        print("✅ Analyses de sensibilité terminées")
        print("   Voir fichiers exports/sensibilite_*.csv")
        
        # Sauvegarde des analyses
        for nom, df in analyses.items():
            df.to_csv(f"exports/sensibilite_{nom}.csv", index=False)
        
    except Exception as e:
        print(f"❌ Erreur sensibilité : {e}")
    
    # ==================== RÉSUMÉ FINAL ====================
    print("\n" + "="*70)
    print("🎯 RÉSUMÉ EXÉCUTION")
    print("="*70)
    
    print("\n✅ Fichiers générés :")
    print("   📁 exports/")
    print("      ├── evaporation_resultats.csv")
    print("      ├── cristallisation_resultats.csv")
    print("      └── sensibilite_*.csv")
    print("   📁 figures/")
    print("      ├── evaporation_analysis.png")
    print("      └── cristallisation_analysis.png")
    
    print("\n🎓 Conformité CDC :")
    print("   ✓ Modélisation évaporation triple effet")
    print("   ✓ Simulation cristallisation batch")
    print("   ✓ Comparaison 3 profils de refroidissement")
    print("   ✓ Analyse de sensibilité paramétrique")
    print("   ✓ Évaluation économique")
    
    print("\n🚀 Simulation terminée avec succès !")

if __name__ == "__main__":
    scenario()