import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# 1. Configuration de l'interface
st.set_page_config(
    page_title="Easygest Web App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Lecture et synchronisation avec les deux feuilles du fichier Excel
@st.cache_data
def charger_donnees_excel():
    nom_fichier = "EASYGEST.xlsm"
    
    # Structure de secours par défaut si le fichier est inaccessible ou vierge
    df_articles_defaut = pd.DataFrame({
        'Code_Article': ['ART001', 'ART002', 'ART003', 'ART004'],
        'Designation': ['Huile de palme 1L', 'Riz Cassé 50kg', 'Sucre Roux 1kg', 'Lait Concentré'],
        'Site': ['Abatta', 'Jules Vernes', 'San-Pedro', 'Abatta'],
        'Stock_Initial': [100, 50, 200, 30],
        'Stock_Minimum': [20, 10, 30, 15],
        'Prix_Unitaire_FCFA': [1200, 31000, 850, 650]
    })
    df_mouvements_defaut = pd.DataFrame(columns=['Date', 'Code_Article', 'Type_Mouvement', 'Quantite', 'Motif'])

    if os.path.exists(nom_fichier):
        try:
            # --- FEUILLE 1 : Référentiel des Articles ---
            df_art = pd.read_excel(nom_fichier, sheet_name=0)
            df_art.columns = [str(c).strip() for c in df_art.columns]
            
            mapping_art = {
                'Code': 'Code_Article', 'Article': 'Designation', 'Produit': 'Designation', 'Désignation': 'Designation',
                'Qte': 'Stock_Initial', 'Stock': 'Stock_Initial', 'Quantité': 'Stock_Initial', 'Quantite': 'Stock_Initial',
                'Prix': 'Prix_Unitaire_FCFA', 'PU': 'Prix_Unitaire_FCFA', 'Prix Unitaire': 'Prix_Unitaire_FCFA',
                'Stock Minimum': 'Stock_Minimum', 'Minimum': 'Stock_Minimum', 'Site': 'Site', 'Secteur': 'Site'
            }
            df_art = df_art.rename(columns=mapping_art)
            
            # Sécurisation des colonnes indispensables
            if 'Code_Article' not in df_art.columns: df_art['Code_Article'] = [f"ART{i+1:03d}" for i in range(len(df_art))]
            if 'Designation' not in df_art.columns: df_art['Designation'] = df_art.columns[0] if len(df_art.columns) > 0 else "Article Sans Nom"
            if 'Site' not in df_art.columns: df_art['Site'] = 'Abatta'
            if 'Stock_Initial' not in df_art.columns: df_art['Stock_Initial'] = 0
            if 'Stock_Minimum' not in df_art.columns: df_art['Stock_Minimum'] = 5
            if 'Prix_Unitaire_FCFA' not in df_art.columns: df_art['Prix_Unitaire_FCFA'] = 0
            
            df_art['Stock_Initial'] = pd.to_numeric(df_art['Stock_Initial'], errors='coerce').fillna(0)
            df_art['Stock_Minimum'] = pd.to_numeric(df_art['Stock_Minimum'], errors='coerce').fillna(5)
            df_art['Prix_Unitaire_FCFA'] = pd.to_numeric(df_art['Prix_Unitaire_FCFA'], errors='coerce').fillna(0)
            
            # --- FEUILLE 2 : Historique des Flux ---
            try:
                df_mvt = pd.read_excel(nom_fichier, sheet_name=1)
                df_mvt.columns = [str(c).strip() for c in df_mvt.columns]
                mapping_mvt = {
                    'Type': 'Type_Mouvement', 'Mouvement': 'Type_Mouvement', 
                    'Qte': 'Quantite', 'Quantité': 'Quantite', 'Quantite': 'Quantite',
                    'Commentaire': 'Motif', 'Raison': 'Motif'
                }
                df_mvt = df_mvt.rename(columns=mapping_mvt)
                
                # Validation des colonnes de mouvements
                for col in ['Date', 'Code_Article', 'Type_Mouvement', 'Quantite', 'Motif']:
                    if col not in df_mvt.columns: df_mvt[col] = np.nan
                df_mvt = df_mvt.dropna(subset=['Code_Article', 'Type_Mouvement'])
                df_mvt['Quantite'] = pd.to_numeric(df_mvt['Quantite'], errors='coerce').fillna(0)
            except Exception:
                df_mvt = df_mouvements_defaut
                
            return df_art[['Code_Article', 'Designation', 'Site', 'Stock_Initial', 'Stock_Minimum', 'Prix_Unitaire_FCFA']], df_mvt, "✅ Fichier Excel synchronisé (Feuilles 1 & 2)"
            
        except Exception as e:
            return df_articles_defaut, df_mouvements_defaut, f"⚠️ Erreur Excel ({str(e)}). Mode démo activé."
    else:
        return df_articles_defaut, df_mouvements_defaut, "ℹ️ Mode démo actif (Fichier EASYGEST.xlsm introuvable)."

# Initialisation de la session d'état
if 'base_articles' not in st.session_state:
    art_init, mvt_init, msg = charger_donnees_excel()
    st.session_state.base_articles = art_init
    st.session_state.historique_mouvements = mvt_init
    st.session_state.statut_msg = msg

# --- RECALCUL DYNAMIQUE DES STOCKS (Calcul par colonne) ---
def consolider_stocks():
    df_art = st.session_state.base_articles.copy()
    df_mvt = st.session_state.historique_mouvements.copy()
    
    # Groupement des entrées et sorties
    df_e = df_mvt[df_mvt['Type_Mouvement'] == 'Entrée'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Entrees')
    df_s = df_mvt[df_mvt['Type_Mouvement'] == 'Sortie'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Sorties')
    
    # Fusion avec le référentiel article
    df_res = df_art.merge(df_e, on='Code_Article', how='left').merge(df_s, on='Code_Article', how='left')
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    
    # Formule mathématique du stock disponible
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    df_res['Valeur_Stock_FCFA'] = df_res['Quantite_Dispo'] * df_res['Prix_Unitaire_FCFA']
    return df_res

df_global = consolider_stocks()

# 3. Traitement et Segmentation Pareto / ABC (Tri par valeur décroissante)
def appliquer_analyse_abc(df_input):
    if df_input.empty: return df_input
    
    # Tri par valeur au sein de la colonne (Règle métier stricte)
    df_sorted = df_input.sort_values(by='Valeur_Stock_FCFA', ascending=False).reset_index(drop=True)
    total_valeur = df_sorted['Valeur_Stock_FCFA'].sum()
    
    if total_valeur > 0:
        df_sorted['Valeur_Cumulee'] = df_sorted['Valeur_Stock_FCFA'].cumsum()
        df_sorted['Pourcentage_Cumule'] = (df_sorted['Valeur_Cumulee'] / total_valeur) * 100
    else:
        df_sorted['Pourcentage_Cumule'] = 0
        
    df_sorted['Classe_ABC'] = df_sorted['Pourcentage_Cumule'].apply(
        lambda pct: 'Classe A (Critique)' if pct <= 80 else ('Classe B (Intermédiaire)' if pct <= 95 else 'Classe C (Secondaire)')
    )
    return df_sorted

# 4. Barre latérale et filtrage géographique
st.sidebar.title("Easygest v1.2")
st.sidebar.info(st.session_state.statut_msg)

liste_sites = ['Tous les sites'] + sorted(list(df_global['Site'].dropna().unique().astype(str)))
site_selectionne = st.sidebar.selectbox("Filtrer par Site commercial :", liste_sites)

df_filtre = df_global[df_global['Site'] == site_selectionne].copy() if site_selectionne != 'Tous les sites' else df_global.copy()
df_analyse = appliquer_analyse_abc(df_filtre)

# 5. Définition des Vues / Onglets de l'Application
def vue_dashboard():
    st.subheader(f"📊 Tableau de Bord Opérationnel — {site_selectionne}")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Références Articles", f"{len(df_analyse)} produits")
    kpi2.metric("Valeur Financière Globale", f"{df_analyse['Valeur_Stock_FCFA'].sum():,.0f} FCFA")
    
    alertes = df_analyse[df_analyse['Quantite_Dispo'] <= df_analyse['Stock_Minimum']].shape[0]
    kpi3.metric("Alertes Réapprovisionnement", f"{alertes} alertes", delta="-Attention" if alertes > 0 else "OK", delta_color="inverse" if alertes > 0 else "normal")
    
    st.markdown("---")
    st.markdown("### 📈 Analyse Pareto (Tri par valeur de stock décroissante)")
    if not df_analyse.empty and df_analyse['Valeur_Stock_FCFA'].sum() > 0:
        fig = px.bar(df_analyse, x='Designation', y='Valeur_Stock_FCFA', color='Classe_ABC',
                     labels={'Valeur_Stock_FCFA': 'Valeur (FCFA)', 'Designation': 'Article'},
                     color_discrete_map={'Classe A (Critique)': '#EF553B', 'Classe B (Intermédiaire)': '#FECB52', 'Classe C (Secondaire)': '#636EFA'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune valeur financière positive à afficher sur le graphique.")

def vue_mouvements():
    st.subheader("🔄 Flux des Stocks : Saisie des Entrées & Sorties")
    col_form, col_table = st.columns([1, 2])
    
    with col_form:
        st.markdown("#### 📝 Nouveau mouvement")
        with st.form("form_flux", clear_on_submit=True):
            options_dict = {f"{r['Code_Article']} - {r['Designation']} ({r['Site']})": r['Code_Article'] for _, r in st.session_state.base_articles.iterrows()}
            choix_article = st.selectbox("Sélectionner l'article :", list(options_dict.keys()))
            
            type_mvt = st.radio("Nature du flux :", ['Entrée', 'Sortie'])
            quantite = st.number_input("Quantité :", min_value=1, value=1)
            motif = st.text_input("Motif / Référence :", value="Livraison" if type_mvt == 'Entrée' else "Vente")
            
            if st.form_submit_button("Enregistrer le mouvement 💾"):
                code_strict = options_dict[choix_article]
                stock_actuel = df_global[df_global['Code_Article'] == code_strict]['Quantite_Dispo'].values[0]
                
                if type_mvt == 'Sortie' and quantite > stock_actuel:
                    st.error(f"❌ Opération impossible : Stock disponible insuffisant ({stock_actuel} unités).")
                else:
                    nouveau = pd.DataFrame([{
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Code_Article': code_strict, 'Type_Mouvement': type_mvt, 'Quantite': quantite, 'Motif': motif
                    }])
                    st.session_state.historique_mouvements = pd.concat([st.session_state.historique_mouvements, nouveau], ignore_index=True)
                    st.success("Flux ajouté avec succès !")
                    st.rerun()
                    
    with col_table:
        st.markdown("#### ⏳ Journal d'historique (Sheet2 Excel)")
        if st.session_state.historique_mouvements.empty:
            st.info("Le journal de suivi des mouvements est vide.")
        else:
            df_hist = st.session_state.historique_mouvements.merge(st.session_state.base_articles[['Code_Article', 'Designation', 'Site']], on='Code_Article', how='left')
            st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True, hide_index=True)

def vue_stocks():
    st.subheader(f"📦 Registre d'État des Stocks — {site_selectionne}")
    if df_analyse.empty:
        st.warning("Aucun produit à afficher.")
    else:
        # Mise en surbrillance rouge pour les ruptures ou sous-stocks
        st.dataframe(
            df_analyse[['Code_Article', 'Designation', 'Site', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Unitaire_FCFA', 'Valeur_Stock_FCFA', 'Classe_ABC']]
            .style.apply(lambda r: ['background-color: #ffcccc' if r['Quantite_Dispo'] <= r['Stock_Minimum'] else '' for _ in r], axis=1),
            use_container_width=True, hide_index=True
        )

# 6. Routage de la Navigation Multi-pages
pg = st.navigation([
    st.Page(vue_dashboard, title="Tableau de Bord", icon="📊"),
    st.Page(vue_mouvements, title="Entrées / Sorties", icon="🔄"),
    st.Page(vue_stocks, title="État des Stocks", icon="📦")
])
pg.run()
