import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# 1. Configuration de la page
st.set_page_config(
    page_title="Easygest Web App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Chargement initial sécurisé de la base articles
@st.cache_data
def charger_base_excel():
    nom_fichier = "EASYGEST.xlsm"
    if os.path.exists(nom_fichier):
        try:
            df = pd.read_excel(nom_fichier, sheet_name=0)
            df.columns = [str(c).strip() for c in df.columns]
            
            mapping = {
                'Code': 'Code_Article', 'Article': 'Designation', 'Produit': 'Designation', 'Désignation': 'Designation',
                'Qte': 'Stock_Initial', 'Stock': 'Stock_Initial', 'Quantité': 'Stock_Initial', 'Quantite': 'Stock_Initial',
                'Prix': 'Prix_Unitaire_FCFA', 'PU': 'Prix_Unitaire_FCFA', 'Prix Unitaire': 'Prix_Unitaire_FCFA',
                'Stock Minimum': 'Stock_Minimum', 'Minimum': 'Stock_Minimum', 'Site': 'Site', 'Secteur': 'Site'
            }
            df = df.rename(columns=mapping)
            
            if 'Code_Article' not in df.columns: df['Code_Article'] = [f"ART{i+1:03d}" for i in range(len(df))]
            if 'Designation' not in df.columns: df['Designation'] = df.columns[0] if len(df.columns) > 0 else "Article Sans Nom"
            if 'Site' not in df.columns: df['Site'] = 'Abatta'
            if 'Stock_Initial' not in df.columns: df['Stock_Initial'] = 0
            if 'Stock_Minimum' not in df.columns: df['Stock_Minimum'] = 5
            if 'Prix_Unitaire_FCFA' not in df.columns: df['Prix_Unitaire_FCFA'] = 1000
            
            df['Stock_Initial'] = pd.to_numeric(df['Stock_Initial'], errors='coerce').fillna(0)
            df['Stock_Minimum'] = pd.to_numeric(df['Stock_Minimum'], errors='coerce').fillna(5)
            df['Prix_Unitaire_FCFA'] = pd.to_numeric(df['Prix_Unitaire_FCFA'], errors='coerce').fillna(0)
            
            return df[['Code_Article', 'Designation', 'Site', 'Stock_Initial', 'Stock_Minimum', 'Prix_Unitaire_FCFA']]
        except Exception:
            return generer_base_secours()
    else:
        return generer_base_secours()

def generer_base_secours():
    return pd.DataFrame({
        'Code_Article': ['ART001', 'ART002', 'ART003', 'ART004'],
        'Designation': ['Huile de palme 1L', 'Riz Cassé 50kg', 'Sucre Roux 1kg', 'Lait Concentré'],
        'Site': ['Abatta', 'Jules Vernes', 'San-Pedro', 'Abatta'],
        'Stock_Initial': [100, 50, 200, 30],
        'Stock_Minimum': [20, 10, 30, 15],
        'Prix_Unitaire_FCFA': [1200, 31000, 850, 650]
    })

# --- INITIALISATION DES VARIABLES DE SESSION (MÉMOIRE DE L'APP) ---
if 'base_articles' not in st.session_state:
    st.session_state.base_articles = charger_base_excel()

if 'historique_mouvements' not in st.session_state:
    # Création d'un historique de mouvements vide par défaut
    st.session_state.historique_mouvements = pd.DataFrame(columns=[
        'Date', 'Code_Article', 'Type_Mouvement', 'Quantite', 'Motif'
    ])

# --- CALCUL DYNAMIQUE DU STOCK DISPONIBLE ---
def recalculer_stocks_globaux():
    df_art = st.session_state.base_articles.copy()
    df_mvt = st.session_state.historique_mouvements.copy()
    
    # Calcul du total des entrées par produit
    df_entrees = df_mvt[df_mvt['Type_Mouvement'] == 'Entrée'].groupby('Code_Article')['Quantite'].sum().reset_index()
    df_entrees.columns = ['Code_Article', 'Total_Entrees']
    
    # Calcul du total des sorties par produit
    df_sorties = df_mvt[df_mvt['Type_Mouvement'] == 'Sortie'].groupby('Code_Article')['Quantite'].sum().reset_index()
    df_sorties.columns = ['Code_Article', 'Total_Sorties']
    
    # Fusion des calculs avec la base article
    df_final = df_art.merge(df_entrees, on='Code_Article', how='left').merge(df_sorties, on='Code_Article', how='left')
    df_final['Total_Entrees'] = df_final['Total_Entrees'].fillna(0)
    df_final['Total_Sorties'] = df_final['Total_Sorties'].fillna(0)
    
    # Calcul de la quantité disponible finale
    df_final['Quantite_Dispo'] = df_final['Stock_Initial'] + df_final['Total_Entrees'] - df_final['Total_Sorties']
    df_final['Valeur_Stock_FCFA'] = df_final['Quantite_Dispo'] * df_final['Prix_Unitaire_FCFA']
    
    return df_final

df_global = recalculer_stocks_globaux()

# 3. Traitement Analyse ABC / Pareto (Tri des valeurs par ordre décroissant)
def appliquer_analyse_abc(df_input):
    if df_input.empty: return df_input
    df_sorted = df_input.sort_values(by='Valeur_Stock_FCFA', ascending=False).reset_index(drop=True)
    total_valeur = df_sorted['Valeur_Stock_FCFA'].sum()
    
    if total_valeur > 0:
        df_sorted['Valeur_Cumulee'] = df_sorted['Valeur_Stock_FCFA'].cumsum()
        df_sorted['Pourcentage_Cumule'] = (df_sorted['Valeur_Cumulee'] / total_valeur) * 100
    else:
        df_sorted['Pourcentage_Cumule'] = 0
        
    def segmenter(pct):
        if pct <= 80: return 'Classe A (Critique)'
        elif pct <= 95: return 'Classe B (Intermédiaire)'
        else: return 'Classe C (Secondaire)'
        
    df_sorted['Classe_ABC'] = df_sorted['Pourcentage_Cumule'].apply(segmenter)
    return df_sorted

# 4. Configuration de la Barre Latérale
st.sidebar.title("Easygest v1.1")
liste_sites = ['Tous les sites'] + sorted(list(df_global['Site'].dropna().unique().astype(str)))
site_selectionne = st.sidebar.selectbox("Filtrer par Site commercial :", liste_sites)

if site_selectionne != 'Tous les sites':
    df_filtre = df_global[df_global['Site'] == site_selectionne].copy()
else:
    df_filtre = df_global.copy()

df_analyse = appliquer_analyse_abc(df_filtre)

# 5. Définition des Vues / Pages
def vue_dashboard():
    st.subheader(f"📊 Tableau de Bord Général — {site_selectionne}")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Références Produits", f"{len(df_analyse)} articles")
    kpi2.metric("Valeur Financière Stock", f"{df_analyse['Valeur_Stock_FCFA'].sum():,.0f} FCFA")
    
    alertes = df_analyse[df_analyse['Quantite_Dispo'] <= df_analyse['Stock_Minimum']].shape[0]
    kpi3.metric("Alertes Réapprovisionnement", f"{alertes} alertes", delta="-Attention" if alertes > 0 else "OK", delta_color="inverse" if alertes > 0 else "normal")
    
    st.markdown("---")
    st.markdown("### 📈 Analyse Pareto des valeurs de stock (Ordre décroissant)")
    if not df_analyse.empty and df_analyse['Valeur_Stock_FCFA'].sum() > 0:
        fig = px.bar(df_analyse, x='Designation', y='Valeur_Stock_FCFA', color='Classe_ABC',
                     labels={'Valeur_Stock_FCFA': 'Valeur (FCFA)', 'Designation': 'Article'},
                     color_discrete_map={'Classe A (Critique)': '#EF553B', 'Classe B (Intermédiaire)': '#FECB52', 'Classe C (Secondaire)': '#636EFA'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun graphique à afficher (valeur des stocks à 0).")

def vue_mouvements():
    st.subheader("🔄 Gestion des Entrées & Sorties de Stock")
    
    col_form, col_Filtre_site = st.columns([1, 2])
    
    with col_form:
        st.markdown("#### 📝 Enregistrer un flux")
        with st.form("form_mouvement", clear_on_submit=True):
            # Sélection de l'article basé sur la liste disponible
            options_articles = {f"{row['Code_Article']} - {row['Designation']} ({row['Site']})": row['Code_Article'] for _, row in st.session_state.base_articles.iterrows()}
            article_choisi = st.selectbox("Sélectionner l'article :", options_list:=list(options_articles.keys()))
            
            type_mvt = st.radio("Nature du mouvement :", ['Entrée', 'Sortie'])
            quantite_mvt = st.number_input("Quantité concernée :", min_value=1, value=1)
            motif_mvt = st.text_input("Motif / Commentaire :", value="Livraison fournisseur" if type_mvt=='Entrée' else "Vente client")
            
            soumis = st.form_submit_button("Valider le mouvement 💾")
            
            if soumis:
                code_art_strict = options_articles[article_choisi]
                
                # Vérification de sécurité pour éviter les stocks négatifs lors d'une sortie
                stock_actuel = df_global[df_global['Code_Article'] == code_art_strict]['Quantite_Dispo'].values[0]
                if type_mvt == 'Sortie' and quantite_mvt > stock_actuel:
                    st.error(f"❌ Action refusée : Stock insuffisant ({stock_actuel} dispo) pour valider cette sortie de {quantite_mvt} unités.")
                else:
                    # Enregistrement du mouvement dans le DataFrame historique
                    nouveau_mvt = pd.DataFrame([{
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Code_Article': code_art_strict,
                        'Type_Mouvement': type_mvt,
                        'Quantite': quantite_mvt,
                        'Motif': motif_mvt
                    }])
                    st.session_state.historique_mouvements = pd.concat([st.session_state.historique_mouvements, nouveau_mvt], ignore_index=True)
                    st.success(f"✔️ {type_mvt} de {quantite_mvt} unités enregistrée avec succès !")
                    st.rerun()

    with col_Filtre_site:
        st.markdown("#### ⏳ Historique des derniers mouvements enregistrés")
        if st.session_state.historique_mouvements.empty:
            st.info("Aucun mouvement enregistré pour le moment.")
        else:
            # Jointure pour afficher la désignation de l'article plutôt que juste son code
            df_historique_affiche = st.session_state.historique_mouvements.merge(
                st.session_state.base_articles[['Code_Article', 'Designation', 'Site']], on='Code_Article', how='left'
            )
            # Tri pour voir le plus récent en premier
            df_historique_affiche = df_historique_affiche.sort_index(ascending=False)
            
            st.dataframe(
                df_historique_affiche[['Date', 'Site', 'Code_Article', 'Designation', 'Type_Mouvement', 'Quantite', 'Motif']],
                use_container_width=True, hide_index=True
            )

def vue_stocks():
    st.subheader(f"📦 Registre Récapitulatif des Stocks — {site_selectionne}")
    
    if df_analyse.empty:
        st.warning("Aucune donnée disponible.")
    else:
        # Alerte visuelle rouge clair si le stock disponible descend sous le niveau minimum
        def colorer_alertes(row):
            return ['background-color: #ffcccc' if row['Quantite_Dispo'] <= row['Stock_Minimum'] else '' for _ in row]
        
        st.dataframe(
            df_analyse[['Code_Article', 'Designation', 'Site', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Unitaire_FCFA', 'Valeur_Stock_FCFA', 'Classe_ABC']].style.apply(colorer_alertes, axis=1),
            use_container_width=True,
            hide_index=True
        )

# 6. Système de Routage
pg = st.navigation([
    st.Page(vue_dashboard, title="Tableau de Bord", icon="📊"),
    st.Page(vue_mouvements, title="Entrées / Sorties", icon="🔄"),
    st.Page(vue_stocks, title="État des Stocks", icon="📦")
])
pg.run()
