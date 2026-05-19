import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# 1. Configuration de l'interface du Restaurant
st.set_page_config(
    page_title="Easygest Resto",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Chargement initial de la Carte (Menu) et des Stocks
@st.cache_data
def charger_carte_restaurant():
    nom_fichier = "EASYGEST.xlsm"
    
    df_menu_defaut = pd.DataFrame({
        'Code_Article': ['MENU001', 'MENU002', 'MENU003', 'MENU004', 'MENU005', 'MENU006'],
        'Designation': ['Poulet Braisé Entier', 'Alloco Simple', 'Riz Gras au Gras', 'Bière Ivoirienne 65cl', 'Jus de Bissap Maison', 'Eau Minérale 1.5L'],
        'Categorie': ['Nourriture', 'Nourriture', 'Nourriture', 'Boisson', 'Boisson', 'Boisson'],
        'Stock_Initial': [30, 100, 40, 120, 80, 200],
        'Stock_Minimum': [5, 15, 8, 24, 10, 36],
        'Prix_Vente_FCFA': [7000, 1500, 2500, 1000, 800, 600]
    })
    
    if os.path.exists(nom_fichier):
        try:
            df = pd.read_excel(nom_fichier, sheet_name=0)
            df.columns = [str(c).strip() for c in df.columns]
            
            mapping = {
                'Code': 'Code_Article', 'Article': 'Designation', 'Produit': 'Designation', 'Désignation': 'Designation',
                'Type': 'Categorie', 'Catégorie': 'Categorie',
                'Qte': 'Stock_Initial', 'Stock': 'Stock_Initial', 'Quantité': 'Stock_Initial',
                'Prix': 'Prix_Vente_FCFA', 'PU': 'Prix_Vente_FCFA', 'Prix de Vente': 'Prix_Vente_FCFA',
                'Minimum': 'Stock_Minimum', 'Stock Minimum': 'Stock_Minimum'
            }
            df = df.rename(columns=mapping)
            
            if 'Code_Article' not in df.columns: df['Code_Article'] = [f"MENU{i+1:03d}" for i in range(len(df))]
            if 'Designation' not in df.columns: df['Designation'] = df.columns[0] if len(df.columns) > 0 else "Article"
            if 'Categorie' not in df.columns: df['Categorie'] = 'Nourriture'
            if 'Stock_Initial' not in df.columns: df['Stock_Initial'] = 50
            if 'Stock_Minimum' not in df.columns: df['Stock_Minimum'] = 10
            if 'Prix_Vente_FCFA' not in df.columns: df['Prix_Vente_FCFA'] = 1000
            
            return df[['Code_Article', 'Designation', 'Categorie', 'Stock_Initial', 'Stock_Minimum', 'Prix_Vente_FCFA']]
        except Exception:
            return df_menu_defaut
    return df_menu_defaut

# --- INITIALISATION DE LA MÉMOIRE DE L'APPLICATION ---
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = charger_carte_restaurant()

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.DataFrame(columns=[
        'Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Total_FCFA', 'Statut'
    ])

# --- CALCUL DU STOCK EN TEMPS RÉEL ---
def consolider_stocks_resto():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    
    df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Sorties')
    df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Entrees')
    
    df_res = df_art.merge(df_sorties, on='Code_Article', how='left').merge(df_entrees, on='Code_Article', how='left')
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    df_res['Valeur_Stock_Vente_FCFA'] = df_res['Quantite_Dispo'] * df_res['Prix_Vente_FCFA']
    return df_res

df_global = consolider_stocks_resto()

# --- REGROUPEMENT PARETO ---
def appliquer_analyse_abc(df_input):
    if df_input.empty: return df_input
    df_sorted = df_input.sort_values(by='Valeur_Stock_Vente_FCFA', ascending=False).reset_index(drop=True)
    total_valeur = df_sorted['Valeur_Stock_Vente_FCFA'].sum()
    
    if total_valeur > 0:
        df_sorted['Valeur_Cumulee'] = df_sorted['Valeur_Stock_Vente_FCFA'].cumsum()
        df_sorted['Pourcentage_Cumule'] = (df_sorted['Valeur_Cumulee'] / total_valeur) * 100
    else:
        df_sorted['Pourcentage_Cumule'] = 0
        
    df_sorted['Classe_ABC'] = df_sorted['Pourcentage_Cumule'].apply(
        lambda pct: 'Classe A (Forte Vente)' if pct <= 80 else ('Classe B (Moyen)' if pct <= 95 else 'Classe C (Faible)')
    )
    return df_sorted

# --- BARRE LATÉRALE ---
st.sidebar.title("🍳 Easygest Resto v1.4")
st.sidebar.markdown("**Capacité :** 25 Tables Clients")

# ==========================================
# OPTION 1 : PRISE DE COMMANDE (ÉCRAN SERVEUR)
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande rapide")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.form("form_commande_strict", clear_on_submit=True):
            liste_tables = [f"Table {i}" for i in range(1, 26)]
            table_choisie = st.selectbox("Sélectionner la Table :", liste_tables)
            
            dict_menu = {f"[{r['Categorie']}] {r['Designation']} - {r['Prix_Vente_FCFA']} FCFA": r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()))
            
            quantite = st.number_input("Quantité :", min_value=1, value=1)
            
            if st.form_submit_button("Envoyer la commande 🚀"):
                code_art = dict_menu[item_choisi]
                item_details = df_global[df_global['Code_Article'] == code_art].iloc[0]
                
                if item_details['Categorie'] == 'Boisson' and quantite > item_details['Quantite_Dispo']:
                    st.error(f"❌ Stock insuffisant au bar ! ({int(item_details['Quantite_Dispo'])} dispo)")
                else:
                    px_unitaire = item_details['Prix_Vente_FCFA']
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%H:%M:%S"),
                        'Table': table_choisie,
                        'Code_Article': code_art,
                        'Type_Flux': 'Sortie',
                        'Quantite': quantite,
                        'Total_FCFA': quantite * px_unitaire,
                        'Statut': 'En cours'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    st.success(f"Commande envoyée avec succès pour la {table_choisie} !")
                    st.rerun()
                    
    with col2:
        st.info("💡 **Guide Serveur :** Sélectionnez la table, choisissez l'article et ajustez la quantité. Cliquez sur 'Envoyer la commande' pour qu'elle apparaisse instantanément sur l'écran de caisse.")

# ==========================================
# OPTION 2 : COMMANDES ET ADDITIONS (ÉCRAN CAISSE)
# ==========================================
def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande active ou enregistrée dans la salle actuellement.")
        return

    # Jointure avec les infos du menu pour l'affichage complet
    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Prix_Vente_FCFA']], on='Code_Article', how='left')
    
    # Filtrer uniquement les commandes qui ne sont pas encore payées/clôturées
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Par Table (Calcul d'Addition)", "📋 Journal de toutes les commandes"])
    
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont actuellement libres et payées ! 🎉")
        else:
            tables_occupees = sorted(df_actives['Table'].unique())
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", tables_occupees)
            
            # Filtrer les lignes de cette table
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee]
            
            st.markdown(f"### 🧾 Ticket Provisoire — {table_selectionnee}")
            st.dataframe(df_table_strict[['Heure', 'Designation', 'Quantite', 'Prix_Vente_FCFA', 'Total_FCFA']], use_container_width=True, hide_index=True)
            
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total à Payer : {total_addition:,.0f} FCFA**")
            
            # Actions de caisse
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                # Mettre à jour le statut des lignes de cette table dans la session globale
                indices_table = st.session_state.historique_ventes[st.session_state.historique_ventes['Table'] == table_selectionnee].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                st.success(f"La {table_selectionnee} a été réglée. Table libérée !")
                st.rerun()
                
            if col_btn2.button(f"Annuler les commandes de la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[st.session_state.historique_ventes['Table'] == table_selectionnee].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                st.warning(f"Commandes annulées pour la {table_selectionnee}.")
                st.rerun()

    with tabs_caisse[1]:
        st.markdown("#### Historique global des flux (Servis, Payés, Annulés)")
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# OPTION 3 : STOCKS CUISINE & BAR
# ==========================================
def vue_cuisine_stocks():
    st.subheader("📦 État des Stocks Cuisine & Bar")
    
    alertes_critiques = df_global[df_global['Quantite_Dispo'] <= df_global['Stock_Minimum']].shape[0]
    
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("Valeur marchande potentielle", f"{df_global['Valeur_Stock_Vente_FCFA'].sum():,.0f} FCFA")
    kpi2.metric("Alertes Stocks Critiques", f"{alertes_critiques} alertes", delta="-Réappro!" if alertes_critiques > 0 else "OK", delta_color="inverse")
    
    st.markdown("---")
    
    with st.expander("📥 Enregistrer un Arrivage de Marchandises"):
        with st.form("form_reappro"):
            dict_reappro = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            art_reappro = st.selectbox("Article reçu :", list(dict_reappro.keys()))
            qte_reappro = st.number_input("Quantité :", min_value=1, value=10)
            
            if st.form_submit_button("Ajouter au Stock"):
                code_r = dict_reappro[art_reappro]
                ligne_reappro = pd.DataFrame([{
                    'Heure': datetime.now().strftime("%H:%M:%S"), 'Table': 'LOGISTIQUE', 'Code_Article': code_r,
                    'Type_Flux': 'Réappro', 'Quantite': qte_reappro, 'Total_FCFA': 0, 'Statut': 'Stocké'
                }])
                st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_reappro], ignore_index=True)
                st.success(f"Stock augmenté pour {art_reappro} !")
                st.rerun()

    categories = ['Tout le Menu', 'Nourriture', 'Boisson']
    cat_selectionnee = st.selectbox("Filtrer le tableau des stocks :", categories)
    df_tab_filtre = df_global[df_global['Categorie'] == cat_selectionnee] if cat_selectionnee != 'Tout le Menu' else df_global.copy()
    df_tab_analyse = appliquer_analyse_abc(df_tab_filtre)

    st.dataframe(
        df_tab_analyse[['Code_Article', 'Designation', 'Categorie', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA', 'Valeur_Stock_Vente_FCFA', 'Classe_ABC']]
        .style.apply(lambda r: ['background-color: #ffcccc' if r['Quantite_Dispo'] <= r['Stock_Minimum'] else '' for _ in r], axis=1),
        use_container_width=True, hide_index=True
    )

# ==========================================
# OPTION 4 : ANALYSE PARETO
# ==========================================
def vue_analyse_pareto():
    st.subheader("📊 Analyses Statistiques & Pareto (Chiffre potentiel)")
    if not df_global.empty and df_global['Valeur_Stock_Vente_FCFA'].sum() > 0:
        df_sorted_global = appliquer_analyse_abc(df_global)
        fig = px.bar(
            df_sorted_global, x='Designation', y='Valeur_Stock_Vente_FCFA', color='Classe_ABC',
            labels={'Valeur_Stock_Vente_FCFA': 'Valeur (FCFA)', 'Designation': 'Article'},
            color_discrete_map={'Classe A (Forte Vente)': '#EF553B', 'Classe B (Moyen)': '#FECB52', 'Classe C (Faible)': '#636EFA'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune vente ou stock disponible pour générer les graphiques.")

# 6. Système de Navigation Multi-pages mis à jour
pg = st.navigation([
    st.Page(vue_prise_commande, title="Prise de Commande", icon="📝"),
    st.Page(vue_commandes_additions, title="Commandes & Additions", icon="🧾"),
    st.Page(vue_cuisine_stocks, title="Stocks Cuisine & Bar", icon="📦"),
    st.Page(vue_analyse_pareto, title="Analyse Pareto", icon="📊")
])
pg.run()
