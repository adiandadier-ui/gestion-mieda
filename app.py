import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime

# 1. Configuration de l'interface du Restaurant
st.set_page_config(
    page_title="Easygest Resto Pro",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Chargement initial de la Carte (Menu) et des Stocks
@st.cache_data
def charger_carte_restaurant():
    nom_fichier = "EASYGEST.xlsm"
    
    # Base de données initiale scindée proprement entre Cuisine et Bar
    df_menu_defaut = pd.DataFrame({
        'Code_Article': ['MENU001', 'MENU002', 'MENU003', 'MENU004', 'MENU005', 'MENU006'],
        'Designation': ['Poulet Braisé Entier', 'Alloco Simple', 'Riz Gras au Gras', 'Bière Ivoirienne 65cl', 'Jus de Bissap Maison', 'Eau Minérale 1.5L'],
        'Categorie': ['Cuisine', 'Cuisine', 'Cuisine', 'Bar', 'Bar', 'Bar'],
        'Stock_Initial': [30, 100, 40, 120, 80, 200],
        'Stock_Minimum': [5, 15, 8, 24, 10, 36],
        'Prix_Vente_FCFA': [7000, 1500, 2500, 1000, 800, 600]
    })
    return df_menu_defaut

# --- INITIALISATION DE LA MÉMOIRE DE L'APPLICATION (SESSION STATE) ---
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = charger_carte_restaurant()

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.DataFrame(columns=[
        'Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Total_FCFA', 'Statut', 'Ref_Bon'
    ])

if 'historique_bons' not in st.session_state:
    st.session_state.historique_bons = {}

# --- CALCUL DU STOCK RESTO EN TEMPS RÉEL ---
def consolider_stocks_resto():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    
    # Tri des flux sortants et entrants
    df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Sorties')
    df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Entrees')
    
    df_res = df_art.merge(df_sorties, on='Code_Article', how='left').merge(df_entrees, on='Code_Article', how='left')
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    df_res['Valeur_Stock_Vente_FCFA'] = df_res['Quantite_Dispo'] * df_res['Prix_Vente_FCFA']
    return df_res

df_global = consolider_stocks_resto()

# ==========================================
# VUE 1 : PRISE DE COMMANDE (ÉCRAN SERVEUR)
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.form("form_commande_strict", clear_on_submit=True):
            liste_tables = [f"Table {i}" for i in range(1, 26)]
            table_choisie = st.selectbox("Sélectionner la Table :", liste_tables)
            
            dict_menu = {f"[{r['Categorie']}] {r['Designation']}" : r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()))
            quantite = st.number_input("Quantité :", min_value=1, value=1)
            
            if st.form_submit_button("Envoyer la commande 🚀"):
                code_art = dict_menu[item_choisi]
                item_details = df_global[df_global['Code_Article'] == code_art].iloc[0]
                
                if quantite > item_details['Quantite_Dispo']:
                    st.error(f"❌ Stock insuffisant ! ({int(item_details['Quantite_Dispo'])} disponibles au {item_details['Categorie']})")
                else:
                    px_unitaire = item_details['Prix_Vente_FCFA']
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Table': table_choisie, 'Code_Article': code_art, 'Type_Flux': 'Sortie',
                        'Quantite': quantite, 'Total_FCFA': quantite * px_unitaire, 'Statut': 'En cours', 'Ref_Bon': '-'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    st.success(f"Commande envoyée pour la {table_choisie} !")
                    st.rerun()
                    
    with col2:
        st.info("💡 **Note aux serveurs** : Les produits du Bar et de la Cuisine sont automatiquement déduits de leurs stocks respectifs dès validation.")

# ==========================================
# VUE 2 : COMMANDES ET ADDITIONS (ÉCRAN CAISSE)
# ==========================================
def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande en cours dans la salle.")
        return

    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Prix_Vente_FCFA', 'Categorie']], on='Code_Article', how='left')
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Calcul d'Addition", "📋 Journal des ventes"])
    
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont libérées. 🎉")
        else:
            tables_occupees = sorted(df_actives['Table'].unique())
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", tables_occupees)
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee]
            
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Designation', 'Quantite', 'Prix_Vente_FCFA', 'Total_FCFA']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total à Payer : {total_addition:,.0f} FCFA**")
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                st.success(f"La {table_selectionnee} a été réglée avec succès.")
                st.rerun()
                
            if col_btn2.button(f"Annuler la commande de la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                st.warning(f"Commandes annulées.")
                st.rerun()

    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# VUE 3 : STOCKS & APPROVISIONNEMENTS (CUISINE VS BAR)
# ==========================================
def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Bons d'Entrée")
    
    tab_cuisine, tab_bar, tab_bons = st.tabs(["🍳 Stock CUISINE", "🍹 Stock BAR", "📄 Bons d'Entrée Générés"])
    
    # --- ONGLET CUISINE ---
    with tab_cuisine:
        st.markdown("### Épargne & Ingrédients Cuisine")
        df_cuisine = df_global[df_global['Categorie'] == 'Cuisine']
        st.dataframe(df_cuisine[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Nouvel Achat / Réapprovisionnement Cuisine"):
            with st.form("form_appro_cuisine", clear_on_submit=True):
                dict_cuisine = {r['Designation']: r['Code_Article'] for _, r in df_cuisine.iterrows()}
                art_choisi = st.selectbox("Article Cuisine reçu :", list(dict_cuisine.keys()))
                qte_recue = st.number_input("Quantité achetée :", min_value=1, value=10, key="qte_cui")
                fournisseur = st.text_input("Nom du Fournisseur / Marché :", value="Grossiste Marché")
                
                if st.form_submit_button("Générer le Bon d'Entrée Cuisine 📑"):
                    code_r = dict_cuisine[art_choisi]
                    ref_bon = f"BON-CUI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    # 1. Enregistrement du flux
                    ligne_appro = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': 'APPRO_CUISINE', 'Code_Article': code_r,
                        'Type_Flux': 'Réappro', 'Quantite': qte_recue, 'Total_FCFA': 0, 'Statut': 'Stocké', 'Ref_Bon': ref_bon
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_appro], ignore_index=True)
                    
                    # 2. Structure physique du Bon pour contrôle
                    st.session_state.historique_bons[ref_bon] = {
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Type': 'CUISINE', 'Article': art_choisi, 'Quantite': qte_recue, 'Fournisseur': fournisseur
                    }
                    st.success(f"Bon {ref_bon} créé ! Vérifiez l'onglet des Bons pour impression.")
                    st.rerun()

    # --- ONGLET BAR ---
    with tab_bar:
        st.markdown("### Cave & Boissons Bar")
        df_bar = df_global[df_global['Categorie'] == 'Bar']
        st.dataframe(df_bar[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Nouvel Achat / Réapprovisionnement Bar"):
            with st.form("form_appro_bar", clear_on_submit=True):
                dict_bar = {r['Designation']: r['Code_Article'] for _, r in df_bar.iterrows()}
                art_choisi_bar = st.selectbox("Boisson reçue :", list(dict_bar.keys()))
                qte_recue_bar = st.number_input("Quantité achetée :", min_value=1, value=24, key="qte_bar")
                fournisseur_bar = st.text_input("Nom du Fournisseur / Brasserie :", value="SOLIBRA / Brassivoire")
                
                if st.form_submit_button("Générer le Bon d'Entrée Bar 📑"):
                    code_r = dict_bar[art_choisi_bar]
                    ref_bon = f"BON-BAR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    ligne_appro = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': 'APPRO_BAR', 'Code_Article': code_r,
                        'Type_Flux': 'Réappro', 'Quantite': qte_recue_bar, 'Total_FCFA': 0, 'Statut': 'Stocké', 'Ref_Bon': ref_bon
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_appro], ignore_index=True)
                    
                    st.session_state.historique_bons[ref_bon] = {
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Type': 'BAR', 'Article': art_choisi_bar, 'Quantite': qte_recue_bar, 'Fournisseur': fournisseur_bar
                    }
                    st.success(f"Bon {ref_bon} créé ! Vérifiez l'onglet des Bons pour impression.")
                    st.rerun()

    # --- ONGLET IMPRESSION DES BONS ---
    with tab_bons:
        st.markdown("### 📄 Justificatifs Physiques d'Achats (Bons d'Entrée)")
        if not st.session_state.historique_bons:
            st.info("Aucun bon d'entrée n'a encore été généré.")
        else:
            liste_ref_bons = list(st.session_state.historique_bons.keys())
            bon_selectionne = st.selectbox("Choisir un Bon pour contrôle ou impression :", liste_ref_bons[::-1])
            
            bon_data = st.session_state.historique_bons[bon_selectionne]
            
            # Mise en page du format papier imprimable
            st.markdown("""---""")
            st.markdown(f"""
            <div style="border:2px solid #000; padding:20px; background-color:#fff; color:#000; font-family:monospace;">
                <h2 style="text-align:center; margin-0;">EASYGEST RESTO - BON D'ENTRÉE STOCK</h2>
                <p style="text-align:center;"><b>N° RÉFÉRENCE : {bon_selectionne}</b></p>
                <hr style="border-top: 1px dashed #000;">
                <p><b>Date/Heure :</b> {bon_data['Date']}</p>
                <p><b>Section :</b> STOCK {bon_data['Type']}</p>
                <p><b>Fournisseur :</b> {bon_data['Fournisseur']}</p>
                <hr style="border-top: 1px dashed #000;">
                <table style="width:100%; text-align:left;">
                    <tr><th>Désignation Article</th><th style="text-align:right;">Quantité Reçue</th></tr>
                    <tr><td>{bon_data['Article']}</td><td style="text-align:right;">{bon_data['Quantite']} unités</td></tr>
                </table>
                <br><br><br>
                <div style="display: flex; justify-content: space-between;">
                    <div><b>Signature Livreur :</b><br><br>____________________</div>
                    <div style="text-align:right;"><b>Visa Magasinier / Contrôle :</b><br><br>____________________</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""---""")
            st.caption("💡 Appuyez sur **Ctrl + P** sur votre clavier pour imprimer ce justificatif directement sur votre imprimante thermique ou de bureau.")

# 6. Routage de la Navigation Multi-pages
pg = st.navigation([
    st.Page(vue_prise_commande, title="Prise de Commande", icon="📝"),
    st.Page(vue_commandes_additions, title="Commandes & Additions", icon="🧾"),
    st.Page(vue_stocks_appro, title="Stocks & Approvisionnements", icon="📦")
])
pg.run()
