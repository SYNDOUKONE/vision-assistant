"""
VISION — Data Science
Chargement, nettoyage, analyse, visualisation et rapport de données.
"""

import os
import time
import base64
import subprocess
from pathlib import Path
from datetime import datetime

from modules import state
from modules.file_manager import resoudre_chemin, chercher_fichier

# Bibliothèques optionnelles
try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import seaborn as sns
    from scipy import stats as scipy_stats
    DATA_LIBS_OK = True
except ImportError:
    DATA_LIBS_OK = False

DATA_EXPORT_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "VISION_Data")


def _data_export_dir():
    os.makedirs(DATA_EXPORT_DIR, exist_ok=True)
    return DATA_EXPORT_DIR


def data_charger(chemin):
    """Charge un fichier CSV, Excel ou JSON dans le DataFrame courant."""
    if not DATA_LIBS_OK:
        return False, "Les bibliothèques pandas/matplotlib ne sont pas installées."
    try:
        chemin_resolu = resoudre_chemin(chemin) or chemin
        print(f"[DATA] Tentative de chargement : {chemin} -> {chemin_resolu}")
        
        if not os.path.exists(chemin_resolu):
            print(f"[DATA] Non trouvé directement, recherche de '{chemin}' dans les dossiers communs...")
            resultats, _ = chercher_fichier(chemin)
            if resultats:
                chemin_resolu = resultats[0]
                print(f"[DATA] Fichier trouvé via recherche : {chemin_resolu}")
            else:
                print(f"[DATA] Échec de la recherche pour '{chemin}'")
                return False, f"Fichier introuvable : {chemin}"

        ext = Path(chemin_resolu).suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(chemin_resolu, sep=None, engine='python', encoding_errors='replace')
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(chemin_resolu)
        elif ext == ".json":
            df = pd.read_json(chemin_resolu)
        elif ext == ".tsv":
            df = pd.read_csv(chemin_resolu, sep='\t', encoding_errors='replace')
        else:
            return False, f"Format non supporté : {ext}. Formats acceptés : CSV, Excel, JSON, TSV."
        state._data_df = df
        state._data_path = chemin_resolu
        lignes, colonnes = df.shape
        return True, f"Fichier chargé : {lignes} lignes, {colonnes} colonnes. Colonnes : {', '.join(df.columns.tolist()[:10])}"
    except Exception as e:
        return False, f"Erreur chargement : {e}"


def data_nettoyer():
    """Nettoie automatiquement le DataFrame : doublons, valeurs manquantes, types."""
    if state._data_df is None:
        return False, "Aucun fichier chargé. Commencez par charger un fichier."
    try:
        df = state._data_df
        rapport = []

        nb_doublons = df.duplicated().sum()
        if nb_doublons > 0:
            df = df.drop_duplicates()
            rapport.append(f"{nb_doublons} doublons supprimés")

        na_avant = df.isnull().sum()
        cols_na = na_avant[na_avant > 0]
        if not cols_na.empty:
            for col in cols_na.index:
                if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                    median = df[col].median()
                    df[col] = df[col].fillna(median)
                    rapport.append(f"Colonne '{col}': {cols_na[col]} valeurs manquantes remplacées par la médiane ({median:.2f})")
                else:
                    mode = df[col].mode()
                    val = mode.iloc[0] if not mode.empty else 'Inconnu'
                    df[col] = df[col].fillna(val)
                    rapport.append(f"Colonne '{col}': {cols_na[col]} valeurs manquantes remplacées par le mode ('{val}')")

        df.columns = [c.strip().replace(' ', '_') for c in df.columns]

        for col in df.columns:
            try:
                if df[col].dtype == object:
                    converted = pd.to_numeric(df[col], errors='coerce')
                    if converted.notna().sum() > len(df) * 0.7:
                        df[col] = converted
            except Exception:
                pass

        state._data_df = df
        apres = df.shape
        if not rapport:
            rapport.append("Données déjà propres, aucune correction nécessaire")
        resume = f"Nettoyage terminé. {' | '.join(rapport)}. Taille finale : {apres[0]} lignes, {apres[1]} colonnes."
        return True, resume
    except Exception as e:
        return False, f"Erreur nettoyage : {e}"


def data_analyser(question=""):
    """Produit une analyse statistique descriptive complète du DataFrame."""
    if state._data_df is None:
        return False, "Aucun fichier chargé."
    try:
        df = state._data_df
        lignes, colonnes_n = df.shape
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        resume = [f"Analyse de {lignes} lignes et {colonnes_n} colonnes."]

        if num_cols:
            resume.append(f"Colonnes numériques ({len(num_cols)}) : {', '.join(num_cols[:6])}.")
            for col in num_cols[:5]:
                moyenne = round(df[col].mean(), 2)
                mini = round(df[col].min(), 2)
                maxi = round(df[col].max(), 2)
                resume.append(f"  - {col} : moyenne={moyenne}, min={mini}, max={maxi}")

        if cat_cols:
            resume.append(f"Colonnes textuelles ({len(cat_cols)}) : {', '.join(cat_cols[:6])}.")
            for col in cat_cols[:3]:
                top = df[col].value_counts().head(3)
                resume.append(f"  - {col} : top valeurs = {', '.join([str(v) for v in top.index.tolist()])}.")

        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr().abs()
            corr_pairs = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    val = corr_matrix.iloc[i, j]
                    if val > 0.5:
                        corr_pairs.append(f"{num_cols[i]} / {num_cols[j]} ({val:.2f})")
            if corr_pairs:
                resume.append(f"Corrélations fortes : {', '.join(corr_pairs[:3])}.")

        return True, " ".join(resume)
    except Exception as e:
        return False, f"Erreur analyse : {e}"


def data_visualiser(type_viz="histogramme", col_x=None, col_y=None, titre=""):
    """Génère un graphique et l'ouvre automatiquement."""
    if state._data_df is None:
        return False, "Aucun fichier chargé."
    if not DATA_LIBS_OK:
        return False, "Matplotlib non disponible."
    try:
        df = state._data_df
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        if col_x is None and num_cols:
            col_x = num_cols[0]
        if col_y is None and len(num_cols) > 1:
            col_y = num_cols[1]

        plt.style.use('dark_background')
        sns.set_palette("coolwarm")
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor('#0d0d1a')
        ax.set_facecolor('#0d0d1a')

        titre_plot = titre or f"VISION — {type_viz.capitalize()} de {col_x}"
        type_l = type_viz.lower()

        if type_l in ["histogramme", "histo", "distribution"]:
            if col_x and col_x in df.columns:
                ax.hist(df[col_x].dropna(), bins=30, color='#4ca8e8', edgecolor='#0d0d1a', alpha=0.85)
                ax.set_xlabel(col_x, color='white')
                ax.set_ylabel("Fréquence", color='white')
            else:
                return False, f"Colonne '{col_x}' introuvable."

        elif type_l in ["scatter", "nuage", "correlation"]:
            if col_x and col_y and col_x in df.columns and col_y in df.columns:
                ax.scatter(df[col_x], df[col_y], color='#4ca8e8', alpha=0.6, s=40, edgecolors='none')
                try:
                    m, b, r, p, _ = scipy_stats.linregress(df[col_x].dropna(), df[col_y].dropna())
                    x_line = [df[col_x].min(), df[col_x].max()]
                    ax.plot(x_line, [m * x + b for x in x_line], color='#e84c4c', lw=2, label=f'r={r:.2f}')
                    ax.legend(facecolor='#1a1a2e', edgecolor='#4ca8e8', labelcolor='white')
                except Exception:
                    pass
                ax.set_xlabel(col_x, color='white')
                ax.set_ylabel(col_y, color='white')
            else:
                return False, f"Colonnes {col_x} ou {col_y} introuvables."

        elif type_l in ["barres", "bar", "barre"]:
            col = col_x or (cat_cols[0] if cat_cols else num_cols[0] if num_cols else None)
            if col and col in df.columns:
                counts = df[col].value_counts().head(15)
                bars = ax.barh(counts.index.astype(str), counts.values, color='#4ca8e8', alpha=0.85)
                ax.set_xlabel("Nombre", color='white')
                ax.set_ylabel(col, color='white')
                for bar, val in zip(bars, counts.values):
                    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2, str(val),
                            va='center', color='white', fontsize=9)
            else:
                return False, "Colonne introuvable pour le graphique en barres."

        elif type_l in ["camembert", "pie", "secteurs"]:
            col = col_x or (cat_cols[0] if cat_cols else None)
            if col and col in df.columns:
                counts = df[col].value_counts().head(8)
                wedges, texts, autotexts = ax.pie(
                    counts.values, labels=counts.index.astype(str),
                    autopct='%1.1f%%', startangle=140,
                    colors=sns.color_palette("coolwarm", len(counts))
                )
                for t in texts + autotexts:
                    t.set_color('white')
            else:
                return False, "Colonne introuvable pour le camembert."

        elif type_l in ["heatmap", "chaleur", "correlation_map"]:
            corr = df[num_cols].corr() if len(num_cols) > 1 else None
            if corr is not None:
                plt.close()
                fig, ax = plt.subplots(figsize=(12, 9))
                fig.patch.set_facecolor('#0d0d1a')
                ax.set_facecolor('#0d0d1a')
                sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm',
                            ax=ax, linewidths=0.5, linecolor='#0d0d1a',
                            cbar_kws={'shrink': 0.8})
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', color='white', fontsize=9)
                ax.set_yticklabels(ax.get_yticklabels(), color='white', fontsize=9)
            else:
                return False, "Pas assez de colonnes numériques pour une heatmap."

        elif type_l in ["boxplot", "boite", "quartiles"]:
            cols_plot = num_cols[:6] if num_cols else []
            if cols_plot:
                df[cols_plot].boxplot(ax=ax, patch_artist=True,
                    boxprops=dict(facecolor='#4ca8e8', color='white'),
                    medianprops=dict(color='#e84c4c', lw=2),
                    whiskerprops=dict(color='white'),
                    capprops=dict(color='white'),
                    flierprops=dict(markerfacecolor='#e84c4c', marker='o', markersize=4))
                ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right', color='white')
                ax.set_ylabel("Valeurs", color='white')
            else:
                return False, "Pas de colonnes numériques pour un boxplot."

        elif type_l in ["ligne", "line", "courbe", "tendance"]:
            if col_x and col_x in df.columns:
                data_line = df[col_x].dropna().values
                ax.plot(range(len(data_line)), data_line, color='#4ca8e8', lw=1.5, alpha=0.9)
                ax.set_xlabel("Index", color='white')
                ax.set_ylabel(col_x, color='white')
            else:
                return False, f"Colonne '{col_x}' introuvable."
        else:
            return False, f"Type de graphique '{type_viz}' non reconnu. Types disponibles : histogramme, scatter, barres, camembert, heatmap, boxplot, ligne."

        ax.set_title(titre_plot, pad=16, color='white', fontsize=14, fontweight='bold')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_edgecolor('#2a2a3e')
        plt.tight_layout()

        ts = int(time.time())
        nom = f"vision_graph_{type_l}_{ts}.png"
        out = os.path.join(_data_export_dir(), nom)
        plt.savefig(out, dpi=140, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close('all')

        subprocess.Popen(f'start "" "{out}"', shell=True)
        return True, out
    except Exception as e:
        plt.close('all')
        return False, f"Erreur génération graphique : {e}"


def data_rapport_html():
    """Génère un rapport HTML complet avec toutes les stats et graphiques."""
    if state._data_df is None:
        return False, "Aucun fichier chargé."
    try:
        df = state._data_df
        nom_fichier = Path(state._data_path).name if state._data_path else "données"
        ts = int(time.time())
        out = os.path.join(_data_export_dir(), f"rapport_vision_{ts}.html")

        images_b64 = {}
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = df.select_dtypes(include='object').columns.tolist()

        plt.style.use('dark_background')

        def _fig_to_b64():
            import io as _io
            buf = _io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#0d0d1a', dpi=100)
            plt.close('all')
            buf.seek(0)
            return base64.b64encode(buf.read()).decode()

        for col in num_cols[:4]:
            fig, ax = plt.subplots(figsize=(7, 4))
            fig.patch.set_facecolor('#0d0d1a'); ax.set_facecolor('#0d0d1a')
            ax.hist(df[col].dropna(), bins=25, color='#4ca8e8', edgecolor='#0d0d1a', alpha=0.85)
            ax.set_title(f"Distribution — {col}", color='white', fontsize=11)
            ax.set_xlabel(col, color='white'); ax.set_ylabel("Fréquence", color='white')
            ax.tick_params(colors='white')
            for s in ax.spines.values(): s.set_edgecolor('#2a2a3e')
            plt.tight_layout()
            images_b64[f"hist_{col}"] = _fig_to_b64()

        if len(num_cols) >= 2:
            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor('#0d0d1a'); ax.set_facecolor('#0d0d1a')
            sns.heatmap(df[num_cols].corr(), annot=True, fmt=".2f", cmap='coolwarm', ax=ax,
                        linewidths=0.5, linecolor='#0d0d1a')
            ax.set_title("Matrice de Corrélation", color='white', fontsize=11)
            ax.tick_params(colors='white')
            plt.tight_layout()
            images_b64["heatmap"] = _fig_to_b64()

        for col in cat_cols[:2]:
            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_facecolor('#0d0d1a'); ax.set_facecolor('#0d0d1a')
            counts = df[col].value_counts().head(12)
            ax.barh(counts.index.astype(str), counts.values, color='#4ca8e8', alpha=0.85)
            ax.set_title(f"Distribution — {col}", color='white', fontsize=11)
            ax.tick_params(colors='white')
            plt.tight_layout()
            images_b64[f"bar_{col}"] = _fig_to_b64()

        stats_html = ""
        if num_cols:
            stats_html = df[num_cols].describe().round(2).to_html(classes="stats-table", border=0)

        imgs_html = ""
        for key, b64 in images_b64.items():
            imgs_html += f'<div class="graph-card"><img src="data:image/png;base64,{b64}" /></div>\n'

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Rapport VISION — {nom_fichier}</title>
<style>
  body {{ margin:0; background:#050508; color:#c8d6e5; font-family:'Segoe UI',sans-serif; }}
  header {{ background:linear-gradient(135deg,#0d0d1a,#1a1a3e); padding:32px 48px; border-bottom:1px solid #2a2a3e; }}
  h1 {{ margin:0; color:#4ca8e8; font-size:2rem; letter-spacing:4px; }}
  .meta {{ color:#8899aa; font-size:13px; margin-top:8px; }}
  main {{ padding:32px 48px; }}
  h2 {{ color:#4ca8e8; font-size:1rem; letter-spacing:3px; text-transform:uppercase; border-bottom:1px solid #2a2a3e; padding-bottom:8px; margin-top:40px; }}
  .stats-table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  .stats-table th {{ background:#1a1a3e; color:#4ca8e8; padding:8px 14px; text-align:left; }}
  .stats-table td {{ padding:7px 14px; border-bottom:1px solid #1a1a3e; }}
  .stats-table tr:hover td {{ background:#0d0d1a; }}
  .graphs {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(480px,1fr)); gap:24px; }}
  .graph-card {{ background:#0d0d1a; border:1px solid #2a2a3e; border-radius:12px; overflow:hidden; padding:12px; }}
  .graph-card img {{ width:100%; border-radius:6px; }}
  footer {{ text-align:center; padding:32px; color:#3a4a5a; font-size:12px; }}
</style>
</head>
<body>
<header>
  <h1>V · I · S · I · O · N</h1>
  <div class="meta">Rapport d'analyse — {nom_fichier} — {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
  {df.shape[0]} lignes &nbsp;·&nbsp; {df.shape[1]} colonnes</div>
</header>
<main>
  <h2>Statistiques Descriptives</h2>
  {stats_html}
  <h2>Visualisations</h2>
  <div class="graphs">{imgs_html}</div>
</main>
<footer>Généré par VISION · Intelligence Artificielle</footer>
</body></html>"""

        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
        subprocess.Popen(f'start "" "{out}"', shell=True)
        return True, out
    except Exception as e:
        return False, f"Erreur génération rapport : {e}"
