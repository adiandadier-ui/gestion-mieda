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

initialiser_fichiers_csv()

# Chargement dans le Session State
if 'base_menu' not in st.session_state:
    st.session_state.base_menu = pd.read_csv(CSV_MENU)

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.read_csv(CSV_VENTES)

if 'historique_z' not in st.session_state:
    st.session_state.historique_z = pd.read_csv(CSV_Z_HISTORIQUE)

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

# ==========================================
# 4. FONCTIONS DE PERSISTANCE & BACKUPS
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

# --- VUES ---
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
        st.info(f"👤 Connecté en tant que : **{st.session_state.role_utilisateur}**")

def vue_commandes_additions():
    st.subheader("🧾 Écran Caisse : Suivi des Tables & Additions")
    if st.session_state.historique_ventes.empty:
        st.info("Aucune commande dans le système.")
        return
    df_suivi = st.session_state.historique_ventes.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Categorie']], on='Code_Article', how='left')
    df_actives = df_suivi[df_suivi['Statut'] == 'En cours'].copy()
    
    tabs_caisse = st.tabs(["🪑 Calcul d'Addition", "📋 Journal Général"])
    with tabs_caisse[0]:
        if df_actives.empty:
            st.success("Toutes les tables sont réglées. ✨")
        else:
            table_selectionnee = st.selectbox("Sélectionner la table à encaisser :", sorted(df_actives['Table'].unique()))
            df_table_strict = df_actives[df_actives['Table'] == table_selectionnee].copy()
            st.dataframe(df_table_strict[['Heure', 'Designation', 'Quantite', 'Total_FCFA']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            
            c1, c2 = st.columns(2)
            if c1.button(f"Encaisser la {table_selectionnee} 💰", type="primary"):
                idx = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[idx, 'Statut'] = 'Payé'
                sauvegarder_ventes()
                st.rerun()
            if c2.button(f"Annuler la {table_selectionnee} ❌"):
                idx = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[idx, 'Statut'] = 'Annulé'
                sauvegarder_ventes()
                st.rerun()
    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Approvisionnements")
    t1, t2 = st.tabs(["🍳 Cuisine", "🍹 Bar"])
    with t1:
        st.dataframe(df_global[df_global['Categorie'] == 'Cuisine'][['Code_Article', 'Designation', 'Quantite_Dispo']], use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(df_global[df_global['Categorie'] == 'Bar'][['Code_Article', 'Designation', 'Quantite_Dispo']], use_container_width=True, hide_index=True)

def vue_finances_marges():
    st.subheader("📊 Compte d'Exploitation & Rentabilité")
    df_p = st.session_state.historique_ventes[st.session_state.historique_ventes['Statut'] == 'Payé']
    if df_p.empty:
        st.info("Aucune donnée financière encaissée.")
        return
    ca = df_p['Total_FCFA'].sum()
    st.metric("Chiffre d'Affaires Encaissé", f"{ca:,.0f} FCFA")

# ========================================================
# 🔒 VUE 5 : CLÔTURE DE CAISSE AVEC IMPRESSION ET DIGITALISATION
# ========================================================
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
    
    # Rappel des KPI du haut (Similaire à l'image_a4597a.png)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recette Encaissée (FCFA)", f"{ca_brut:,.0f} F")
    c2.metric("Total Articles Vendus", f"{nb_couverts} pcs")
    c3.metric("Nombre de Tables Servies", f"{nb_tables}")
    c4.metric("Panier Moyen / Table", f"{panier_moyen:,.0f} F")
    
    if not df_jour_en_cours.empty:
        st.warning(f"⚠️ **Clôture impossible :** Il reste **{len(df_jour_en_cours)} table(s) en cours** non soldée(s).")
        return

    st.info("💡 Le système est prêt pour l'édition et l'archivage numérique du Z de Caisse.")
    
    # Variables de formulaire isolées hors du st.form pour conserver le rendu HTML après soumission
    fond_de_caisse = st.number_input("Montant de fond de caisse laissé (FCFA) :", min_value=0, value=15000, key="cloture_fond")
    nom_caissier = st.text_input("Nom du caissier responsable :", key="cloture_user")
    remarques = st.text_area("Observations / Écarts éventuels :", key="cloture_obs")
    check_verrou = st.checkbox("Je certifie l'exactitude des chiffres ci-dessus.", key="cloture_check")
    
    if st.button("🔒 Générer, Imprimer & Archiver le Z de Caisse", type="primary", use_container_width=True):
        if not nom_caissier:
            st.error("❌ Erreur : Veuillez renseigner le nom du caissier avant de valider.")
        elif not check_verrou:
            st.error("❌ Erreur : Vous devez cocher la case de certification des chiffres.")
        else:
            # 1. Génération de la référence unique du Z
            ref_z = f"Z-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            date_courante = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Archivage dans l'historique numérique (DataFrame & CSV global)
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
            
            # 3. Création du format d'impression Ticket de Caisse (HTML Thermal Style)
            ticket_html = f"""
            <div id="thermal-z-ticket" style="border:1px dashed #000; padding:15px; background-color:#fff; color:#000; font-family:'Courier New', Courier, monospace; max-width:320px; margin:auto; font-size:13px; line-height:1.2;">
                <h3 style="text-align:center; margin:0 0 5px 0; font-size:16px;">*** EASYGEST RESTO ***</h3>
                <h4 style="text-align:center; margin:0 0 10px 0; font-size:14px;">TICKET Z DE CLÔTURE</h4>
                <p><b>REF TICKET :</b> {ref_z}</p>
                <p><b>DATE     :</b> {date_courante}</p>
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
            
            # Affichage du rendu visuel à l'écran
            st.success(f"🎉 Le rapport numérique {ref_z} a été enregistré avec succès sur le disque local !")
            st.markdown("### 🖨️ Aperçu du Ticket Imprimé")
            st.markdown(ticket_html, unsafe_allow_html=True)
            
            # Action JavaScript injectée de manière invisible pour lancer la boîte d'impression
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

def vue_configuration_carte():
    st.subheader("⚙️ Configuration de la Carte")
    with st.form("add_p"):
        d = st.text_input("Nom produit :")
        c = st.selectbox("Famille :", ["Cuisine", "Bar"])
        p = st.number_input("Prix Vente :", value=1000)
        if st.form_submit_button("Enregistrer"):
            if d:
                if len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']:
                    st.session_state.base_menu = pd.DataFrame(columns=st.session_state.base_menu.columns)
                code = f"MENU{len(st.session_state.base_menu) + 1:03d}"
                n = pd.DataFrame([{'Code_Article': code, 'Designation': d, 'Categorie': c, 'Stock_Initial': 100, 'Stock_Minimum': 5, 'Prix_Vente_FCFA': p, 'Prix_Achat_Moyen_FCFA': 0}])
                st.session_state.base_menu = pd.concat([st.session_state.base_menu, n], ignore_index=True)
                sauvegarder_menu()
                st.rerun()

# ========================================================
# 🔐 VUE 7 : ZONE ADMIN - AJOUT CONSULTATION DES NUMERIQUES Z
# ========================================================
def vue_administrateur():
    st.subheader("🔐 Espace Administrateur : Maintenance & Consultation")
    
    tab_logs, tab_purge = st.tabs(["📁 Consultation Numérique des Z", "🚨 Purges & Maintenance"])
    
    with tab_logs:
        st.write("Retrouvez ici l'ensemble des clôtures archivées numériquement dans le système.")
        if st.session_state.historique_z.empty:
            st.info("Aucun historique numérique de clôture de caisse enregistré pour le moment.")
        else:
            # Tableau récapitulatif synthétique
            st.dataframe(st.session_state.historique_z.sort_index(ascending=False), use_container_width=True, hide_index=True)
            
            st.markdown("### 🔎 Visualiser et Réimprimer un Ticket Z spécifique")
            liste_z = st.session_state.historique_z['Ref_Z'].tolist()[::-1]
            z_choisi = st.selectbox("Sélectionnez la référence du Z à inspecter :", liste_z)
            
            # Extraction des données de la ligne sélectionnée
            infos_z = st.session_state.historique_z[st.session_state.historique_z['Ref_Z'] == z_choisi].iloc[0]
            
            # Reconstruction dynamique du format ticket
            ticket_reconstruit = f"""
            <div style="border:1px solid #000; padding:15px; background-color:#fff; color:#000; font-family:'Courier New', Courier, monospace; max-width:320px; margin:10px auto; font-size:13px; line-height:1.2;">
                <h3 style="text-align:center; margin:0 0 5px 0; font-size:16px;">*** EASYGEST RESTO ***</h3>
                <h4 style="text-align:center; margin:0 0 10px 0; font-size:14px;">RÉÉDITION LOG ARCHIVE</h4>
                <p><b>REF TICKET :</b> {infos_z['Ref_Z']}</p>
                <p><b>DATE     :</b> {infos_z['Date_Cloture']}</p>
                <p><b>CAISSIER :</b> {infos_z['Caissier']}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <table style="width:100%; font-size:13px;">
                    <tr><td>RECETTE TOTALE :</td><td style="text-align:right; font-weight:bold;">{float(infos_z['Recette_Encaissee']):,.0f} F</td></tr>
                    <tr><td>ARTICLES VENDUS:</td><td style="text-align:right;">{infos_z['Articles_Vendus']} pcs</td></tr>
                    <tr><td>TABLES CLÔTURE :</td><td style="text-align:right;">{infos_z['Tables_Servies']}</td></tr>
                    <tr><td>FOND DE CAISSE :</td><td style="text-align:right;">{float(infos_z['Fond_De_Caisse']):,.0f} F</td></tr>
                </table>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <p><b>OBSERVATIONS :</b><br>{infos_z['Observations']}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <h4 style="text-align:center; margin:5px 0 0 0; font-size:11px;">DUPLICATA ADMINISTRATEUR</h4>
            </div>
            """
            st.markdown(ticket_reconstruit, unsafe_allow_html=True)
            
            if st.button("🖨️ Lancer la réimpression du duplicata", type="secondary", use_container_width=True):
                js_reprint = f"""
                <script>
                    var w = window.open('', '_blank', 'height=600,width=400');
                    w.document.write('<html><body>');
                    w.document.write(`{ticket_reconstruit}`);
                    w.document.write('</body></html>');
                    w.document.close();
                    setTimeout(function() {{ w.print(); w.close(); }}, 300);
                </script>
                """
                components.html(js_reprint, height=0, width=0)

    with tab_purge:
        if st.checkbox("Activer l'option de réinitialisation générale"):
            if st.button("🚨 VIDER LE JOURNAL DES OPÉRATIONS", type="primary"):
                st.session_state.historique_ventes = pd.DataFrame(columns=['Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon'])
                st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
                st.rerun()

# ==========================================
# 🛑 MIRE DE CONNEXION PRINCIPALE
# ==========================================
if not st.session_state.authentifie:
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("🔑 Connexion - Easygest Resto Pro+")
        role_selectionne = st.selectbox("Sélectionnez votre profil d'accès :", ["Serveur", "Responsable Caisse", "Administrateur"])
        mot_de_passe = st.text_input("Saisissez le mot de passe d'authentification :", type="password")
        
        if st.button("Se connecter 🔓", use_container_width=True, type="primary"):
            if role_selectionne == "Serveur" and mot_de_passe == "serveur123":
                st.session_state.authentifie = True
                st.session_state.role_utilisateur = "Serveur"
                st.rerun()
            elif role_selectionne == "Responsable Caisse" and mot_de_passe == "caisse123":
                st.session_state.authentifie = True
                st.session_state.role_utilisateur = "Responsable Caisse"
                st.rerun()
            elif role_selectionne == "Administrateur" and mot_de_passe == "admin123":
                st.session_state.authentifie = True
                st.session_state.role_utilisateur = "Administrateur"
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")
else:
    # ==========================================
    # 📊 ROUTAGE DYNAMIQUE ET BARRE LATÉRALE
    # ==========================================
    st.sidebar.title("🍳 Easygest Resto Pro+")
    st.sidebar.markdown(f"👤 Connecté : **{st.session_state.role_utilisateur}**")
    st.sidebar.markdown("---")

    options_autorisees = OPTIONS_PAR_ROLE[st.session_state.role_utilisateur]
    choix_menu = st.sidebar.radio("Navigation Principale :", options_autorisees, index=len(options_autorisees)-1 if st.session_state.role_utilisateur == "Administrateur" else 0)

    st.sidebar.markdown("---")
    if st.sidebar.button("Déconnexion 🚪", type="secondary", use_container_width=True):
        st.session_state.authentifie = False
        st.session_state.role_utilisateur = None
        st.rerun()

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
        vue_administrateur()
