import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# 1. Configuration de la page
st.set_page_config(
    page_title="Easygest Web App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Fonction de chargement ultra-sécurisée
@st.cache_data
def charger_donnees_excel():
    nom_fichier = "EASYGEST.xlsm"
    
    if os.path.exists(nom_fichier):
        try:
            # Lecture du fichier Excel
            df = pd.read_excel(nom_fichier, sheet_name=0)
            
            # Si le fichier est vide ou mal lu, on nettoie les colonnes de manière sécurisée
            if df.empty or len(df.columns) == 0:
                return generer_donnees_secours(), f"ℹ️ Le fichier '{nom_fichier}' semble vide. Mode démo activé."
            
            # Convertir tous les noms de colonnes en chaînes de caractères propres
            df.columns = [str(c).strip() for c in df.columns]
            
            # Mapping flexible pour renommer vos colonnes existantes
            mapping = {
                'Code': 'Code_Article', 'Article': 'Designation', 'Produit': 'Designation', 'Désignation': 'Designation',
                'Qte': 'Quantite_Dispo', 'Stock': 'Quantite_Dispo', 'Quantité': 'Quantite_Dispo',
                'Prix': 'Prix_Unitaire_FCFA', 'PU': 'Prix_Unitaire_FCFA', 'Prix Unitaire': 'Prix_Unitaire_FCFA',
                'Stock Minimum': 'Stock_Minimum', 'Minimum': 'Stock_Minimum'
            }
            df = df.rename(columns=mapping)
            
            # Vérification et création sécurisée des colonnes manquantes (SANS utiliser d'index numérique)
            if 'Code_Article' not in df.columns: 
                df['Code_Article'] = [f"ART{i+1:03d}" for i in range(len(df))]
                
            if 'Designation' not in df.columns:
                # Si aucune colonne de désignation n'est trouvée, on utilise la toute première colonne existante par son nom direct
                premiere_colonne = list(df.columns)[0]
                df = df.rename(columns={premiere_colonne: 'Designation'})
                
            if 'Site' not in df.columns: 
                df['Site'] = 'Abatta'  # Par défaut si absent
                
            if 'Quantite_Dispo' not in df.columns: df['Quantite_Dispo'] = 0
            if 'Stock_Minimum' not in df.columns: df['Stock_Minimum'] = 5
            if 'Prix_Unitaire_FCFA' not in df.columns: df['Prix_Unitaire_FCFA'] = 0
            
            # Conversion forcée en formats numériques
            df['Quantite_Dispo'] = pd.to_numeric(df['Quantite_Dispo'], errors='coerce').fillna(0)
            df['Stock_Minimum'] = pd.to_numeric(df['Stock_Minimum'], errors='coerce').fillna(5)
            df['Prix_Unitaire_FCFA'] = pd.to_numeric(df['Prix_Unitaire_FCFA'], errors='coerce').fillna(0)
            
            # Calcul de la valeur financière
            df['Valeur_Stock_FCFA'] = df['Quantite_Dispo'] * df['Prix_Unitaire_FCFA']
            return df, f"✅ Données chargées avec succès depuis {nom_fichier}"
            
        except Exception as e:
            return generer_donnees_secours(), f"⚠️ Erreur de traitement Excel : {str(e)}. Mode démo activé."
    else:
        return generer_donnees_secours(), f"ℹ️ Fichier '{nom_fichier}' introuvable. Mode démo activé."

def generer_donnees_secours():
    stocks_data = {
        'Code_Article': ['ART001', 'ART002', 'ART003', 'ART004', 'ART005'],
        'Designation': ['Huile de palme 1L', 'Riz Cassé 50kg', 'Sucre Roux 1kg', 'Lait Concentré', 'Farine de Blé 25kg'],
        'Site': ['Abatta', 'Jules Vernes', 'San-Pedro', 'Abatta', 'San-Pedro'],
        'Quantite_Dispo': [150, 45, 210, 8, 95],
        'Stock_Minimum': [50, 20, 40, 15, 30],
        'Prix_Unitaire_FCFA': [1200, 31000, 850, 650, 14500]
    }
    df = pd.DataFrame(stocks_data)
    df['Valeur_Stock_FCFA'] = df['Quantite_Dispo'] * df['Prix_Unitaire_FCFA']
    return df

# Initialisation de la session d'état Streamlit
if 'df_stocks' not in st.session_state:
    df_init, statut_message = charger_donnees_excel()
    st.session_state.df_stocks = df_init
    st.session_state.statut_msg = statut_message

df_global = st.session_state.df_stocks.copy()

# 3. Tri et Analyse ABC / Pareto (Tri des valeurs par ordre décroissant)
def appliquer_analyse_abc(df_input):
    if df_input.empty:
        return df_input
    
    # Tri impératif par valeur financière décroissante
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

# 4. Barre latérale et filtres de navigation
st.sidebar.title("Easygest v1.0")
st.sidebar.info(st.session_state.statut_msg)

if 'Site' in df_global.columns and not df_global.empty:
    liste_sites = ['Tous les sites'] + sorted(list(df_global['Site'].unique().astype(str)))
else:
    liste_sites = ['Tous les sites']

site_selectionne = st.sidebar.selectbox("Choisir le site commercial :", liste_sites)

if site_selectionne != 'Tous les sites' and 'Site' in df_global.columns:
    df_filtre = df_global[df_global['Site'] == site_selectionne].copy()
else:
    df_filtre = df_global.copy()

df_analyse = appliquer_analyse_abc(df_filtre)

# 5. Définition des Vues (Dashboard et Tableaux)
def vue_dashboard():
    st.subheader(f"📊 Tableau de Bord Analytique — {site_selectionne}")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Références Articles", f"{len(df_analyse)} produits")
    kpi2.metric("Valeur Totale Stock", f"{df_analyse['Valeur_Stock_FCFA'].sum():,.0f} FCFA")
    
    alertes = df_analyse[df_analyse['Quantite_Dispo'] <= df_analyse['Stock_Minimum']].shape[0] if 'Stock_Minimum' in df_analyse.columns else 0
    kpi3.metric("Articles en sous-stock", f"{alertes} alertes", delta="-Attention" if alertes > 0 else "OK", delta_color="inverse" if alertes > 0 else "normal")
    
    st.markdown("---")
    st.markdown("### 📈 Classement Pareto par valeur décroissante")
    
    if not df_analyse.empty and df_analyse['Valeur_Stock_FCFA'].sum() > 0:
        fig = px.bar(
            df_analyse, 
            x='Designation', 
            y='Valeur_Stock_FCFA', 
            color='Classe_ABC',
            labels={'Valeur_Stock_FCFA': 'Valeur (FCFA)', 'Designation': 'Article'},
            color_discrete_map={'Classe A (Critique)': '#EF553B', 'Classe B (Intermédiaire)': '#FECB52', 'Classe C (Secondaire)': '#636EFA'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée financière graphique disponible à afficher pour ce choix.")

def vue_stocks():
    st.subheader(f"📦 Registre des Stocks — {site_selectionne}")
    
    if df_analyse.empty:
        st.warning("Aucune donnée disponible.")
    else:
        def colorer_alertes(row):
            if 'Stock_Minimum' in row and row['Quantite_Dispo'] <= row['Stock_Minimum']:
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)
        
        st.dataframe(
            df_analyse.style.apply(colorer_alertes, axis=1),
            use_container_width=True,
            hide_index=True
        )

# 6. Système de Navigation de l'application
pg = st.navigation([
    st.Page(vue_dashboard, title="Tableau de Bord", icon="📊"),
    st.Page(vue_stocks, title="Gestion des Stocks", icon="📦")
])
pg.run()
