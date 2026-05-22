import streamlit as st
import pandas as pd
import numpy as np
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

# --- CONFIGURATION DU DOSSIER LOCAL C: ---
def initialiser_dossier_easygest():
    """
    Vérifie l'existence du dossier 'EASYGEST APPS' sur le disque C:
    et le crée s'il n'existe pas. Retourne le chemin d'accès sécurisé.
    """
    chemin_cible = r"C:\EASYGEST APPS"
    
    if not os.path.exists(chemin_cible):
        try:
            os.makedirs(chemin_cible)
            print(f" [+] Configuration initiale : Dossier créé avec succès -> {chemin_cible}")
        except Exception as e:
            print(f" [!] Erreur d'accès au disque C: ({e})")
            chemin_cible = os.path.join(os.getcwd(), "EASYGEST_APPS_LOCAL")
            if not os.path.exists(chemin_cible):
                os.makedirs(chemin_cible)
            print(f" [->] Solution de repli activée : Stockage dans -> {chemin_cible}")
            
    # Création du dossier de sauvegarde (backups)
    dossier_backup = os.path.join(chemin_cible, "backups")
    if not os.path.exists(dossier_backup):
        os.makedirs(dossier_backup)
    
    return chemin_cible

# Récupération dynamique du dossier d'exploitation
DOSSIER_EXPLOITATION = initialiser_dossier_easygest()
DOSSIER_BACKUPS = os.path.join(DOSSIER_EXPLOITATION, "backups")

# Liaison des fichiers de données vers le dossier local
CSV_MENU = os.path.join(DOSSIER_EXPLOITATION, "easygest_base_menu.csv")
CSV_VENTES = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_ventes.csv")
CSV_BONS = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_bons.csv")

# Fonctions de persistance et initialisation propre (Sans données démo)
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

initialiser_fichiers_csv()

# Chargement dans le Session State
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = pd.read_csv(CSV_MENU)

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.read_csv(CSV_VENTES)

if 'historique_bons' not in st.session_state:
    df_b = pd.read_csv(CSV_BONS)
    st.session_state.historique_bons = {}
    for _, r in df_b.iterrows():
        st.session_state.historique_bons[r['Ref_Bon']] = {
            'Date': r['Date'], 'Type': r['Type'], 'Article': r['Article'],
            'Quantite': r['Quantite'], 'Prix_Unitaire': r['Prix_Unitaire'], 
            'Total': r['Total'], 'Fournisseur': r['Fournisseur']
        }

# --- FUNCTIONS DE SAUVEGARDE ET DE BACKUP ---
def sauvegarder_menu():
    st.session_state.base_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_backup = os.path.join(DOSSIER_BACKUPS, f"backup_menu_{horodatage}.csv")
    st.session_state.base_menu.to_csv(chemin_backup, index=False, encoding='utf-8-sig')

def sauvegarder_ventes():
    st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_backup = os.path.join(DOSSIER_BACKUPS, f"backup_ventes_{horodatage}.csv")
    st.session_state.historique_ventes.to_csv(chemin_backup, index=False, encoding='utf-8-sig')

def sauvegarder_bons():
    liste_bons = []
    for ref, b in st.session_state.historique_bons.items():
        liste_bons.append({
            'Ref_Bon': ref, 'Date': b['Date'], 'Type': b['Type'], 'Article': b['Article'],
            'Quantite': b['Quantite'], 'Prix_Unitaire': b['Prix_Unitaire'], 
            'Total': b['Total'], 'Fournisseur': b['Fournisseur']
        })
    df_b = pd.DataFrame(liste_bons) if liste_bons else pd.DataFrame(columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur'])
    df_b.to_csv(CSV_BONS, index=False, encoding='utf-8-sig')
    
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_backup = os.path.join(DOSSIER_BACKUPS, f"backup_bons_{horodatage}.csv")
    df_b.to_csv(chemin_backup, index=False, encoding='utf-8-sig')

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
    df_res['Valeur_Stock_Vente_FCFA'] = df_res['Quantite_Dispo'] * df_res['Prix_Vente_FCFA']
    
    return df_res

df_global = consolider_stocks_et_marges()

# ==========================================
# VUE 1 : PRISE DE COMMANDE SANS PORTIONNAGE
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide & Options")
    
    if len(st.session_state.base_menu) == 0 or (len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']):
        st.warning("⚠️ La carte est actuellement vide. Veuillez d'abord ajouter vos vrais produits dans l'onglet 'Configuration Carte' avant de prendre des commandes.")
        return

    col1, col2 = st.columns([1, 1])
    
    with col1:
        dict_menu = {}
        dict_categories = {} 
        for _, r in st.session_state.base_menu.iterrows():
            label = f"[{r['Categorie']}] {r['Designation']} ({int(r['Prix_Vente_FCFA'])} FCFA)"
            dict_menu[label] = r['Code_Article']
            dict_categories[label] = r['Categorie']

        with st.form("form_commande_strict", clear_on_submit=True):
            liste_tables = [f"Table {i}" for i in range(1, 31)]
            table_choisie = st.selectbox("Sélectionner la Table :", liste_tables, key="cmd_table")
            item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()), key="cmd_article")
            
            categorie_active = dict_categories[item_choisi] if item_choisi else "Cuisine"
            
            accomp_choisi = "-"
            if categorie_active == "Cuisine":
                st.markdown("👇 *Options Spécifiques Cuisine*")
                accomp_choisi = st.selectbox(
                    "Choisir l'accompagnement gratuit :", 
                    ["Alloco", "Attiéké", "Frites de Pomme de terre", "Riz Blanc", "Riz Gras", "Sans accompagnement"],
                    key="cmd_accomp"
                )
                st.markdown("---")
            
            quantite = st.number_input("Quantité :", min_value=1, value=1, key="cmd_qte")
            
            st.markdown("##### 🎁 Option de Remise (Optionnel)")
            opt_remise = st.selectbox("Taux de remise à appliquer :", [0, 5, 10, 15, 20, "Autre (Saisie manuelle)"], key="cmd_opt_remise")
            
            if opt_remise == "Autre (Saisie manuelle)":
                taux_remise = st.number_input("Entrez le taux de remise (%) :", min_value=0, max_value=100, value=0, key="cmd_taux_manuel")
            else:
                taux_remise = int(opt_remise)
                
            motif_remise = "Aucun"
            if taux_remise > 0:
                motif_remise = st.selectbox("Motif / Profil bénéficiaire :", ["Client Fidèle ⭐", "Ami Spécial 🤝", "Geste Commercial 🛠️"], key="cmd_motif")
            
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
                    
                    sauvegarder_ventes()
                    st.success(f"Commande envoyée pour la {table_choisie} ! Enregistrement OK.")
                    st.rerun()
                    
    with col2:
        st.info(f"💾 **Répertoire de Production Actif :**\n- Emplacement de la base de données locale : `{DOSSIER_EXPLOITATION}`\n- Sécurité : Vos données sont clonées dans le dossier `backups` à chaque transaction.")

# ==========================================
# VUE 2 : COMMANDES ET ADDITIONS (ÉCRAN CAISSE)
# ==========================================
def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande en cours dans le système.")
        return

    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Categorie']], on='Code_Article', how='left')
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Calcul d'Addition", "📋 Journal Général des Opérations"])
    
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont actuellement libres et clôturées. ✨")
        else:
            tables_occupees = sorted(df_actives['Table'].unique())
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", tables_occupees)
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee].copy()
            
            def formater_libelle(row):
                if row['Accompagnement'] != "-" and row['Accompagnement'] != "Sans accompagnement":
                    return f"{row['Designation']} (+ {row['Accompagnement']})"
                return row['Designation']
                
            df_table_strict['Désignation Produit'] = df_table_strict.apply(formater_libelle, axis=1)
            
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Désignation Produit', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Total_FCFA', 'Motif_Remise']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                
                sauvegarder_ventes()
                st.success(f"La {table_selectionnee} a été validée avec succès !")
                st.rerun()
                
            if col_btn2.button(f"Annuler l'addition de la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                
                sauvegarder_ventes()
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
            if df_cuisine.empty:
                st.info("Aucun article Cuisine configuré à la carte.")
            else:
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
                        sauvegarder_ventes()
                        sauvegarder_menu()
                        sauvegarder_bons()
                        
                        st.success(f"Bon {ref_bon} créé avec succès et stock mis à jour !")
                        st.rerun()

    with tab_bar:
        df_bar = df_global[df_global['Categorie'] == 'Bar']
        st.dataframe(df_bar[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Bar"):
            if df_bar.empty:
                st.info("Aucun article Bar configuré à la carte.")
            else:
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
                        sauvegarder_ventes()
                        sauvegarder_menu()
                        sauvegarder_bons()
                        
                        st.success(f"Bon {ref_bon} enregistré avec succès !")
                        st.rerun()

    with tab_bons:
        if not st.session_state.historique_bons:
            st.info("Aucun bon d'entrée disponible pour le moment.")
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
                st.success("Fenêtre d'impression ouverte !")

# ==========================================
# VUE 4 : FINANCES AVEC IMPACT DES REMISES
# ==========================================
def vue_finances_marges():
    st.subheader("📊 Compte d'Exploitation & Rentabilité Réelle")
    df_ventes_payees = st.session_state.historique_ventes[(st.session_state.historique_ventes['Type_Flux'] == 'Sortie') & (st.session_state.historique_ventes['Statut'] == 'Payé')]
    
    if df_ventes_payees.empty:
        st.info("Les indicateurs financiers s'activeront dès les premiers encaissements réels.")
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
    
    st.markdown("---")
    st.markdown("### 📋 Analyse des Ventes par Table")
    st.dataframe(df_ventes_payees.merge(st.session_state.base_menu[['Code_Article', 'Designation']], on='Code_Article')[['Heure', 'Table', 'Designation', 'Quantite', 'Accompagnement', 'Remise_Pourcent', 'Motif_Remise', 'Total_FCFA']], use_container_width=True, hide_index=True)

# ==========================================
# VUE 5 : CONFIGURATION DE LA CARTE (PAR LE CLIENT)
# ==========================================
def vue_configuration_carte():
    st.subheader("⚙️ Configuration de la Carte (Ajout / Modification / Suppression)")
    action = st.radio("Sélectionnez l'action de gestion de votre carte :", ["➕ Ajouter un Nouveau Produit", "✏️ Modifier un Produit Existant", "❌ Supprimer un Produit de la Carte"])
    st.markdown("---")
    
    if action == "➕ Ajouter un Nouveau Produit":
        with st.form("form_ajout_produit", clear_on_submit=True):
            new_designation = st.text_input("Désignation du produit (ex: Kedjenou de Poulet, Soupe de Poisson, Heineken...) :")
            new_categorie = st.selectbox("Famille d'article :", ["Cuisine", "Bar"])
            c1, c2, c3 = st.columns(3)
            new_stock_init = c1.number_input("Stock Initial disponible (Saisie unique de départ) :", min_value=0, value=0)
            new_stock_min = c2.number_input("Seuil d'Alerte Stock Minimum (Alerte Rouge) :", min_value=1, value=5)
            new_prix_vente = c3.number_input("Prix de Vente Client (FCFA) :", min_value=0, value=1000, step=100)
            new_prix_achat = st.number_input("Prix d'Achat Estimé / unitaire (FCFA) :", min_value=0, value=500, step=50)
            
            if st.form_submit_button("💾 Enregistrer ce Produit à la Carte"):
                if not new_designation:
                    st.error("Le nom du produit est obligatoire.")
                else:
                    if len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']:
                        st.session_state.base_menu = pd.DataFrame(columns=st.session_state.base_menu.columns)
                    
                    prochain_id = len(st.session_state.base_menu) + 1
                    new_code = f"MENU{prochain_id:03d}"
                    nouvel_article = pd.DataFrame([{
                        'Code_Article': new_code, 'Designation': new_designation, 'Categorie': new_categorie,
                        'Stock_Initial': new_stock_init, 'Stock_Minimum': new_stock_min, 
                        'Prix_Vente_FCFA': new_prix_vente, 'Prix_Achat_Moyen_FCFA': new_prix_achat
                    }])
                    st.session_state.base_menu = pd.concat([st.session_state.base_menu, nouvel_article], ignore_index=True)
                    
                    sauvegarder_menu()
                    st.success(f"Félicitations ! L'article '{new_designation}' est maintenant disponible sur la carte.")
                    st.rerun()

    elif action == "✏️ Modifier un Produit Existant":
        if st.session_state.base_menu.empty or (len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']):
            st.info("Aucun produit disponible à modifier.")
            return

        dict_edit = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
        produit_a_modifier = st.selectbox("Sélectionner le produit à réajuster :", list(dict_edit.keys()))
        code_strict = dict_edit[produit_a_modifier]
        infos_actuelles = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_strict].iloc[0]
        
        with st.form("form_edit_produit"):
            edit_designation = st.text_input("Modifier le nom de l'article :", value=infos_actuelles['Designation'])
            edit_categorie = st.selectbox("Modifier la Famille :", ["Cuisine", "Bar"], index=0 if infos_actuelles['Categorie'] == 'Cuisine' else 1)
            col1, col2 = st.columns(2)
            edit_prix_vente = col1.number_input("Nouveau Prix de Vente (FCFA) :", min_value=0, value=int(infos_actuelles['Prix_Vente_FCFA']), step=100)
            edit_stock_min = col2.number_input("Nouveau Stock Minimum :", min_value=1, value=int(infos_actuelles['Stock_Minimum']))
            
            if st.form_submit_button("⚡ Sauvegarder les Changements"):
                idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code_strict].index
                st.session_state.base_menu.loc[idx, 'Designation'] = edit_designation
                st.session_state.base_menu.loc[idx, 'Categorie'] = edit_categorie
                st.session_state.base_menu.loc[idx, 'Prix_Vente_FCFA'] = edit_prix_vente
                st.session_state.base_menu.loc[idx, 'Stock_Minimum'] = edit_stock_min
                
                sauvegarder_menu()
                st.success(f"Modifications enregistrées localement.")
                st.rerun()

    elif action == "❌ Supprimer un Produit de la Carte":
        if st.session_state.base_menu.empty:
            st.info("La carte est déjà vide.")
            return

        if not st.session_state.historique_ventes.empty:
            codes_utilises = set(st.session_state.historique_ventes[st.session_state.historique_ventes['Type_Flux'] == 'Sortie']['Code_Article'].unique())
        else:
            codes_utilises = set()
            
        options_suppression = {}
        for _, r in st.session_state.base_menu.iterrows():
            deja_vendu = r['Code_Article'] in codes_utilises
            label = f"{r['Designation']} ({r['Categorie']}) — {'🔒 Vendu (Verrouillé pour cohérence comptable)' if deja_vendu else '🔓 Supprimable'}"
            options_suppression[label] = {'code': r['Code_Article'], 'bloque': deja_vendu, 'nom': r['Designation']}
            
        choix_label = st.selectbox("Choisir l'article à supprimer définitivement :", list(options_suppression.keys()))
        
        if choix_label:
            info_art = options_suppression[choix_label]
            if info_art['bloque']:
                st.error("🚨 Cet article ne peut pas être supprimé car il possède des données de vente associées dans le Journal des Opérations. (Sécurité comptable)")
            else:
                if st.button(f"🗑️ Confirmer la suppression définitive de {info_art['nom']}", type="primary"):
                    st.session_state.base_menu = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] != info_art['code']]
                    sauvegarder_menu()
                    st.success("Produit retiré de la carte.")
                    st.rerun()

# ==========================================
# 🆕 VUE 6 : ESPACE ADMINISTRATEUR (NOUVEAU)
# ==========================================
def vue_administrateur():
    st.subheader("🔐 Espace Administrateur : Maintenance du système")
    st.write("Cet écran permet d'effectuer des opérations sensibles sur la base de données de l'application.")
    
    st.markdown("---")
    st.error("⚠️ **Zone de Danger : Réinitialisation du Journal Général des Opérations**")
    st.write("Cette action supprimera **définitivement** tout l'historique des ventes, des annulations et des réapprovisionnements (les données visibles dans l'onglet mentionné sur le fichier *image_43927f.png*). Votre base de produits (la carte) restera intacte.")
    
    # Étape de sécurité 1 : Demande de mot de passe admin (Ici par défaut : admin123)
    mot_de_pass = st.text_input("Veuillez saisir le mot de passe administrateur pour déverrouiller l'action :", type="password")
    
    if mot_de_pass == "admin123":
        st.success("🔓 Mot de passe correct. Option de suppression débloquée.")
        
        # Étape de sécurité 2 : Case à cocher de confirmation
        confirmation = st.checkbox("Je comprends que cette action est irréversible et effacera l'historique complet.")
        
        if confirmation:
            if st.button("🚨 VIDER LE JOURNAL GÉNÉRAL DES OPÉRATIONS", type="primary", use_container_width=True):
                # 1. On vide le DataFrame en conservant la structure exacte des colonnes
                colonnes_ventes = [
                    'Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 
                    'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon'
                ]
                st.session_state.historique_ventes = pd.DataFrame(columns=colonnes_ventes)
                
                # 2. On écrase le fichier CSV principal pour enregistrer la modification
                st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
                
                # 3. Par sécurité, on force un backup horodaté de l'état "vide"
                horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
                chemin_backup = os.path.join(DOSSIER_BACKUPS, f"backup_ventes_REINITIALISE_{horodatage}.csv")
                st.session_state.historique_ventes.to_csv(chemin_backup, index=False, encoding='utf-8-sig')
                
                st.toast("Journal des opérations effacé avec succès !", icon="🗑️")
                st.success("Le journal général des opérations a été vidé avec succès. L'application va s'actualiser.")
                
                # Rafraîchissement automatique
                st.rerun()
    elif mot_de_pass != "":
        st.error("❌ Mot de passe administrateur incorrect.")


# ==========================================
# 📊 BARRE LATERALE ET ROUTAGE PRINCIPAL
# ==========================================
st.sidebar.title("🍳 Easygest Resto Pro+")
st.sidebar.markdown(f"**Version 2026**")
st.sidebar.markdown("---")

choix_menu = st.sidebar.radio(
    "Navigation Principale :",
    [
        "📝 Prise de Commande",
        "🧾 Commandes & Additions",
        "📦 Stocks & Approvisionnements",
        "📊 Finances & Marges",
        "⚙️ Configuration Carte",
        "🔐 Administrateur" # Ajout de la nouvelle option ici
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Développé pour la gestion locale fluide d'un restaurant.")

# Logique de routage vers les fonctions d'affichage
if choix_menu == "📝 Prise de Commande":
    vue_prise_commande()
elif choix_menu == "🧾 Commandes & Additions":
    vue_commandes_additions()
elif choix_menu == "📦 Stocks & Approvisionnements":
    vue_stocks_appro()
elif choix_menu == "📊 Finances & Marges":
    vue_finances_marges()
elif choix_menu == "⚙️ Configuration Carte":
    vue_configuration_carte()
elif choix_menu == "🔐 Administrateur":
    vue_administrateur()
