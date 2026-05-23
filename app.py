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
    return chemin_cible

DOSSIER_EXPLOITATION = initialiser_dossier_easygest()
CSV_MENU = os.path.join(DOSSIER_EXPLOITATION, "easygest_base_menu.csv")
CSV_VENTES = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_ventes.csv")
CSV_BONS = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_bons.csv")
CSV_Z_HISTORIQUE = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_z.csv")
CSV_UTILISATEURS = os.path.join(DOSSIER_EXPLOITATION, "easygest_utilisateurs.csv")

def initialiser_fichiers_csv():
    if not os.path.exists(CSV_MENU):
        pd.DataFrame({'Code_Article': ['MENU001'], 'Designation': ['Exemple'], 'Categorie': ['Cuisine'], 'Stock_Initial': [0], 'Stock_Minimum': [5], 'Prix_Vente_FCFA': [0], 'Prix_Achat_Moyen_FCFA': [0]}).to_csv(CSV_MENU, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_VENTES):
        pd.DataFrame(columns=['Heure', 'Table', 'Code_Article', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon']).to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_BONS):
        pd.DataFrame(columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur']).to_csv(CSV_BONS, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_Z_HISTORIQUE):
        # AJOUT DES COLONNES POUR LE SUIVI DES ÉCARTS DANS L'HISTORIQUE Z
        pd.DataFrame(columns=['Ref_Z', 'Date_Cloture', 'Caissier', 'Recette_Encaissee', 'Montant_Verse', 'Ecart_Caisse', 'Articles_Vendus', 'Tables_Servies', 'Fond_De_Caisse', 'Observations']).to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_UTILISATEURS):
        pd.DataFrame({'Identifiant': ['admin', 'serveur1'], 'Mot_De_Passe': ['admin123', 'pass123'], 'Role': ['Administrateur', 'Serveur']}).to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')

initialiser_fichiers_csv()

if 'base_menu' not in st.session_state: st.session_state.base_menu = pd.read_csv(CSV_MENU)
if 'historique_ventes' not in st.session_state: st.session_state.historique_ventes = pd.read_csv(CSV_VENTES)
if 'historique_z' not in st.session_state: st.session_state.historique_z = pd.read_csv(CSV_Z_HISTORIQUE)
if 'base_utilisateurs' not in st.session_state: st.session_state.base_utilisateurs = pd.read_csv(CSV_UTILISATEURS)

if 'historique_bons' not in st.session_state:
    df_b = pd.read_csv(CSV_BONS)
    st.session_state.historique_bons = {}
    for _, r in df_b.iterrows():
        st.session_state.historique_bons[r['Ref_Bon']] = {'Date': r['Date'], 'Type': r['Type'], 'Article': r['Article'], 'Quantite': r['Quantite'], 'Prix_Unitaire': r['Prix_Unitaire'], 'Total': r['Total'], 'Fournisseur': r['Fournisseur']}

# Vues & Rôles
if 'authentifie' not in st.session_state: st.session_state.authentifie = False
if 'role_utilisateur' not in st.session_state: st.session_state.role_utilisateur = None
if 'nom_utilisateur' not in st.session_state: st.session_state.nom_utilisateur = None

OPTIONS_PAR_ROLE = {
    "Serveur": ["📝 Prise de Commande"],
    "Responsable Caisse": ["📝 Prise de Commande", "🧾 Commandes & Additions", "📦 Stocks & Approvisionnements", "🔒 Clôture de Caisse"],
    "Administrateur": ["📝 Prise de Commande", "🧾 Commandes & Additions", "📦 Stocks & Approvisionnements", "📊 Finances & Marges", "🔒 Clôture de Caisse", "⚙️ Configuration Carte"]
}

def sauvegarder_menu(): st.session_state.base_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')
def sauvegarder_ventes(): st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
def sauvegarder_z_historique(): st.session_state.historique_z.to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')
def sauvegarder_bons():
    liste_bons = [{'Ref_Bon': k, **v} for k, v in st.session_state.historique_bons.items()]
    pd.DataFrame(liste_bons if liste_bons else columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur']).to_csv(CSV_BONS, index=False, encoding='utf-8-sig')

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
# FONCTIONS DES DIFFÉRENTES VUES
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide")
    if len(st.session_state.base_menu) == 0 or (len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base_menu.iloc[0]['Designation']):
        st.warning("⚠️ La carte est vide. Utilisez l'accès Admin pour la configurer.")
        return
    col1, col2 = st.columns([2, 1])
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
        st.info(f"👤 Connecté : **{st.session_state.nom_utilisateur}**\n\nRôle : `{st.session_state.role_utilisateur}`")

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
            df_table_strict['Désignation Produit'] = df_table_strict.apply(lambda r: f"{r['Designation']} (+ {r['Accompagnement']})" if pd.notna(r['Accompagnement']) and r['Accompagnement'] not in ["-", "Sans"] else r['Designation'], axis=1)
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Désignation Produit', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Total_FCFA']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser et Clôturer la {table_selectionnee} 💰", type="primary"):
                st.session_state.historique_ventes.loc[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours'), 'Statut'] = 'Payé'
                sauvegarder_ventes()
                st.success(f"La {table_selectionnee} a été validée avec succès !")
                st.rerun()
            if col_btn2.button(f"Annuler l'addition de la {table_selectionnee} ❌"):
                st.session_state.historique_ventes.loc[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours'), 'Statut'] = 'Annulé'
                sauvegarder_ventes()
                st.warning(f"Commandes de la {table_selectionnee} annulées.")
                st.rerun()
    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Bons d'Entrée")
    tab_cuisine, tab_bar, tab_bons = st.tabs(["🍳 Stock CUISINE", "🍹 Stock BAR", "📄 Bons d'Entrée Valorisés"])
    with tab_cuisine:
        df_cuisine = df_global[df_global['Categorie'] == 'Cuisine']
        st.dataframe(df_cuisine[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)
    with tab_bar:
        df_bar = df_global[df_global['Categorie'] == 'Bar']
        st.dataframe(df_bar[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum', 'Prix_Vente_FCFA']], use_container_width=True, hide_index=True)

def vue_finances_marges():
    st.subheader("📊 Compte d'Exploitation & Rentabilité Réelle")
    df_ventes_payees = st.session_state.historique_ventes[(st.session_state.historique_ventes['Type_Flux'] == 'Sortie') & (st.session_state.historique_ventes['Statut'] == 'Payé')]
    if df_ventes_payees.empty:
        st.info("Les données financières apparaîtront après les premiers encaissements.")
        return
    df_calc_marge = df_ventes_payees.groupby('Code_Article').agg({'Quantite': 'sum', 'Total_FCFA': 'sum'}).reset_index()
    df_calc_marge = df_calc_marge.merge(st.session_state.base_menu[['Code_Article', 'Designation', 'Prix_Achat_Moyen_FCFA']], on='Code_Article', how='left')
    df_calc_marge['Cout_Total_Achat'] = df_calc_marge['Quantite'] * df_calc_marge['Prix_Achat_Moyen_FCFA'].fillna(0)
    df_calc_marge['Marge_Brute_FCFA'] = df_calc_marge['Total_FCFA'] - df_calc_marge['Cout_Total_Achat']
    ca_total = df_calc_marge['Total_FCFA'].sum()
    cout_achats_total = df_calc_marge['Cout_Total_Achat'].sum()
    marge_globale = df_calc_marge['Marge_Brute_FCFA'].sum()
    taux_marge_global = (marge_globale / ca_total) * 100 if ca_total > 0 else 0
    f1, f2, f3 = st.columns(3)
    f1.metric("Chiffre d'Affaires Net Encaissé", f"{ca_total:,.0f} FCFA")
    f2.metric("Coût des Matières (Achats)", f"{cout_achats_total:,.0f} FCFA")
    f3.metric("Marge Réelle nette", f"{marge_globale:,.0f} FCFA", delta=f"{taux_marge_global:.1f}% de marge")

# ==========================================
# 🔒 VUE 5 : CLÔTURE DE CAISSE (PERSONNALISÉE)
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
    c1.metric("Recette Encaissée Théorique (FCFA)", f"{ca_brut:,.0f} F")
    c2.metric("Total Articles Vendus", f"{nb_couverts} pcs")
    c3.metric("Nombre de Tables Servies", f"{nb_tables}")
    c4.metric("Panier Moyen / Table", f"{panier_moyen:,.0f} F")
    
    if not df_jour_en_cours.empty:
        st.warning(f"⚠️ **Clôture impossible :** Il reste **{len(df_jour_en_cours)} table(s) en cours** non soldée(s).")
        return

    st.info("💡 Le système est prêt pour l'édition, l'archivage numérique et l'impression du Z.")
    
    # --- ZONE DE PERSONNALISATION DEMANDÉE ---
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        fond_de_caisse = st.number_input("Montant de fond de caisse laissé (FCFA) :", min_value=0, value=15000, key="cloture_fond")
        nom_caissier = st.text_input("Nom du caissier responsable :", value=st.session_state.nom_utilisateur if st.session_state.nom_utilisateur else "", key="cloture_user")
    
    with col_input2:
        # Nouveau champ pour le montant physique versé à la fin de l'exercice
        montant_verse = st.number_input("💰 Montant PHYSIQUE Réellement Versé (FCFA) :", min_value=0, value=int(ca_brut), step=500, key="cloture_verse")
        
        # Calcul automatique de l'écart de caisse
        ecart = montant_verse - ca_brut
        if ecart == 0:
            st.success("✅ Caisse Parfaite : Aucun écart détecté.")
        elif ecart < 0:
            st.error(f"🚨 Manquant de Caisse : {ecart:,.0f} FCFA (Argent insuffisant en caisse !)")
        else:
            st.warning(f"💵 Surplus de Caisse : +{ecart:,.0f} FCFA")
    # ----------------------------------------

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
                'Montant_Verse': montant_verse, # Sauvegarde du montant versé
                'Ecart_Caisse': ecart,           # Sauvegarde de l'écart
                'Articles_Vendus': nb_couverts,
                'Tables_Servies': nb_tables,
                'Fond_De_Caisse': fond_de_caisse,
                'Observations': remarques if remarques else "Aucune"
            }])
            st.session_state.historique_z = pd.concat([st.session_state.historique_z, nouvel_index_z], ignore_index=True)
            sauvegarder_z_historique()
            
            # Intégration des nouvelles données dans le modèle HTML du ticket thermique
            ticket_html = f"""
            <div id="thermal-z-ticket" style="border:1px dashed #000; padding:15px; background-color:#fff; color:#000; font-family:'Courier New', Courier, monospace; max-width:320px; margin:auto; font-size:13px; line-height:1.2;">
                <h3 style="text-align:center; margin:0 0 5px 0; font-size:16px;">*** EASYGEST RESTO ***</h3>
                <h4 style="text-align:center; margin:0 0 10px 0; font-size:14px;">TICKET Z DE CLÔTURE</h4>
                <p><b>REF TICKET :</b> {ref_z}</p>
                <p><b>DATE      :</b> {date_courante}</p>
                <p><b>CAISSIER :</b> {nom_caissier}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <table style="width:100%; font-size:13px;">
                    <tr><td>RECETTE THEORIQUE:</td><td style="text-align:right;">{ca_brut:,.0f} F</td></tr>
                    <tr><td>MONTANT VERSE    :</td><td style="text-align:right; font-weight:bold;">{montant_verse:,.0f} F</td></tr>
                    <tr><td>ECART DE CAISSE  :</td><td style="text-align:right; color:{'red' if ecart < 0 else 'black'}; font-weight:bold;">{ecart:,.0f} F</td></tr>
                    <tr style="height:10px;"><td></td><td></td></tr>
                    <tr><td>ARTICLES VENDUS  :</td><td style="text-align:right;">{nb_couverts} pcs</td></tr>
                    <tr><td>TABLES CLÔTURE   :</td><td style="text-align:right;">{nb_tables}</td></tr>
                    <tr><td>FOND DE CAISSE   :</td><td style="text-align:right;">{fond_de_caisse:,.0f} F</td></tr>
                </table>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <p><b>OBSERVATIONS :</b><br>{remarques if remarques else 'Aucune'}</p>
                <hr style="border-top: 1px dashed #000; margin:10px 0;">
                <h4 style="text-align:center; margin:10px 0 0 0;">FIN DE SERVICE ARCHIVÉE</h4>
            </div>
            """
            
            st.success(f"🎉 Le rapport numérique {ref_z} a bien été archivé de manière sécurisée !")
            st.markdown("### 🖨️ Aperçu du Ticket")
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

def vue_configuration_carte():
    st.subheader("⚙️ Configuration de la Carte")
    action = st.radio("Sélectionnez une action :", ["➕ Ajouter un Nouveau Produit", "✏️ Modifier un Produit Existant"])
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
                    st.session_state.base_menu = pd.concat([st.session_state.base_menu, pd.DataFrame([{'Code_Article': new_code, 'Designation': new_designation, 'Categorie': new_categorie, 'Stock_Initial': new_stock_init, 'Stock_Minimum': new_stock_min, 'Prix_Vente_FCFA': new_prix_vente, 'Prix_Achat_Moyen_FCFA': new_prix_achat}])], ignore_index=True)
                    sauvegarder_menu()
                    st.success("Article ajouté !")
                    st.rerun()
    elif action == "✏️ Modifier un Produit Existant":
        if not st.session_state.base_menu.empty:
            dict_edit = {r['Designation']: r['Code_Article'] for _, r in st.session_state.base_menu.iterrows()}
            prod = st.selectbox("Sélectionner le produit à modifier :", list(dict_edit.keys()))
            code = dict_edit[prod]
            infos = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code].iloc[0]
            with st.form("form_edit"):
                edit_name = st.text_input("Nom du produit :", value=infos['Designation'])
                edit_cat = st.selectbox("Famille :", ["Cuisine", "Bar"], index=0 if infos['Categorie']=='Cuisine' else 1)
                edit_px_v = st.number_input("Prix de Vente (FCFA) :", min_value=0, value=int(infos['Prix_Vente_FCFA']))
                edit_px_a = st.number_input("Prix d'Achat (FCFA) :", min_value=0, value=int(infos['Prix_Achat_Moyen_FCFA']))
                if st.form_submit_button("✏️ Enregistrer les modifications"):
                    idx = st.session_state.base_menu[st.session_state.base_menu['Code_Article'] == code].index
                    st.session_state.base_menu.loc[idx, ['Designation', 'Categorie', 'Prix_Vente_FCFA', 'Prix_Achat_Moyen_FCFA']] = [edit_name, edit_cat, edit_px_v, edit_px_a]
                    sauvegarder_menu()
                    st.success("Produit mis à jour !")
                    st.rerun()

# ==========================================
# POINT D'ENTRÉE MAIN
# ==========================================
def main():
    if not st.session_state.authentifie:
        st.title("🔑 Connexion - Easygest Resto Pro+")
        with st.form("login_form"):
            user_input = st.text_input("Identifiant :")
            password_input = st.text_input("Mot de passe :", type="password")
            if st.form_submit_button("Se connecter"):
                df_u = st.session_state.base_utilisateurs
                valid_user = df_u[(df_u['Identifiant'] == user_input) & (df_u['Mot_De_Passe'] == password_input)]
                if not valid_user.empty:
                    st.session_state.authentifie = True
                    st.session_state.role_utilisateur = valid_user.iloc[0]['Role']
                    st.session_state.nom_utilisateur = valid_user.iloc[0]['Identifiant']
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
    else:
        st.sidebar.title("🍳 Menu Navigation")
        options_disponibles = OPTIONS_PAR_ROLE.get(st.session_state.role_utilisateur, ["📝 Prise de Commande"])
        choix = st.sidebar.radio("Aller vers :", options_disponibles)
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Déconnexion"):
            st.session_state.authentifie = False
            st.rerun()
            
        if choix == "📝 Prise de Commande": vue_prise_commande()
        elif choix == "🧾 Commandes & Additions": vue_commandes_additions()
        elif choix == "📦 Stocks & Approvisionnements": vue_stocks_appro()
        elif choix == "📊 Finances & Marges": vue_finances_marges()
        elif choix == "🔒 Clôture de Caisse": vue_cloture_caisse()
        elif choix == "⚙️ Configuration Carte": vue_configuration_carte()

if __name__ == "__main__":
    main()
