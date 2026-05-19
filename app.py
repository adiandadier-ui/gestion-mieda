import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime
import streamlit.components.v1 as components

# 1. Configuration de l'interface
st.set_page_config(
    page_title="Easygest Resto Pro+",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Chargement de la Carte initiale (uniquement au tout premier démarrage)
@st.cache_data
def charger_carte_restaurant_initiale():
    return pd.DataFrame({
        'Code_Article': ['MENU001', 'MENU002', 'MENU003', 'MENU004', 'MENU005', 'MENU006'],
        'Designation': ['Poulet Braisé Entier', 'Alloco Simple', 'Riz Gras au Gras', 'Bière Ivoirienne 65cl', 'Jus de Bissap Maison', 'Eau Minérale 1.5L'],
        'Categorie': ['Cuisine', 'Cuisine', 'Cuisine', 'Bar', 'Bar', 'Bar'],
        'Stock_Initial': [30, 100, 40, 120, 80, 200],
        'Stock_Minimum': [5, 15, 8, 24, 10, 36],
        'Prix_Vente_FCFA': [7000, 1500, 2500, 1000, 800, 600],
        'Prix_Achat_Moyen_FCFA': [3500, 600, 1000, 650, 300, 250]
    })

# --- ENREGISTREMENT DANS LA SESSION STATE (MÉMOIRE VIVE DE L'APP) ---
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = charger_carte_restaurant_initiale()

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.DataFrame(columns=[
        'Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 
        'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon'
    ])

if 'historique_bons' not in st.session_state:
    st.session_state.historique_bons = {}

# --- RECALCUL ET CONSOLIDATION DYNAMIQUE ---
def consolider_stocks_et_marges():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    
    # Sorties (Ventes validées)
    df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Sorties')
    
    # Entrées (Réapprovisionnements)
    df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Entrees')
    
    # Fusion
    df_res = df_art.merge(df_sorties, on='Code_Article', how='left').merge(df_entrees, on='Code_Article', how='left')
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    
    # Quantité disponible actuelle
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    df_res['Valeur_Stock_Vente_FCFA'] = df_res['Quantite_Dispo'] * df_res['Prix_Vente_FCFA']
    
    return df_res

df_global = consolider_stocks_et_marges()

# ==========================================
# VUE 1 : PRISE DE COMMANDE SANS LE PORTIONNAGE
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide & Options")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        dict_menu = {}
        dict_categories = {} 
        for _, r in st.session_state.base_menu.iterrows():
            label = f"[{r['Categorie']}] {r['Designation']} ({int(r['Prix_Vente_FCFA'])} FCFA)"
            dict_menu[label] = r['Code_Article']
            dict_categories[label] = r['Categorie']

        with st.form("form_commande_strict", clear_on_submit=True):
            liste_tables = [f"Table {i}" for i in range(1, 26)]
            table_choisie = st.selectbox("Sélectionner la Table :", liste_tables)
            
            item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()))
            
            # Détection de la catégorie
            categorie_active = dict_categories[item_choisi] if item_choisi else "Cuisine"
            
            # --- ACCOMPAGNEMENT GRATUIT UNIQUEMENT (SANS PORTION) ---
            accomp_choisi = "-"
            if categorie_active == "Cuisine":
                st.markdown("👇 *Options Spécifiques Cuisine*")
                accomp_choisi = st.selectbox(
                    "Choisir l'accompagnement gratuit :", 
                    ["Alloco", "Attiéké", "Frites de Pomme de terre", "Riz Blanc", "Riz Gras", "Sans accompagnement"]
                )
                st.markdown("---")
            
            quantite = st.number_input("Quantité de plats principaux :", min_value=1, value=1)
            
            st.markdown("##### 🎁 Option de Remise (Optionnel)")
            opt_remise = st.selectbox("Taux de remise à appliquer :", [0, 5, 10, 15, 20, "Autre (Saisie manuelle)"])
            
            if opt_remise == "Autre (Saisie manuelle)":
                taux_remise = st.number_input("Entrez le taux de remise (%) :", min_value=0, max_value=100, value=0)
            else:
                taux_remise = int(opt_remise)
                
            motif_remise = "Aucun"
            if taux_remise > 0:
                motif_remise = st.selectbox("Motif / Profil bénéficiaire :", ["Client Fidèle ⭐", "Ami Spécial 🤝", "Geste Commercial 🛠️"])
            
            if st.form_submit_button("Envoyer la commande 🚀"):
                code_art = dict_menu[item_choisi]
                item_details = df_global[df_global['Code_Article'] == code_art].iloc[0]
                
                if quantite > item_details['Quantite_Dispo']:
                    st.error(f"❌ Stock insuffisant ! ({int(item_details['Quantite_Dispo'])} disponibles au stock {item_details['Categorie']})")
                else:
                    px_vente_unitaire = item_details['Prix_Vente_FCFA']
                    total_brut = quantite * px_vente_unitaire
                    total_net_remise = total_brut * (1 - (taux_remise / 100))
                    
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Table': table_choisie, 'Code_Article': code_art, 'Type_Flux': 'Sortie',
                        'Quantite': quantite, 'Prix_Unitaire_Flux': px_vente_unitaire, 
                        'Remise_Pourcent': taux_remise, 'Accompagnement': accomp_choisi, 
                        'Total_FCFA': total_net_remise, 'Motif_Remise': motif_remise, 
                        'Statut': 'En cours', 'Ref_Bon': '-'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    st.success(f"Commande envoyée en cuisine pour la {table_choisie} !")
                    st.rerun()
                    
    with col2:
        st.info(f"""
        💡 **Prise de commande simplifiée :**
        - Le volet de portionnement a été retiré pour accélérer la saisie.
        - Le choix de l'accompagnement gratuit reste disponible pour guider la préparation en cuisine.
        """)

# ==========================================
# VUE 2 : COMMANDES ET ADDITIONS (ÉCRAN CAISSE)
# ==========================================
def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande en cours dans la salle.")
        return

    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Categorie']], on='Code_Article', how='left')
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Calcul d'Addition", "📋 Journal des Flux & Remises"])
    
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont libérées et encaissées. 🎉")
        else:
            tables_occupees = sorted(df_actives['Table'].unique())
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", tables_occupees)
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee].copy()
            
            # Affichage combiné : Nom du plat + Accompagnement
            def formater_libelle(row):
                if row['Accompagnement'] != "-" and row['Accompagnement'] != "Sans accompagnement":
                    return f"{row['Designation']} (Acc: {row['Accompagnement']})"
                return row['Designation']
                
            df_table_strict['Désignation Produit'] = df_table_strict.apply(formater_libelle, axis=1)
            
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Désignation Produit', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Total_FCFA', 'Motif_Remise']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                st.success(f"La {table_selectionnee} a été réglée.")
                st.rerun()
                
            if col_btn2.button(f"Annuler la commande de la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                st.warning(f"Commandes annulées.")
                st.rerun()

    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# VUE 3 : STOCKS & BONS D'ENTREE
# ==========================================
def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Bons d'Entrée")
    tab_cuisine, tab_bar, tab_bons = st.tabs(["🍳 Stock CUISINE", "🍹 Stock BAR", "📄 Bons d'Entrée Valorisés"])
    
    with tab_cuisine:
        df_cuisine = df_global[df_global['Categorie'] == 'Cuisine']
        st.dataframe(df_cuisine[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Cuisine"):
            with st.form("form_appro_cuisine", clear_on_submit=True):
                dict_cuisine = {r['Designation']: r['Code_Article'] for _, r in df_cuisine.iterrows()}
                art_choisi = st.selectbox("Article Cuisine reçu :", list(dict_cuisine.keys()))
                qte_recue = st.number_input("Quantité achetée :", min_value=1, value=10)
                px_achat_unit = st.number_input("Prix d'Achat UNITAIRE (FCFA) :", min_value=0, value=1000, step=50)
                fournisseur = st.text_input("Nom du Fournisseur :", value="Grossiste Marché")
                
                if st.form_submit_button("Générer le Bon d'Entrée Cuisine 📑"):
                    code_r = dict_cuisine[art_choisi]
                    ref_bon = f"BON-CUI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    ligne_appro = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': 'APPRO_CUISINE', 'Code_Article': code_r,
                        'Type_Flux': 'Réappro', 'Quantite': qte_recue, 'Prix_Unitaire_Flux': px_achat_unit,
                        'Remise_Pourcent': 0, 'Accompagnement': '-', 
                        'Total_FCFA': qte_recue * px_achat_unit, 'Motif_Remise': 'Aucun', 'Statut': 'Stocké', 'Ref_Bon': ref_bon
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_appro], ignore_index=True)
                    
                    idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_r].index
                    st.session_state.base_menu.loc[idx, 'Prix_Achat_Moyen_FCFA'] = px_achat_unit
                    
                    st.session_state.historique_bons[ref_bon] = {
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Type': 'CUISINE', 'Article': art_choisi,
                        'Quantite': qte_recue, 'Prix_Unitaire': px_achat_unit, 'Total': qte_recue * px_achat_unit, 'Fournisseur': fournisseur
                    }
                    st.success(f"Bon {ref_bon} créé avec succès !")
                    st.rerun()

    with tab_bar:
        df_bar = df_global[df_global['Categorie'] == 'Bar']
        st.dataframe(df_bar[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Bar"):
            with st.form("form_appro_bar", clear_on_submit=True):
                dict_bar = {r['Designation']: r['Code_Article'] for _, r in df_bar.iterrows()}
                art_choisi_bar = st.selectbox("Boisson reçue :", list(dict_bar.keys()))
                qte_recue_bar = st.number_input("Quantité achetée :", min_value=1, value=24)
                px_achat_unit_bar = st.number_input("Prix d'Achat UNITAIRE (FCFA) :", min_value=0, value=500, step=50)
                fournisseur_bar = st.text_input("Nom du Fournisseur :", value="SOLIBRA")
                
                if st.form_submit_button("Générer le Bon d'Entrée Bar 📑"):
                    code_r = dict_bar[art_choisi_bar]
                    ref_bon = f"BON-BAR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    ligne_appro = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': 'APPRO_BAR', 'Code_Article': code_r,
                        'Type_Flux': 'Réappro', 'Quantite': qte_recue_bar, 'Prix_Unitaire_Flux': px_achat_unit_bar,
                        'Remise_Pourcent': 0, 'Accompagnement': '-', 
                        'Total_FCFA': qte_recue_bar * px_achat_unit_bar, 'Motif_Remise': 'Aucun', 'Statut': 'Stocké', 'Ref_Bon': ref_bon
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_appro], ignore_index=True)
                    
                    idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_r].index
                    st.session_state.base_menu.loc[idx, 'Prix_Achat_Moyen_FCFA'] = px_achat_unit_bar
                    
                    st.session_state.historique_bons[ref_bon] = {
                        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Type': 'BAR', 'Article': art_choisi_bar,
                        'Quantite': qte_recue_bar, 'Prix_Unitaire': px_achat_unit_bar, 'Total': qte_recue_bar * px_achat_unit_bar, 'Fournisseur': fournisseur_bar
                    }
                    st.success(f"Bon {ref_bon} créé avec succès !")
                    st.rerun()

    with tab_bons:
        if not st.session_state.historique_bons:
            st.info("Aucun bon d'entrée valorisé généré.")
        else:
            bon_selectionne = st.selectbox("Choisir un Bon pour contrôle physique :", list(st.session_state.historique_bons.keys())[::-1])
            b = st.session_state.historique_bons[bon_selectionne]
            
            code_html_bon = f"""
            <div id="print-area" style="border:2px solid #000; padding:20px; background-color:#fff; color:#000; font-family:monospace; max-width:600px; margin:auto;">
                <h2 style="text-align:center; margin:0;">EASYGEST RESTO - BON D'ENTRÉE VALORISÉ</h2>
                <p style="text-align:center;"><b>N° BON : {bon_selectionne}</b></p>
                <hr style="border-top: 1px dashed #000;">
                <p><b>Date :</b> {b['Date']} | <b>Section :</b> {b['Type']}</p>
                <p><b>Fournisseur :</b> {b['Fournisseur']}</p>
                <hr style="border-top: 1px dashed #000;">
                <table style="width:100%; text-align:left; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px dashed #000;">
                            <th>Désignation</th>
                            <th>Qté</th>
                            <th>P.U Achat</th>
                            <th style="text-align:right;">Total Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{b['Article']}</td>
                            <td>{b['Quantite']}</td>
                            <td>{b['Prix_Unitaire']:,} F</td>
                            <td style="text-align:right;">{b['Total']:,} FCFA</td>
                        </tr>
                    </tbody>
                </table>
                <hr style="border-top: 1px dashed #000;">
                <h4 style="text-align:right; margin-top:10px;">MONTANT TOTAL ACHAT : {b['Total']:,} FCFA</h4>
                <br><br>
                <div style="display: flex; justify-content: space-between;">
                    <div><b>Signature Livreur :</b><br><br>___________________</div>
                    <div style="text-align:right;"><b>Visa Caisse / Contrôle :</b><br><br>___________________</div>
                </div>
            </div>
            """
            st.markdown(code_html_bon, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🖨 Imprimer ce Bon d'Entrée", type="primary", use_container_width=True):
                js_script = f"""
                <script>
                    var printWindow = window.open('', '_blank', 'height=600,width=800');
                    printWindow.document.write('<html><head><title>Impression Bon d-Entree</title>');
                    printWindow.document.write('</head><body>');
                    printWindow.document.write(`{code_html_bon}`);
                    printWindow.document.write('</body></html>');
                    printWindow.document.close();
                    printWindow.focus();
                    setTimeout(function() {{ printWindow.print(); printWindow.close(); }}, 500);
                </script>
                """
                components.html(js_script, height=0, width=0)
                st.success("Ordre d'impression envoyé !")

# ==========================================
# VUE 4 : FINANCES AVEC IMPACT DES REMISES
# ==========================================
def vue_finances_marges():
    st.subheader("📊 Compte d'Exploitation & Marges Réelles")
    df_ventes_payees = st.session_state.historique_ventes[(st.session_state.historique_ventes['Type_Flux'] == 'Sortie') & (st.session_state.historique_ventes['Statut'] == 'Payé')]
    
    if df_ventes_payees.empty:
        st.info("Aucun encaissement validé pour le moment.")
        return
        
    df_calc_marge = df_ventes_payees.groupby('Code_Article').agg({'Quantite': 'sum', 'Total_FCFA': 'sum'}).reset_index()
    df_calc_marge = df_calc_marge.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Prix_Achat_Moyen_FCFA']], on='Code_Article', how='left')
    
    df_calc_marge['Cout_Total_Achat'] = df_calc_marge['Quantite'] * df_calc_marge['Prix_Achat_Moyen_FCFA']
    df_calc_marge['Marge_Brute_FCFA'] = df_calc_marge['Total_FCFA'] - df_calc_marge['Cout_Total_Achat']
    df_calc_marge['Taux_Marge_%'] = (df_calc_marge['Marge_Brute_FCFA'] / df_calc_marge['Total_FCFA']) * 100
    
    ca_total = df_calc_marge['Total_FCFA'].sum()
    cout_achats_total = df_calc_marge['Cout_Total_Achat'].sum()
    marge_globale = df_calc_marge['Marge_Brute_FCFA'].sum()
    taux_marge_global = (marge_globale / ca_total) * 100 if ca_total > 0 else 0
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Chiffre d'Affaires Net encaissé", f"{ca_total:,.0f} FCFA")
    f2.metric("Coût des Matières (Achats)", f"{cout_achats_total:,.0f} FCFA", delta="-Dépenses", delta_color="inverse")
    f3.metric("Marge Réelle d'Exploitation", f"{marge_globale:,.0f} FCFA", delta=f"{taux_marge_global:.1f}% de marge")
    
    st.markdown("---")
    st.markdown("### 📋 Analyse détaillée des ventes et options d'accompagnements")
    st.dataframe(df_ventes_payees.merge(st.session_state.base_menu[['Code_Article', 'Designation']], on='Code_Article')[['Heure', 'Table', 'Designation', 'Quantite', 'Accompagnement', 'Remise_Pourcent', 'Motif_Remise', 'Total_FCFA']], use_container_width=True, hide_index=True)

# ==========================================
# VUE 5 : CONFIGURATION DE LA CARTE
# ==========================================
def vue_configuration_carte():
    st.subheader("⚙️ Configuration Technique de la Carte & Menu")
    action = st.radio("Sélectionnez l'action de gestion de la carte :", ["➕ Ajouter un Nouveau Produit", "✏️ Modifier un Produit Existant", "❌ Supprimer un Produit Inutilisé"])
    st.markdown("---")
    
    if action == "➕ Ajouter un Nouveau Produit":
        with st.form("form_ajout_produit", clear_on_submit=True):
            new_designation = st.text_input("Désignation / Nom du plat ou de la boisson :")
            new_categorie = st.selectbox("Famille d'article :", ["Cuisine", "Bar"])
            c1, c2, c3 = st.columns(3)
            new_stock_init = c1.number_input("Stock Initial de départ :", min_value=0, value=10)
            new_stock_min = c2.number_input("Seuil d'Alerte Stock Minimum :", min_value=1, value=5)
            new_prix_vente = c3.number_input("Prix de Vente Client (FCFA) :", min_value=0, value=1500, step=100)
            new_prix_achat = st.number_input("Prix d'Achat Estimé initial (FCFA) :", min_value=0, value=700, step=50)
            
            if st.form_submit_button("Enregistrer le nouveau produit à la carte 💾"):
                if not new_designation:
                    st.error("Le nom du produit ne peut pas être vide.")
                else:
                    prochain_id = len(st.session_state.base_menu) + 1
                    new_code = f"MENU{prochain_id:03d}"
                    nouvel_article = pd.DataFrame([{
                        'Code_Article': new_code, 'Designation': new_designation, 'Categorie': new_categorie,
                        'Stock_Initial': new_stock_init, 'Stock_Minimum': new_stock_min, 
                        'Prix_Vente_FCFA': new_prix_vente, 'Prix_Achat_Moyen_FCFA': new_prix_achat
                    }])
                    st.session_state.base_menu = pd.concat([st.session_state.base_menu, nouvel_article], ignore_index=True)
                    st.success(f"Article '{new_designation}' ajouté avec succès under {new_code} !")
                    st.rerun()

    elif action == "✏️ Modifier un Produit Existant":
        dict_edit = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
        produit_a_modifier = st.selectbox("Sélectionner le produit à réajuster :", list(dict_edit.keys()))
        code_strict = dict_edit[produit_a_modifier]
        infos_actuelles = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_strict].iloc[0]
        
        with st.form("form_edit_produit"):
            edit_designation = st.text_input("Modifier le nom de l'article :", value=infos_actuelles['Designation'])
            edit_categorie = st.selectbox("Modifier la Famille :", ["Cuisine", "Bar"], index=0 if infos_actuelles['Categorie'] == 'Cuisine' else 1)
            col1, col2 = st.columns(2)
            edit_prix_vente = col1.number_input("Nouveau Prix de Vente (FCFA) :", min_value=0, value=int(infos_actuelles['Prix_Vente_FCFA']), step=100)
            edit_stock_min = col2.number_input("Nouveau Stock Minimum d'Alerte :", min_value=1, value=int(infos_actuelles['Stock_Minimum']))
            
            if st.form_submit_button("Enregistrer les modifications ⚡"):
                idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_strict].index
                st.session_state.base_menu.loc[idx, 'Designation'] = edit_designation
                st.session_state.base_menu.loc[idx, 'Categorie'] = edit_categorie
                st.session_state.base_menu.loc[idx, 'Prix_Vente_FCFA'] = edit_prix_vente
                st.session_state.base_menu.loc[idx, 'Stock_Minimum'] = edit_stock_min
                st.success(f"Mise à jour effectuée !")
                st.rerun()

    elif action == "❌ Supprimer un Produit Inutilisé":
        if not st.session_state.historique_ventes.empty:
            codes_utilises = set(st.session_state.historique_ventes[st.session_state.historique_ventes['Type_Flux'] == 'Sortie']['Code_Article'].unique())
        else:
            codes_utilises = set()
            
        options_suppression = {}
        for _, r in st.session_state.base_menu.iterrows():
            deja_vendu = r['Code_Article'] in codes_utilises
            label = f"{r['Designation']} ({r['Categorie']}) — {'🔒 Vendu (Bloqué)' if deja_vendu else '🔓 Jamais vendu (Supprimable)'}"
            options_suppression[label] = {'code': r['Code_Article'], 'bloque': deja_vendu, 'nom': r['Designation']}
            
        choix_label = st.selectbox("Choisir l'article à supprimer :", list(options_suppression.keys()))
        info_choix = options_suppression[choix_label]
        
        if info_choix['bloque']:
            st.error(f"❌ Impossible de supprimer '{info_choix['nom']}'.")
        else:
            with st.form("form_suppression_strict"):
                if st.form_submit_button("Confirmer la suppression définitive 🗑️", type="primary"):
                    st.session_state.base_menu = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] != info_choix['code']].reset_index(drop=True)
                    st.success(f"Article supprimé.")
                    st.rerun()

# 6. Système de Navigation Multi-pages
pg = st.navigation([
    st.Page(vue_prise_commande, title="Prise de Commande", icon="📝"),
    st.Page(vue_commandes_additions, title="Commandes & Additions", icon="🧾"),
    st.Page(vue_stocks_appro, title="Stocks & Approvisionnements", icon="📦"),
    st.Page(vue_finances_marges, title="Finances & Marges", icon="📊"),
    st.Page(vue_configuration_carte, title="Configuration Carte", icon="⚙️")
])
pg.run()
