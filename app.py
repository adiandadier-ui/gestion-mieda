import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
# 0. FONCTION DE CALIBRAGE & LISTE DES MATIÈRES PREMIÈRES
# ==========================================
MATIERES_PREMIERES_CIBLES = [
    "PETIT POISSON", 
    "MOYEN POISSON", 
    "GROS POISSON", 
    "POULET", 
    "LAPIN", 
    "PINTADE"
]

def determiner_matiere_premiere(nom_article, prix_unitaire):
    """
    Détermine le libellé exact de la matière première en stock à impacter
    en fonction du nom de l'article ou de sa tranche de prix pour les poissons.
    """
    nom_article_up = str(nom_article).upper().strip()
    
    # --- CAS DES POISSONS ---
    if "POISSON" in nom_article_up:
        if prix_unitaire == 2000:
            return "PETIT POISSON"
        elif prix_unitaire == 4000:
            return "MOYEN POISSON"
        elif prix_unitaire == 6000:
            return "GROS POISSON"
        else:
            if "PETIT" in nom_article_up: return "PETIT POISSON"
            if "MOYEN" in nom_article_up: return "MOYEN POISSON"
            if "GROS" in nom_article_up: return "GROS POISSON"
            return None
            
    # --- AUTRES VIANDES ---
    elif "POULET" in nom_article_up:
        return "POULET"
    elif "LAPIN" in nom_article_up:
        return "LAPIN"
    elif "PINTADE" in nom_article_up:
        return "PINTADE"
        
    return None

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
            'Heure', 'Table', 'Code_Article', 'Code_Matiere_Stock', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 
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
            'Ref_Z', 'Date_Cloture', 'Caissier', 'Recette_Encaissee', 'Montant_Verse', 'Ecart_Caisse', 
            'Articles_Vendus', 'Tables_Servies', 'Fond_De_Caisse', 'Observations'
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

if 'base_menu' not in st.session_state:
    st.session_state.base_menu = pd.read_csv(CSV_MENU)

if 'historique_ventes' not in st.session_state:
    st.session_state.historique_ventes = pd.read_csv(CSV_VENTES)
    if 'Code_Matiere_Stock' not in st.session_state.historique_ventes.columns:
        st.session_state.historique_ventes['Code_Matiere_Stock'] = st.session_state.historique_ventes['Code_Article']

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
# 3. GESTION DES SAUVEGARDES ET STOCKS
# ==========================================
def sauvegarder_utilisateurs():
    st.session_state.base_utilisateurs.to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')

def sauvegarder_menu():
    st.session_state.base_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')

def sauvegarder_ventes():
    st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')

def sauvegarder_bons():
    liste_bons = [{'Ref_Bon': k, **v} for k, v in st.session_state.historique_bons.items()]
    if liste_bons:
        pd.DataFrame(liste_bons).to_csv(CSV_BONS, index=False, encoding='utf-8-sig')
    else:
        pd.DataFrame(columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur']).to_csv(CSV_BONS, index=False, encoding='utf-8-sig')

def sauvegarder_z_historique():
    st.session_state.historique_z.to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')

def consolider_stocks_et_marges():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    
    if not df_vnt.empty:
        df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Code_Matiere_Stock')['Quantite'].sum().reset_index(name='Total_Sorties')
        df_sorties.rename(columns={'Code_Matiere_Stock': 'Code_Article'}, inplace=True)
        
        df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Code_Matiere_Stock')['Quantite'].sum().reset_index(name='Total_Entrees')
        df_entrees.rename(columns={'Code_Matiere_Stock': 'Code_Article'}, inplace=True)
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
# 4. GESTION DE L'AUTHENTIFICATION
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

if not st.session_state.authentifie:
    st.title("🔑 Connexion Easygest Resto Pro+")
    identifiant_input = st.text_input("Identifiant :")
    mot_de_passe_input = st.text_input("Mot de passe :", type="password")
    
    if st.button("Se connecter 🚀", use_container_width=True):
        utilisateurs = st.session_state.base_utilisateurs
        match = utilisateurs[(utilisateurs['Identifiant'] == identifiant_input) & (utilisateurs['Mot_De_Passe'] == mot_de_passe_input)]
        
        if not match.empty:
            st.session_state.authentifie = True
            st.session_state.role_utilisateur = match.iloc[0]['Role']
            st.session_state.nom_utilisateur = match.iloc[0]['Identifiant']
            st.success("Connexion réussie !")
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect.")
    st.stop()

# ==========================================
# 5. NAVIGATION PRINCIPALE (SIDEBAR)
# ==========================================
st.sidebar.title("🍳 Menu Easygest")
options_disponibles = OPTIONS_PAR_ROLE.get(st.session_state.role_utilisateur, ["📝 Prise de Commande"])
choix_vue = st.sidebar.radio("Navigation :", options_disponibles)

if st.sidebar.button("Déconnexion 🚪", use_container_width=True):
    st.session_state.authentifie = False
    st.session_state.role_utilisateur = None
    st.session_state.nom_utilisateur = None
    st.rerun()

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
            designation_upper = str(r['Designation']).upper().strip()
            
            if designation_upper in MATIERES_PREMIERES_CIBLES:
                continue
                
            label = f"[{r['Categorie']}] {r['Designation']} ({int(r['Prix_Vente_FCFA'])} FCFA)"
            dict_menu[label] = r['Code_Article']
            dict_categories[label] = r['Categorie']

        if not dict_menu:
            st.info("Aucun plat commercialisable configuré pour le moment.")
            return

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
                code_art_fini = dict_menu[item_choisi]
                item_details = df_global[df_global['Code_Article'] == code_art_fini].iloc[0]
                
                nom_matiere_brute = determiner_matiere_premiere(item_details['Designation'], item_details['Prix_Vente_FCFA'])
                
                code_article_a_deduire = code_art_fini
                target_details = item_details
                
                if nom_matiere_brute:
                    match_brute = df_global[df_global['Designation'].str.upper().str.strip() == nom_matiere_brute.upper()]
                    if not match_brute.empty:
                        code_article_a_deduire = match_brute.iloc[0]['Code_Article']
                        target_details = match_brute.iloc[0]
                    else:
                        st.error(f"❌ Erreur : L'ingrédient de base '{nom_matiere_brute}' n'existe pas en stock.")
                        st.stop()

                if quantite > target_details['Quantite_Dispo']:
                    st.error(f"❌ Stock insuffisant ! (Disponible en {target_details['Designation']} : {target_details['Quantite_Dispo']} pcs)")
                else:
                    total_net = (quantite * item_details['Prix_Vente_FCFA']) * (1 - (opt_remise / 100))
                    
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                        'Table': table_choisie, 
                        'Code_Article': code_art_fini, 
                        'Code_Matiere_Stock': code_article_a_deduire, 
                        'Type_Flux': 'Sortie', 
                        'Quantite': quantite, 
                        'Prix_Unitaire_Flux': item_details['Prix_Vente_FCFA'], 
                        'Remise_Pourcent': opt_remise, 
                        'Accompagnement': accomp_choisi, 
                        'Total_FCFA': total_net,
                        'Motif_Remise': motif_remise, 
                        'Statut': 'En cours', 
                        'Ref_Bon': '-'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    sauvegarder_ventes()
                    st.success(f"Commande envoyée ! Plat enregistré : {item_details['Designation']}")
                    st.rerun()
    with col2:
        st.info(f"👤 Connecté en tant que : **{st.session_state.nom_utilisateur}** ({st.session_state.role_utilisateur})")

# ==========================================
# VUE 2 : COMMANDES & ADDITIONS
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
                designation = row['Designation'] if pd.notna(row['Designation']) else "Produit Inconnu"
                if row['Accompagnement'] != "-" and row['Accompagnement'] != "Sans" and pd.notna(row['Accompagnement']):
                    return f"{designation} (+ {row['Accompagnement']})"
                return designation
                
            df_table_strict['Désignation Produit'] = df_table_strict.apply(formater_libelle, axis=1)
            st.dataframe(df_table_strict[['Heure', 'Categorie', 'Désignation Produit', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Total_FCFA']], use_container_width=True, hide_index=True)
            total_addition = df_table_strict['Total_FCFA'].sum()
            st.markdown(f"## **Total Net à Payer : {total_addition:,.0f} FCFA**")
            
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Encaisser la {table_selectionnee} 💰", type="primary"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Payé'
                sauvegarder_ventes()
                st.success(f"La {table_selectionnee} a été réglée !")
                st.rerun()
                
            if col_btn2.button(f"Annuler la {table_selectionnee} ❌"):
                indices_table = st.session_state.historique_ventes[(st.session_state.historique_ventes['Table'] == table_selectionnee) & (st.session_state.historique_ventes['Statut'] == 'En cours')].index
                st.session_state.historique_ventes.loc[indices_table, 'Statut'] = 'Annulé'
                sauvegarder_ventes()
                st.warning(f"Commandes annulées.")
                st.rerun()

    with tabs_caisse[1]:
        st.dataframe(df_suivi.sort_index(ascending=False), use_container_width=True, hide_index=True)

# ==========================================
# VUE 3 : STOCKS & APPROS
# ==========================================
def vue_stocks_appro():
    st.subheader("📦 Gestion des Stocks & Bons d'Entrée")
    tab_cuisine, tab_bar, tab_bons = st.tabs(["🍳 Stock CUISINE (Ingrédients)", "🍹 Stock BAR (Boissons)", "📄 Bons d'Entrée Valorisés"])
    
    with tab_cuisine:
        df_cuisine_brut = df_global[df_global['Categorie'] == 'Cuisine'].copy()
        df_cuisine = df_cuisine_brut[df_cuisine_brut['Designation'].str.upper().str.strip().isin(MATIERES_PREMIERES_CIBLES)]
        
        if df_cuisine.empty:
            st.info("Aucune matière première brute n'est détectée dans votre base de données cuisine.")
        else:
            st.dataframe(df_cuisine[['Code_Article', 'Designation', 'Stock_Initial', 'Total_Entrees', 'Total_Sorties', 'Quantite_Dispo', 'Stock_Minimum']], use_container_width=True, hide_index=True)
        
        with st.expander("📥 Enregistrer un Achat / Approvisionnement Cuisine"):
            if df_cuisine.empty:
                st.info("Configurez d'abord vos matières premières dans l'onglet Configuration Carte.")
            else:
                with st.form("form_appro_cuisine", clear_on_submit=True):
                    dict_cuisine = {r['Designation']: r['Code_Article'] for _, r in df_cuisine.iterrows()}
                    art_choisi = st.selectbox("Ingrédient Cuisine reçu :", list(dict_cuisine.keys()))
                    qte_recue = st.number_input("Quantité achetée :", min_value=1, value=10)
                    px_achat_unit = st.number_input("Prix d'Achat UNITAIRE (FCFA) :", min_value=0, value=1000)
                    fournisseur = st.text_input("Nom du Fournisseur :", value="Grossiste Marché")
                    
                    if st.form_submit_button("Générer le Bon d'Entrée Cuisine 📑"):
                        code_r = dict_cuisine[art_choisi]
                        ref_bon = f"BON-CUI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                        
                        ligne_appro = pd.DataFrame([{
                            'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': 'APPRO_CUISINE', 'Code_Article': code_r,
                            'Code_Matiere_Stock': code_r, 'Type_Flux': 'Réappro', 'Quantite': qte_recue, 'Prix_Unitaire_Flux': px_achat_unit,
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
                        st.success(f"Bon {ref_bon} enregistré !")
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
                            'Code_Matiere_Stock': code_r, 'Type_Flux': 'Réappro', 'Quantite': qte_recue_bar, 'Prix_Unitaire_Flux': px_achat_unit_bar,
                            'Remise_Pourcent': 0, 'Accompagnement': '-', 
                            'Total_FCFA': qte_recue_bar * px_achat_unit_bar, 'Motif_Remise': 'Aucun', 'Statut': 'Stocké', 'Ref_Bon': ref_bon
                        }])
                        st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, ligne_appro], ignore_index=True)
                        idx = st.session_state.
