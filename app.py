import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
# 1. CONFIGURATION DE L'INTERFACE
# ==========================================
st.set_page_config(
    page_title="Easygest Resto Pro+",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. INITIALISATION ET STOCKAGE LOCAL (C:)
# ==========================================
def initialiser_dossier_easygest():
    """
    Vérifie l'existence du dossier 'EASYGEST APPS' sur le disque C:
    et le crée s'il n'existe pas.
    """
    chemin_cible = r"C:\EASYGEST APPS"
    
    if not os.path.exists(chemin_cible):
        try:
            os.makedirs(chemin_cible)
        except Exception as e:
            chemin_cible = os.path.join(os.getcwd(), "EASYGEST_APPS_LOCAL")
            if not os.path.exists(chemin_cible):
                os.makedirs(chemin_cible)
            
    dossier_backup = os.path.join(chemin_cible, "backups")
    if not os.path.exists(dossier_backup):
        os.makedirs(dossier_backup)
    
    return chemin_cible

DOSSIER_EXPLOITATION = initialiser_dossier_easygest()
DOSSIER_BACKUPS = os.path.join(DOSSIER_EXPLOITATION, "backups")

CSV_MENU = os.path.join(DOSSIER_EXPLOITATION, "easygest_base_menu.csv")
CSV_VENTES = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_ventes.csv")
CSV_BONS = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_bons.csv")
CSV_Z_HISTORIQUE = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_z.csv")
CSV_UTILISATEURS = os.path.join(DOSSIER_EXPLOITATION, "easygest_utilisateurs.csv")

def initialiser_fichiers_csv():
    if not os.path.exists(CSV_MENU):
        df_init_menu = pd.DataFrame({
            'Code_Article': ['MENU001'],
            'Designation': ['Exemple (À supprimer après avoir créé vos produits)'],
            'Categorie': ['Cuisine'],
            'Stock_Initial': [0],
            'Stock_Minimum': [5],
            'Prix_Vente_FCFA': [0],
            'Prix_Achat_Moyen_FCFA': [0]
        })
        df_init_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')

    if not os.path.exists(CSV_VENTES):
        df_init_ventes = pd.DataFrame(columns=[
            'Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 
            'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon'
        ])
        df_init_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')

    if not os.path.exists(CSV_BONS):
        df_init_bons = pd.DataFrame(columns=[
            'Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur'
        ])
        df_init_bons.to_csv(CSV_BONS, index=False, encoding='utf-8-sig')
        
    if not os.path.exists(CSV_Z_HISTORIQUE):
        df_init_z = pd.DataFrame(columns=[
            'Ref_Z', 'Date_Cloture', 'Caissier', 'Recette_Encaissee', 'Articles_Vendus', 'Tables_Servies', 'Fond_De_Caisse', 'Observations'
        ])
        df_init_z.to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')

    if not os.path.exists(CSV_UTILISATEURS):
        df_init_users = pd.DataFrame({
            'Identifiant': ['admin'],
            'Mot_De_Passe': ['admin123'],
            'Role': ['Administrateur']
        })
        df_init_users.to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')

initialiser_fichiers_csv()

# Chargement des données persistantes
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = pd.read_csv(CSV_MENU)

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.read_csv(CSV_VENTES)

if 'historique_z' not in st.session_state:
    st.session_state.historique_z = pd.read_csv(CSV_Z_HISTORIQUE)

if 'base_utilisateurs' not in st.session_state:
    st.session_state.base_utilisateurs = pd.read_csv(CSV_UTILISATEURS)

if 'historique_bons' not in st.session_state:
    df_b = pd.read_csv(CSV_BONS)
    st.session_state.historique_bons = {}
    for _, r in df_b.iterrows():
        st.session_state.historique_bons[r['Ref_Bon']] = {
            'Date': r['Date'], 'Type': r['Type'], 'Article': r['Article'],
            'Quantite': r['Quantite'], 'Prix_Unitaire': r['Prix_Unitaire'], 
            'Total': r['Total'], 'Fournisseur': r['Fournisseur']
        }

# ==========================================
# 3. GESTION DE L'AUTHENTIFICATION & ROLES
# ==========================================
if 'authentifie' not in st.session_state:
    st.session_state.authentifie = False
if 'role_utilisateur' not in st.session_state:
    st.session_state.role_utilisateur = None
if 'nom_utilisateur' not in st.session_state:
    st.session_state.nom_utilisateur = None

OPTIONS_PAR_ROLE = {
    "Serveur": ["📝 Prise de Commande"],
    "Responsable Caisse": ["📝 Prise de Commande", "🧾 Commandes & Additions", "📦 Stocks & Approvisionnements"],
    "Administrateur": [
        "📝 Prise de Commande", 
        "🧾 Commandes & Additions", 
        "📦 Stocks & Approvisionnements", 
        "📊 Finances & Marges", 
        "🔒 Clôture de Caisse", 
        "⚙️ Configuration Carte", 
        "🔐 Administrateur"
    ]
}

def sauvegarder_utilisateurs():
    st.session_state.base_utilisateurs.to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')

# ==========================================
# 4. FONCTIONS DE SAUVEGARDE SUR LE DISQUE
# ==========================================
def sauvegarder_menu():
    st.session_state.base_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')

def sauvegarder_ventes():
    st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')

def sauvegarder_bons():
    liste_bons = []
    for ref, b in st.session_state.historique_bons.items():
        liste_bons.append({
            'Ref_Bon': ref, 'Date': b['Date'], 'Type': b['Type'], 'Article': b['Article'],
            'Quantite': b['Quantite'], 'Prix_Unitaire': b['Prix_Unitaire'], 'Total': b['Total'], 'Fournisseur': b['Fournisseur']
        })
    df_b = pd.DataFrame(liste_bons) if liste_bons else pd.DataFrame(columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur'])
    df_b.to_csv(CSV_BONS, index=False, encoding='utf-8-sig')

def sauvegarder_z_historique():
    st.session_state.historique_z.to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')

def consolider_stocks_et_marges():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    if not df_vnt.empty:
        df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Sorties')
        df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Code_Article')['Quantite'].sum().reset_index(name='Total_Entrees')
    else:
        df_sorties = pd.DataFrame(columns=['Code_Article', 'Total_Sorties'])
        df_entrees = pd.DataFrame(columns=['Code_Article', 'Total_Entrees'])
    df_res = df_art.merge(df_sorties, on='Code_Article', how='left').merge(df_entrees, on='Code_Article', how='left')
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    return df_res

df_global = consolider_stocks_et_marges()

# ==========================================
# VUE 1 : PRISE DE COMMANDE
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide & Options")
    if len(st.session_state.base_menu) == 0 or (len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']):
        st.warning("⚠️ La carte est vide. Utilisez l'accès Admin pour la configurer.")
        return
    col1, col2 = st.columns([1, 1])
    with col1:
        dict_menu, dict_categories = {}, {}
        for _, r in st.session_state.base_menu.iterrows():
            label = f"[{r['Categorie']}] {r['Designation']} ({int(r['Prix_Vente_FCFA'])} FCFA)"
            dict_menu[label] = r['Code_Article']
            dict_categories[label] = r['Categorie']

        with st.form("form_commande_strict", clear_on_submit=True):
            table_choisie = st.selectbox("Sélectionner la Table :", [f"Table {i}" for i in range(1, 31)])
            item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()))
            categorie_active = dict_categories[item_choisi] if item_choisi else "Cuisine"
            accomp_choisi = "-"
            if categorie_active == "Cuisine":
                accomp_choisi = st.selectbox("Accompagnement gratuit :", ["Alloco", "Attiéké", "Frites", "Riz Blanc", "Riz Gras", "Sans"])
            quantite = st.number_input("Quantité :", min_value=1, value=1)
            opt_remise = st.selectbox("Taux de remise :", [0, 5, 10, 15, 20])
            motif_remise = "Aucun" if opt_remise == 0 else "Geste Commercial"
            
            if st.form_submit_button("Envoyer la commande 🚀"):
                code_art = dict_menu[item_choisi]
                item_details = df_global[df_global['Code_Article'] == code_art].iloc[0]
                if quantite > item_details['Quantite_Dispo']:
                    st.error("❌ Stock insuffisant !")
                else:
                    total_net = (quantite * item_details['Prix_Vente_FCFA']) * (1 - (opt_remise / 100))
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': table_choisie, 'Code_Article': code_art,
                        'Type_Flux': 'Sortie', 'Quantite': quantite, 'Prix_Unitaire_Flux': item_details['Prix_Vente_FCFA'], 
                        'Remise_Pourcent': opt_remise, 'Accompagnement': accomp_choisi, 'Total_FCFA': total_net,
                        'Motif_Remise': motif_remise, 'Statut': 'En cours', 'Ref_Bon': '-'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    sauvegarder_ventes()
                    st.success("Commande enregistrée !")
                    st.rerun()
    with col2:
        st.info(f"👤 Connecté en tant que : **{st.session_state.nom_utilisateur}** ({st.session_state.role_utilisateur})")

# ==========================================
# VUE 2 : COMMANDES ET ADDITIONS
# ==========================================
def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande dans le système.")
        return

    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Categorie']], on='Code_Article', how='left')
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Calcul d'Addition", "📋 Journal Général des Opérations"])
    
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont actuellement réglées. ✨")
        else:
            tables_occupees = sorted(df_actives['Table'].unique())
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", tables_occupees)
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee].copy()
            
            def formater_libelle(row):
                if row['Accompagnement'] != "-" and row['Accompagnement'] != "Sans accompagnement":
                    return f"{row['Designation']} (+ {row['Accompagnement']})"
                return row['Designation']
                
            df_table_strict['Désignation Produit'] = df_table_strict.apply(formater_libelle, axis=1)
            
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Désignation Produit', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Total_FCFA']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours').index]
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                
                sauvegarder_ventes()
                st.success(f"La {table_selectionnee} a été validée !")
                st.rerun()
                
            if col_btn2.button(f"Annuler l'addition de la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours').index]
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                
                sauvegarder_ventes()
                st.warning(f"Commandes annulées.")
                st.rerun()

    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# VUE 3 : STOCKS & APPROVISIONNEMENTS
# ==========================================
def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Bons d'Entrée")
    tab_cuisine, tab_bar, tab_bons = st.tabs(["🍳 Stock CUISINE", "🍹 Stock BAR", "📄 Bons d'Entrée Valorisés"])
    
    with tab_cuisine:
        df_cuisine = df_global[df_global['Categorie'] == 'Cuisine']
        st.dataframe(df_cuisine[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Cuisine"):
            if df_cuisine.empty:
                st.info("Aucun article Cuisine configuré.")
            else:
                with st.form("form_appro_cuisine", clear_on_submit=True):
                    dict_cuisine = {r['Designation']: r['Code_Article'] for _, r in df_cuisine.iterrows()}
                    art_choisi = st.selectbox("Article Cuisine reçu :", list(dict_cuisine.keys()))
                    qte_recue = st.number_input("Quantité achetée :", min_value=1, value=10)
                    px_achat_unit = st.number_input("Prix d'Achat UNITAIRE (FCFA) :", min_value=0, value=1000)
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
                        sauvegarder_ventes()
                        sauvegarder_menu()
                        sauvegarder_bons()
                        st.success(f"Bon {ref_bon} mis à jour !")
                        st.rerun()

    with tab_bar:
        df_bar = df_global[df_global['Categorie'] == 'Bar']
        st.dataframe(df_bar[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Bar"):
            if df_bar.empty:
                st.info("Aucun article Bar configuré.")
            else:
                with st.form("form_appro_bar", clear_on_submit=True):
                    dict_bar = {r['Designation']: r['Code_Article'] for _, r in df_bar.iterrows()}
                    art_choisi_bar = st.selectbox("Boisson reçue :", list(dict_bar.keys()))
                    qte_recue_bar = st.number_input("Quantité achetée :", min_value=1, value=24)
                    px_achat_unit_bar = st.number_input("Prix d'Achat UNITAIRE (FCFA) :", min_value=0, value=500)
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
                        sauvegarder_ventes()
                        sauvegarder_menu()
                        sauvegarder_bons()
                        st.success(f"Bon {ref_bon} enregistré !")
                        st.rerun()

    with tab_bons:
        if not st.session_state.historique_bons:
            st.info("Aucun bon d'entrée disponible.")
        else:
            bon_selectionne = st.selectbox("Choisir un Bon pour contrôle :", list(st.session_state.historique_bons.keys())[::-1])
            b = st.session_state.historique_bons[bon_selectionne]
            
            code_html_bon = f"""
            <div id="print-area" style="border:2px solid #000; padding:20px; background-color:#fff; color:#000; font-family:monospace; max-width:600px; margin:auto;">
                <h2 style="text-align:center; margin:0;">EASYGEST RESTO - BON D'ENTRÉE</h2>
                <p style="text-align:center;"><b>N° BON : {bon_selectionne}</b></p>
                <hr style="border-top: 1px dashed #000;">
                <p><b>Date :</b> {b['Date']} | <b>Section :</b> {b['Type']}</p>
                <p><b>Fournisseur :</b> {b['Fournisseur']}</p>
                <hr style="border-top: 1px dashed #000;">
                <table style="width:100%; text-align:left;">
                    <tr><th>Désignation</th><th>Qté</th><th>P.U</th><th>Total</th></tr>
                    <tr><td>{b['Article']}</td><td>{b['Quantite']}</td><td>{b['Prix_Unitaire']:,} F</td><td>{b['Total']:,} F</td></tr>
                </table>
                <hr style="border-top: 1px dashed #000;">
                <h4 style="text-align:right;">MONTANT TOTAL : {b['Total']:,} FCFA</h4>
            </div>
            """
            st.markdown(code_html_bon, unsafe_allow_html=True)
            if st.button("🖨 Imprimer ce Bon d'Entrée", type="primary", use_container_width=True):
                js_script = f"""
                <script>
                    var printWindow = window.open('', '_blank', 'height=600,width=800');
                    printWindow.document.write('<html><body>{code_html_bon}</body></html>');
                    printWindow.document.close();
                    setTimeout(function() {{ printWindow.print(); printWindow.close(); }}, 500);
                </script>
                """
                components.html(js_script, height=0, width=0)

# ==========================================
# VUE 4 : FINANCES & MARGES
# ==========================================
def vue_finances_marges():
    st.subheader("📊 Compte d'Exploitation & Rentabilité Réelle")
    df_ventes_payees = st.session_state.historique_ventes[(st.session_state.historique_ventes['Type_Flux'] == 'Sortie') & (st.session_state.historique_ventes['Statut'] == 'Payé')]
    
    if df_ventes_payees.empty:
        st.info("Les données financières apparaîtront après les premiers encaissements.")
        return
        
    df_calc_marge = df_ventes_payees.groupby('Code_Article').agg({'Quantite': 'sum', 'Total_FCFA': 'sum'}).reset_index()
    df_calc_marge = df_calc_marge.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Prix_Achat_Moyen_FCFA']], on='Code_Article', how='left')
    
    df_calc_marge['Cout_Total_Achat'] = df_calc_marge['Quantite'] * df_calc_marge['Prix_Achat_Moyen_FCFA']
    df_calc_marge['Marge_Brute_FCFA'] = df_calc_marge['Total_FCFA'] - df_calc_marge['Cout_Total_Achat']
    
    ca_total = df_calc_marge['Total_FCFA'].sum()
    cout_achats_total = df_calc_marge['Cout_Total_Achat'].sum()
    marge_globale = df_calc_marge['Marge_Brute_FCFA'].sum()
    taux_marge_global = (marge_globale / ca_total) * 100 if ca_total > 0 else 0
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Chiffre d'Affaires Net Encaissé", f"{ca_total:,.0f} FCFA")
    f2.metric("Coût des Matières (Achats)", f"{cout_achats_total:,.0f} FCFA", delta="-Coûts", delta_color="inverse")
    f3.metric("Marge Réelle nette", f"{marge_globale:,.0f} FCFA", delta=f"{taux_marge_global:.1f}% de marge")

# ==========================================
# 🔒 VUE 5 : CLÔTURE DE CAISSE
# ==========================================
def vue_cloture_caisse():
    st.subheader("🔒 Clôture Journalière & Génération du Z de Caisse")
    st.write(f"Date d'activité : **{datetime.now().strftime('%d/%m/%Y')}**")
    st.markdown("---")
    
    df_v = st.session_state.historique_ventes
    df_jour_paye = df_v[(df_v['Type_Flux'] == 'Sortie') & (df_v['Statut'] == 'Payé')].copy()
    df_jour_en_cours = df_v[(df_v['Type_Flux'] == 'Sortie') & (df_v['Statut'] == 'En cours')].copy()
    
    ca_brut = df_jour_paye['Total_FCFA'].sum() if not df_jour_paye.empty else 0
    nb_couverts = int(df_jour_paye['Quantite'].sum()) if not df_jour_paye.empty else 0
    nb_tables = df_jour_paye['Table'].nunique() if not df_jour_paye.empty else 0
    panier_moyen = ca_brut / nb_tables if nb_tables > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recette Encaissée (FCFA)", f"{ca_brut:,.0f} F")
    c2.metric("Total Articles Vendus", f"{nb_couverts} pcs")
    c3.metric("Nombre de Tables Servies", f"{nb_tables}")
    c4.metric("Panier Moyen / Table", f"{panier_moyen:,.0f} F")
    
    if not df_jour_en_cours.empty:
        st.warning(f"⚠️ **Clôture impossible :** Il reste **{len(df_jour_en_cours)} table(s) en cours** non soldée(s).")
        return

    st.info("💡 Le système est prêt pour l'édition, l'archivage numérique et l'impression automatique du Z.")
    
    fond_de_caisse = st.number_input("Montant de fond de caisse laissé (FCFA) :", min_value=0, value=15000, key="cloture_fond")
    nom_caissier = st.text_input("Nom du caissier responsable :", value=st.session_state.nom_utilisateur, key="cloture_user")
    remarques = st.text_area("Observations / Écarts éventuels :", key="cloture_obs")
    check_verrou = st.checkbox("Je certifie l'exactitude des chiffres ci-dessus.", key="cloture_check")
    
    if st.button("🔒 Générer, Imprimer & Archiver le Z de Caisse", type="primary", use_container_width=True):
        if not nom_caissier:
            st.error("❌ Erreur : Veuillez renseigner le nom du caissier avant de valider.")
        elif not check_verrou:
            st.error("❌ Erreur : Vous devez cocher la case de certification des chiffres.")
        else:
            ref_z = f"Z-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            date_courante = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            nouvel_index_z = pd.DataFrame([{
                'Ref_Z': ref_z,
                'Date_Cloture': date_courante,
                'Caissier': nom_caissier,
                'Recette_Encaissee': ca_brut,
                'Articles_Vendus': nb_couverts,
                'Tables_Servies': nb_tables,
                'Fond_De_Caisse': fond_de_caisse,
                'Observations': remarques if remarques else "Aucune"
            }])
            st.session_state.historique_z = pd.concat([st.session_state.historique_z, nouvel_index_z], ignore_index=True)
            sauvegarder_z_historique()
            
            ticket_html = f"""
            <div id="thermal-z-ticket" style="border:1px dashed #000; padding:15px; background-color:#fff; color:#000; font-family:'Courier New', Courier, monospace; max-width:320px; margin:auto; font-size:13px; line-height:1.2;">
                <h3 style="text-align:center; margin:0 0 5px 0; font-size:16px;">*** EASYGEST RESTO ***</h3>
                <h4 style="text-align:center; margin:0 0 10px 0; font-size:14px;">TICKET Z DE CLÔTURE</h4>
                <p><b>REF TICKET :</b> {ref_z}</p>
                <p><b>DATE      :</b> {date_courante}</p>
                <p><b>CAISSIER :</b> {nom_caissier}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <table style="width:100%; font-size:13px;">
                    <tr><td>RECETTE TOTALE :</td><td style="text-align:right; font-weight:bold;">{ca_brut:,.0f} F</td></tr>
                    <tr><td>ARTICLES VENDUS:</td><td style="text-align:right;">{nb_couverts} pcs</td></tr>
                    <tr><td>TABLES CLÔTURE :</td><td style="text-align:right;">{nb_tables}</td></tr>
                    <tr><td>PANIER MOYEN   :</td><td style="text-align:right;">{panier_moyen:,.0f} F</td></tr>
                    <tr><td>FOND DE CAISSE :</td><td style="text-align:right;">{fond_de_caisse:,.0f} F</td></tr>
                </table>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <p><b>OBSERVATIONS :</b><br>{remarques if remarques else 'Aucune'}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <h4 style="text-align:center; margin:10px 0 0 0;">FIN DE SERVICE ARCHIVÉE</h4>
            </div>
            """
            
            st.success(f"🎉 Le rapport numérique {ref_z} a bien été archivé de manière sécurisée !")
            st.markdown("### 🖨️ Aperçu du Ticket Envoyé à l'Imprimante")
            st.markdown(ticket_html, unsafe_allow_html=True)
            
            js_print = f"""
            <script>
                var w = window.open('', '_blank', 'height=600,width=400');
                w.document.write('<html><head><title>Imprimer Z de Caisse</title></head><body style="margin:10px;">');
                w.document.write(`{ticket_html}`);
                w.document.write('</body></html>');
                w.document.close();
                setTimeout(function() {{ w.print(); w.close(); }}, 300);
            </script>
            """
            components.html(js_print, height=0, width=0)

# ==========================================
# VUE 6 : CONFIGURATION DE LA CARTE
# ==========================================
def vue_configuration_carte():
    st.subheader("⚙️ Configuration de la Carte")
    action = st.radio("Sélectionnez une action :", ["➕ Ajouter un Nouveau Produit", "✏️ Modifier un Produit Existant", "❌ Supprimer un Produit"])
    
    if action == "➕ Ajouter un Nouveau Produit":
        with st.form("form_ajout_produit", clear_on_submit=True):
            new_designation = st.text_input("Désignation du produit :")
            new_categorie = st.selectbox("Famille d'article :", ["Cuisine", "Bar"])
            c1, c2, c3 = st.columns(3)
            new_stock_init = c1.number_input("Stock Initial :", min_value=0, value=0)
            new_stock_min = c2.number_input("Stock Minimum :", min_value=1, value=5)
            new_prix_vente = c3.number_input("Prix de Vente (FCFA) :", min_value=0, value=1000)
            new_prix_achat = st.number_input("Prix d'Achat initial (FCFA) :", min_value=0, value=500)
            
            if st.form_submit_button("💾 Enregistrer le Produit"):
                if new_designation:
                    if len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']:
                        st.session_state.base_menu = pd.DataFrame(columns=st.session_state.base_menu.columns)
                    new_code = f"MENU{len(st.session_state.base_menu) + 1:03d}"
                    nouvel_article = pd.DataFrame([{
                        'Code_Article': new_code, 'Designation': new_designation, 'Categorie': new_categorie,
                        'Stock_Initial': new_stock_init, 'Stock_Minimum': new_stock_min, 
                        'Prix_Vente_FCFA': new_prix_vente, 'Prix_Achat_Moyen_FCFA': new_prix_achat
                    }])
                    st.session_state.base_menu = pd.concat([st.session_state.base_menu, nouvel_article], ignore_index=True)
                    sauvegarder_menu()
                    st.success("Article ajouté !")
                    st.sidebar.empty()
                    st.rerun()

    elif action == "✏️ Modifier un Produit Existant":
        if not st.session_state.base_menu.empty:
            dict_edit = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            prod = st.selectbox("Produit :", list(dict_edit.keys()))
            code = dict_edit[prod]
            infos = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code].iloc[0]
            
            with st.form("form_edit"):
                edit_name = st.text_input("Nom :", value=infos['Designation'])
                edit_px = st.number_input("Prix de Vente :", min_value=0, value=int(infos['Prix_Vente_FCFA']))
                if st.form_submit_button("Sauvegarder Changes"):
                    idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code].index
                    st.session_state.base_menu.loc[idx, 'Designation'] = edit_name
                    st.session_state.base_menu.loc[idx, 'Prix_Vente_FCFA'] = edit_px
                    sauvegarder_menu()
                    st.success("Produit modifié avec succès !")
                    st.rerun()

    elif action == "❌ Supprimer un Produit":
        if not st.session_state.base_menu.empty:
            dict_del = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            prod_to_del = st.selectbox("Sélectionner le produit à effacer :", list(dict_del.keys()))
            
            if st.button("Supprimer définitivement 🗑️", type="primary"):
                code_del = dict_del[prod_to_del]
                st.session_state.base_menu = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] != code_del]
                sauvegarder_menu()
                st.success(f"'{prod_to_del}' a été retiré de la carte.")
                st.rerun()

# ==========================================
# 🔐 VUE 7 : GESTION DES RÔLES & UTILISATEURS (NOUVEAU)
# ==========================================
def vue_gestion_utilisateurs():
    st.subheader("🔐 Administration : Rôles, Utilisateurs & Sécurité")
    
    tab_list, tab_add, tab_edit, tab_del = st.tabs([
        "📋 Liste des Utilisateurs", 
        "➕ Ajouter un Utilisateur", 
        "✏️ Modifier les Droits/Mots de Passe",
        "❌ Supprimer un Compte"
        "📁 Consultation Numérique des Z", 
        "🚨 Purges & Maintenance"
    ])
    
    # 1. Liste des comptes
    with tab_list:
        st.write("Comptes configurés sur cette machine :")
        st.dataframe(
            st.session_state.base_utilisateurs[['Identifiant', 'Role']], 
            use_container_width=True, 
            hide_index=True
        )
        
    # 2. Création de compte
    with tab_add:
        with st.form("form_creer_user", clear_on_submit=True):
            new_id = st.text_input("Identifiant / Nom de l'employé :").strip()
            new_pwd = st.text_input("Mot de passe :", type="password")
            new_role = st.selectbox("Attribuer un Rôle :", ["Serveur", "Responsable Caisse", "Administrateur"])
            
            if st.form_submit_button("Créer le compte utilisateur 💾"):
                if not new_id or not new_pwd:
                    st.error("Champs obligatoires manquants.")
                elif new_id in st.session_state.base_utilisateurs['Identifiant'].values:
                    st.error("Cet identifiant existe déjà.")
                else:
                    nouvel_u = pd.DataFrame([{'Identifiant': new_id, 'Mot_De_Passe': new_pwd, 'Role': new_role}])
                    st.session_state.base_utilisateurs = pd.concat([st.session_state.base_utilisateurs, nouvel_u], ignore_index=True)
                    sauvegarder_utilisateurs()
                    st.success(f"Compte pour **{new_id}** configuré avec succès !")
                    st.rerun()
                    
    # 3. Modification (Rôle ou Mot de passe)
    with tab_edit:
        users_list = st.session_state.base_utilisateurs['Identifiant'].tolist()
        selected_u = st.selectbox("Choisir l'utilisateur à modifier :", users_list)
        
        info_u = st.session_state.base_utilisateurs[st.session_state.base_utilisateurs['Identifiant'] == selected_u].iloc[0]
        
        with st.form("form_edit_user"):
            edit_pwd = st.text_input("Nouveau mot de passe (Laisser identique si inchangé) :", value=info_u['Mot_De_Passe'], type="password")
            edit_role = st.selectbox("Nouveau Rôle :", ["Serveur", "Responsable Caisse", "Administrateur"], index=["Serveur", "Responsable Caisse", "Administrateur"].index(info_u['Role']))
            
            if st.form_submit_button("Mettre à jour les accès 🔄"):
                idx = st.session_state.base_utilisateurs[st.session_state.base_utilisateurs['Identifiant'] == selected_u].index
                st.session_state.base_utilisateurs.loc[idx, 'Mot_De_Passe'] = edit_pwd
                st.session_state.base_utilisateurs.loc[idx, 'Role'] = edit_role
                sauvegarder_utilisateurs()
                st.success("Modifications enregistrées.")
                st.rerun()
                
    # 4. Suppression de compte
    with tab_del:
        users_to_del = st.session_state.base_utilisateurs['Identifiant'].tolist()
        del_target = st.selectbox("Sélectionner le compte à supprimer :", users_to_del)
        
        if st.button("Confirmer la suppression définitive 🗑️", type="primary"):
            target_role = st.session_state.base_utilisateurs[st.session_state.base_utilisateurs['Identifiant'] == del_target].iloc[0]['Role']
            nb_admins = len(st.session_state.base_utilisateurs[st.session_state.base_utilisateurs['Role'] == 'Administrateur'])
            
            if del_target == st.session_state.nom_utilisateur:
                st.error("Vous ne pouvez pas supprimer votre propre compte en cours de session.")
            elif target_role == "Administrateur" and nb_admins <= 1:
                st.error("Action impossible. Le système requiert au moins un compte Administrateur actif.")
            else:
                st.session_state.base_utilisateurs = st.session_state.base_utilisateurs[st.session_state.base_utilisateurs['Identifiant'] != del_target]
                sauvegarder_utilisateurs()
                st.success(f"Compte de {del_target} supprimé.")
                st.rerun()
                with tab_logs:
        st.write("Retrouvez ci-dessous l'intégralité des clôtures de caisse (Rapports Z) enregistrées numériquement.")
        if st.session_state.historique_z.empty:
            st.info("Aucun rapport Z n'a encore été archivé numériquement dans le système.")
        else:
            # Affichage de la grille globale ordonnée par date descendante
            st.dataframe(st.session_state.historique_z.sort_index(ascending=False), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### 🔎 Inspecter & Réimprimer un Duplicata")
            
            liste_z = st.session_state.historique_z['Ref_Z'].tolist()[::-1]
            z_choisi = st.selectbox("Sélectionnez la référence du rapport Z à analyser :", liste_z)
            
            # Récupération des informations associées à ce Z
            infos_z = st.session_state.historique_z[st.session_state.historique_z['Ref_Z'] == z_choisi].iloc[0]
            
            # Reconstruction du ticket pour visualisation et réimpression
            ticket_reconstruit = f"""
            <div style="border:1px solid #000; padding:15px; background-color:#fff; color:#000; font-family:'Courier New', Courier, monospace; max-width:320px; margin:10px auto; font-size:13px; line-height:1.2;">
                <h3 style="text-align:center; margin:0 0 5px 0; font-size:16px;">*** EASYGEST RESTO ***</h3>
                <h4 style="text-align:center; margin:0 0 10px 0; font-size:14px;">DUPLICATA TICKET Z</h4>
                <p><b>REF TICKET :</b> {infos_z['Ref_Z']}</p>
                <p><b>DATE CLÔTURE:</b> {infos_z['Date_Cloture']}</p>
                <p><b>CAISSIER    :</b> {infos_z['Caissier']}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <table style="width:100%; font-size:13px;">
                    <tr><td>RECETTE COLLECTÉE:</td><td style="text-align:right; font-weight:bold;">{float(infos_z['Recette_Encaissee']):,.0f} F</td></tr>
                    <tr><td>ARTICLES VENDUS  :</td><td style="text-align:right;">{infos_z['Articles_Vendus']} pcs</td></tr>
                    <tr><td>TABLES FACTURÉES :</td><td style="text-align:right;">{infos_z['Tables_Servies']}</td></tr>
                    <tr><td>FOND DE CAISSE   :</td><td style="text-align:right;">{float(infos_z['Fond_De_Caisse']):,.0f} F</td></tr>
                </table>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <p><b>OBSERVATIONS :</b><br>{infos_z['Observations']}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <h4 style="text-align:center; margin:5px 0 0 0; font-size:11px; color:#555;">DUPLICATA SÉCURISÉ ADMIN</h4>
            </div>
            """
            
            col_z_1, col_z_2 = st.columns([1, 2])
            with col_z_1:
                st.markdown(ticket_reconstruit, unsafe_allow_html=True)
            with col_z_2:
                st.info("💡 Ce panneau vous permet de réimprimer un ticket à tout moment si le rouleau thermique de la caisse a subi une coupure ou une panne lors de la fermeture.")
                if st.button("🖨️ Lancer la réimpression de ce Duplicata Z", type="secondary", use_container_width=True):
                    js_reprint = f"""
                    <script>
                        var w = window.open('', '_blank', 'height=600,width=400');
                        w.document.write('<html><head><title>Duplicata Z</title></head><body>');
                        w.document.write(`{ticket_reconstruit}`);
                        w.document.write('</body></html>');
                        w.document.close();
                        setTimeout(function() {{ w.print(); w.close(); }}, 300);
                    </script>
                    """
                    components.html(js_reprint, height=0, width=0)

    with tab_purge:
        if st.checkbox("Activer l'option de réinitialisation générale du journal"):
            if st.button("🚨 VIDER LE JOURNAL DES OPÉRATIONS", type="primary"):
                st.session_state.historique_ventes = pd.DataFrame(columns=['Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon'])
                st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
                st.rerun()

# ==========================================
# GESTION DES ÉCRANS LOGIQUES
# ==========================================
if not st.session_state.authentifie:
    st.markdown("<h2 style='text-align: center;'>🔑 Connexion - Easygest Resto Pro+</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    
    with col_l2:
        with st.form("form_login"):
            input_user = st.text_input("Identifiant :").strip()
            input_password = st.text_input("Mot de passe :", type="password")
            btn_login = st.form_submit_button("Se connecter 🔓", use_container_width=True)
            
            if btn_login:
                match_user = st.session_state.base_utilisateurs[
                    (st.session_state.base_utilisateurs['Identifiant'] == input_user) & 
                    (st.session_state.base_utilisateurs['Mot_De_Passe'] == input_password)
                ]
                if not match_user.empty:
                    st.session_state.authentifie = True
                    st.session_state.role_utilisateur = match_user.iloc[0]['Role']
                    st.session_state.nom_utilisateur = match_user.iloc[0]['Identifiant']
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
else:
    # Sidebar de navigation selon rôle
    st.sidebar.title("🍳 Easygest Resto Pro+")
    st.sidebar.write(f"Utilisateur : **{st.session_state.nom_utilisateur}**")
    st.sidebar.write(f"Statut : `{st.session_state.role_utilisateur}`")
    st.sidebar.markdown("---")
    
    options_disponibles = OPTIONS_PAR_ROLE.get(st.session_state.role_utilisateur, ["Prise de Commande"])
    choix_menu = st.sidebar.radio("Navigation principale :", options_disponibles)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Déconnexion 🔒", use_container_width=True):
        st.session_state.authentifie = False
        st.session_state.role_utilisateur = None
        st.session_state.nom_utilisateur = None
        st.rerun()

    # Routage des vues
    if choix_menu == "📝 Prise de Commande":
        vue_prise_commande()
    elif choix_menu == "🧾 Commandes & Additions":
        vue_commandes_additions()
    elif choix_menu == "📦 Stocks & Approvisionnements":
        vue_stocks_appro()
    elif choix_menu == "📊 Finances & Marges":
        vue_finances_marges()
    elif choix_menu == "🔒 Clôture de Caisse":
        vue_cloture_caisse()
    elif choix_menu == "⚙️ Configuration Carte":
        vue_configuration_carte()
    elif choix_menu == "🔐 Administrateur":
        vue_gestion_utilisateurs()
