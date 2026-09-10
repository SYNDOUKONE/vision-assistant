"""
VISION — Module Overlay HUD (Mini-fenêtre transparente au premier plan)
Affiche le texte parlé par VISION en direct dans un mini-HUD flottant sans vol de focus.
"""

import sys
import os
import threading

_overlay_root = None
_overlay_label = None
_overlay_thread = None
_overlay_visible = False
_overlay_desactive = (sys.platform == "darwin")  # Désactivé sur macOS Tkinter/Pygame SDL conflict

def _lancer_fenetre_hud():
    """Initialise et lance la fenêtre Tkinter HUD transparente au premier plan."""
    global _overlay_root, _overlay_label, _overlay_visible, _overlay_desactive
    
    if _overlay_desactive:
        return

    try:
        import tkinter as tk
        _overlay_root = tk.Tk()
        _overlay_root.title("VISION HUD")
        _overlay_root.geometry("450x120+50+50")  # Coin supérieur gauche
        _overlay_root.overrideredirect(True)       # Sans bordures système
        _overlay_root.attributes("-topmost", True)  # Toujours au premier plan
        _overlay_root.attributes("-alpha", 0.85)    # Transparence
        
        # Fond sombre futuriste
        _overlay_root.configure(bg="#0B0E14")

        # Container avec bordure lumineuse cyan
        frame = tk.Frame(_overlay_root, bg="#0B0E14", highlightbackground="#00F0FF", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        titre = tk.Label(frame, text="VISION — Assistant Vocal", font=("Helvetica", 9, "bold"), fg="#00F0FF", bg="#0B0E14")
        titre.pack(anchor="w", padx=10, pady=(5, 0))

        _overlay_label = tk.Label(
            frame, 
            text="En attente...", 
            font=("Helvetica", 11), 
            fg="#E2E8F0", 
            bg="#0B0E14", 
            wraplength=420, 
            justify="left"
        )
        _overlay_label.pack(fill="both", expand=True, padx=10, pady=5)

        _overlay_visible = True
        _overlay_root.mainloop()
    except BaseException as e:
        print(f"[OVERLAY] HUD Tkinter indisponible ({e}). L'affichage Web HUD prend le relais.")
        _overlay_desactive = True
        _overlay_visible = False

def afficher_texte_hud(texte):
    """Met à jour le texte affiché sur l'overlay HUD."""
    global _overlay_root, _overlay_label, _overlay_visible, _overlay_thread, _overlay_desactive
    
    if _overlay_desactive:
        return

    if not _overlay_visible or _overlay_root is None:
        try:
            _overlay_thread = threading.Thread(target=_lancer_fenetre_hud, daemon=True)
            _overlay_thread.start()
        except Exception as e:
            print(f"[OVERLAY] Impossible d'initialiser l'HUD : {e}")
            _overlay_desactive = True
            return


    if _overlay_label and _overlay_root:
        try:
            _overlay_root.after(0, lambda: _overlay_label.config(text=texte))
        except Exception:
            pass

def masquer_hud():
    """Ferme l'overlay HUD."""
    global _overlay_root, _overlay_visible
    if _overlay_root:
        try:
            _overlay_root.after(0, _overlay_root.destroy)
        except Exception:
            pass
    _overlay_visible = False
