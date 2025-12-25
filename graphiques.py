# graphiques.py
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd

def init_output_dir():
    """Crée le dossier de sortie si nécessaire."""
    os.makedirs("resultats", exist_ok=True)

def graphique_cristallisation_complet(hist, titre="Profil de cristallisation - CDC"):
    """Génère les graphiques de cristallisation complets."""
    init_output_dir()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    t = hist["t"]
    
    # 1. Température et sursaturation
    ax1.plot(t, hist["T"], 'b-', label='Température (°C)', linewidth=2)
    ax1.set_xlabel("Temps (s)", fontsize=12)
    ax1.set_ylabel("Température (°C)", fontsize=12, color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    ax1_twin = ax1.twinx()
    ax1_twin.plot(t, hist["S"], 'r-', label='Sursaturation S', linewidth=2)
    ax1_twin.set_ylabel("Sursaturation S", fontsize=12, color='r')
    ax1_twin.tick_params(axis='y', labelcolor='r')
    ax1_twin.legend(loc='upper right')
    ax1.set_title("Température et sursaturation", fontsize=14, fontweight='bold')
    
    # 2. Taille moyenne
    Lmean_um = [l * 1e6 for l in hist["Lmean"]]
    ax2.plot(t, Lmean_um, 'g-', linewidth=2)
    ax2.axhline(y=450, color='r', linestyle='--', linewidth=2, label='Cible: 450 μm')
    ax2.fill_between(t, 400, 500, alpha=0.2, color='green', label='Zone cible')
    ax2.set_xlabel("Temps (s)", fontsize=12)
    ax2.set_ylabel("Lmean (μm)", fontsize=12)
    ax2.set_title("Taille moyenne des cristaux", fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Coefficient de variation
    CV_pct = [cv * 100 for cv in hist["CV"]]
    ax3.plot(t, CV_pct, 'm-', linewidth=2)
    ax3.axhline(y=30, color='r', linestyle='--', linewidth=2, label='Limite: 30%')
    ax3.fill_between(t, 0, 30, alpha=0.2, color='orange', label='Zone conforme')
    ax3.set_xlabel("Temps (s)", fontsize=12)
    ax3.set_ylabel("CV (%)", fontsize=12)
    ax3.set_title("Coefficient de variation", fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Concentration
    ax4.plot(t, hist["C"], 'b-', label='Concentration C', linewidth=2)
    ax4.plot(t, hist["Cs"], 'r--', label='Solubilité C*', linewidth=2)
    ax4.set_xlabel("Temps (s)", fontsize=12)
    ax4.set_ylabel("Concentration (g/100g)", fontsize=12)
    ax4.set_title("Évolution de la concentration", fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(titre, fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig("resultats/cristallisation_complet.png", dpi=300, bbox_inches='tight')
    plt.close()

def graphique_evaporation_complet(res_evap, titre="Analyse évaporateurs - CDC"):
    """Génère les graphiques d'évaporation complets."""
    init_output_dir()
    
    details = res_evap.get("details", [])
    if not details:
        return
    
    df = details if isinstance(details, list) else pd.DataFrame(details)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    effets = np.arange(1, len(df) + 1)
    
    # 1. Températures
    ax1.plot(effets, df["T_hot_C"], 'o-', linewidth=2, markersize=8, label='T chaud')
    ax1.plot(effets, df["T_cold_C"], 's-', linewidth=2, markersize=8, label='T froid')
    ax1.set_xlabel("Effet", fontsize=12)
    ax1.set_ylabel("Température (°C)", fontsize=12)
    ax1.set_title("Températures d'ébullition par effet", fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Surfaces d'échange
    ax2.bar(effets, df["A_m2"], color='skyblue', edgecolor='navy', linewidth=2)
    ax2.set_xlabel("Effet", fontsize=12)
    ax2.set_ylabel("Surface (m²)", fontsize=12)
    ax2.set_title("Surface d'échange par effet", fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Ajouter valeurs sur les barres
    for i, v in enumerate(df["A_m2"]):
        ax2.text(i + 1, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Eau évaporée
    ax3.plot(effets, df["V_kg_h"], 'o-', color='green', linewidth=2, markersize=8)
    ax3.set_xlabel("Effet", fontsize=12)
    ax3.set_ylabel("Eau évaporée (kg/h)", fontsize=12)
    ax3.set_title("Évaporation par effet", fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # 4. ΔT
    ax4.plot(effets, df["dT_K"], 'o-', color='red', linewidth=2, markersize=8)
    ax4.set_xlabel("Effet", fontsize=12)
    ax4.set_ylabel("ΔT (K)", fontsize=12)
    ax4.set_title("ΔT de fonctionnement", fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    plt.suptitle(titre, fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig("resultats/evaporation_complet.png", dpi=300, bbox_inches='tight')
    plt.close()

def graphique_sensibilite(df_sens, param_x, param_y, titre="Analyse de sensibilité - CDC"):
    """Génère un graphique de sensibilité."""
    init_output_dir()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if param_x in df_sens.columns and param_y in df_sens.columns:
        ax.plot(df_sens[param_x], df_sens[param_y], 'o-', linewidth=2, markersize=8)
        ax.set_xlabel(param_x, fontsize=12)
        ax.set_ylabel(param_y, fontsize=12)
        ax.set_title(titre, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        filename = f"resultats/sensibilite_{param_x}_{param_y}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        return filename
    
    return None

def graphique_comparaison_profils(resultats, titre="Comparaison profils refroidissement - CDC"):
    """Génère un graphique de comparaison des profils."""
    init_output_dir()
    
    profils = list(resultats.keys())
    Lmean_values = [r["Lmean_um"] for r in resultats.values()]
    CV_values = [r["CV_pct"] for r in resultats.values()]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Graphique Lmean
    bars1 = ax1.bar(profils, Lmean_values, color=['skyblue', 'lightgreen', 'lightcoral'])
    ax1.axhline(y=450, color='r', linestyle='--', linewidth=2, label='Cible 450 μm')
    ax1.set_xlabel("Profil", fontsize=12)
    ax1.set_ylabel("Lmean (μm)", fontsize=12)
    ax1.set_title("Taille moyenne finale", fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Ajouter valeurs sur barres
    for bar, val in zip(bars1, Lmean_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    # Graphique CV
    bars2 = ax2.bar(profils, CV_values, color=['skyblue', 'lightgreen', 'lightcoral'])
    ax2.axhline(y=30, color='r', linestyle='--', linewidth=2, label='Limite 30%')
    ax2.set_xlabel("Profil", fontsize=12)
    ax2.set_ylabel("CV (%)", fontsize=12)
    ax2.set_title("Coefficient de variation", fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Ajouter valeurs sur barres
    for bar, val in zip(bars2, CV_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.suptitle(titre, fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig("resultats/comparaison_profils.png", dpi=300, bbox_inches='tight')
    plt.close()