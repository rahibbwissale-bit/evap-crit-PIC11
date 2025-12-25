# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

def lancer_simulation():
    """Lance la simulation principale."""
    try:
        # Exécute main.py
        result = subprocess.run([sys.executable, "main.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            messagebox.showinfo("Succès", 
                "✅ Simulation terminée avec succès !\n\n"
                "Les résultats sont disponibles dans :\n"
                "- exports/ : fichiers CSV\n"
                "- figures/ : graphiques PNG\n"
                "- resultats/ : rapports")
        else:
            messagebox.showerror("Erreur", 
                f"❌ Erreur lors de l'exécution :\n\n{result.stderr[:500]}")
    except Exception as e:
        messagebox.showerror("Exception", f"Erreur : {str(e)}")

def ouvrir_streamlit():
    """Ouvre Streamlit dans le navigateur."""
    try:
        subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
        messagebox.showinfo("Streamlit", 
            "🎈 Streamlit est en cours de lancement...\n\n"
            "Ouvrez votre navigateur à l'adresse :\n"
            "http://localhost:8501")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer Streamlit : {e}")

def interface():
    """Interface Tkinter principale."""
    root = tk.Tk()
    root.title("Projet PIC - Évaporation & Cristallisation")
    root.geometry("500x400")
    root.resizable(False, False)
    
    # Style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Titre
    title_frame = ttk.Frame(root)
    title_frame.pack(pady=20)
    
    title = ttk.Label(title_frame, 
                     text="🧪 Projet PIC 2024-2025\nÉvaporation & Cristallisation",
                     font=("Arial", 14, "bold"),
                     justify="center")
    title.pack()
    
    subtitle = ttk.Label(title_frame,
                        text="Simulation d'une unité intégrée\nConforme au cahier des charges CDC",
                        font=("Arial", 10),
                        justify="center")
    subtitle.pack(pady=5)
    
    # Boutons
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=30)
    
    btn_style = {"font": ("Arial", 11), "padding": 10}
    
    btn_sim = ttk.Button(button_frame, text="🚀 Lancer simulation complète",
                        command=lancer_simulation, **btn_style)
    btn_sim.pack(pady=10, fill='x', padx=50)
    
    btn_streamlit = ttk.Button(button_frame, text="🌐 Ouvrir interface Web (Streamlit)",
                              command=ouvrir_streamlit, **btn_style)
    btn_streamlit.pack(pady=10, fill='x', padx=50)
    
    # Informations
    info_frame = ttk.LabelFrame(root, text="📁 Dossiers générés", padding=10)
    info_frame.pack(pady=20, padx=20, fill='x')
    
    info_text = """
    • exports/      : Fichiers CSV des résultats
    • figures/      : Graphiques en PNG
    • resultats/    : Rapports et analyses
    • requirements.txt : Dépendances Python
    """
    
    info_label = ttk.Label(info_frame, text=info_text, font=("Courier", 9))
    info_label.pack()
    
    # Pied de page
    footer = ttk.Label(root, 
                      text="FST Settat - Université Hassan 1\nCDC PIC 2024-2025",
                      font=("Arial", 8),
                      justify="center",
                      foreground="gray")
    footer.pack(side="bottom", pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    interface()