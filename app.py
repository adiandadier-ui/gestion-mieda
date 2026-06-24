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
    "PINTADE",
    "PORTION SAUCE",
    "LIQUEUR"
]

def determiner_matiere_premiere(nom_article, prix_unitaire):
    """
    Détermine dynamiquement la matière première en stock ainsi que le coefficient 
    de décalquage (gère TOURNEE, TRNÉE, TRNEE, DEMI, ENTIERE).
    """
    nom_article_up = str(nom_article).upper().strip()
    
    # --- CAS DES PLATS ACCOMPAGNÉS DE SAUCE ---
    if "SAUCE" in nom_article_up:
        return "PORTION SAUCE", 1.0 / 15.0

    # --- CAS DES FORMATS DE VENTE DE LIQUEURS (Prise en compte de TRNÉE / TRNEE) ---
    est_un_verre = "TOURNEE" in nom_article_up or "TRNÉE" in nom_article_up or "TRNEE" in nom_article_up
    est_un_demi  = "DEMI" in nom_article_up
    est_entiere  = "ENTIERE" in nom_article_up or "BOUTEILLE" in nom_article_up

    if est_un_verre or est_un_demi or est_entiere:
        if 'base_menu' in st.session_state and not st.session_state.base_menu.empty:
            tous_les_articles = st.session_state.base_menu['Designation'].tolist()
            liqueurs_en_stock = [str(art).upper().strip() for art in tous_les_articles if "LIQUEUR" in str(art).upper()]
            
            for liqueur_brute in liqueurs_en_stock:
                # On extrait la marque nettoyée (ex: "HAMWICK")
                marque = liqueur_brute.replace("LIQUEUR", "").strip()
                
                if marque and marque in nom_article_up:
                    if est_un_verre: return liqueur_brute, 0.04
                    elif est_un_demi: return liqueur_brute, 0.50
                    elif est_entiere: return liqueur_brute, 1.00

    # --- CAS DES POISSONS ---
    if "POISSON" in nom_article_up:
        coef = 1.0
        if prix_unitaire == 2000: return "PETIT POISSON", coef
        elif prix_unitaire == 4000: return "MOYEN POISSON", coef
        elif prix_unitaire == 6000: return "GROS POISSON", coef
        else:
            if "PETIT" in nom_article_up: return "PETIT POISSON", coef
            if "MOYEN" in nom_article_up: return "MOYEN POISSON", coef
            if "GROS" in nom_article_up: return "GROS POISSON", coef
            return None, 0.0
            
    # --- CAS DES VIANDES ---
    base_viande = None
    if "POULET" in nom_article_up: base_viande = "POULET"
    elif "LAPIN" in nom_article_up: base_viande = "LAPIN"
    elif "PINTADE" in nom_article_up: base_viande = "PINTADE"

    if base_viande:
        if "1/4" in nom_article_up or "QUART" in nom_article_up: return base_viande, 0.25
        elif "1/2" in nom_article_up or "DEMI" in nom_article_up: return base_viande, 0.50
        else: return base_viande, 1.0
        
    return None, 0.0

# ==========================================
# 1. CONFIGURATION DE L'INTERFACE
# ==========================================
st.set_page_config(page_title="Easygest Resto Pro+", page_icon="🍳", layout="wide")

# ==========================================
# 2. INITIALISATION ET STOCKAGE LOCAL (C:)
# ==========================================
def initialiser_dossier_easygest():
    chemin_cible = r"C:\EASYGEST APPS"
    if not os.path.exists(chemin_cible):
        try:
            os.makedirs(chemin_cible)
        except Exception:
            chemin_cible = os.path.join(os.getcwd(), "EASYGEST_APPS_LOCAL")
            if not os.path.exists(chemin_cible): os.makedirs(chemin_cible)
    return chemin_cible

DOSSIER_EXPLOITATION = initialiser_dossier_easygest()
CSV_MENU = os.path.join(DOSSIER_EXPLOITATION, "easygest_base_menu.csv")
CSV_VENTES = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_ventes.csv")
CSV_BONS = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_bons.csv")
CSV_Z_HISTORIQUE = os.path.join(DOSSIER_EXPLOITATION, "easygest_historique_z.csv")
CSV_UTILISATEURS = os.path.join(DOSSIER_EXPLOITATION, "easygest_utilisateurs.csv")

def initialiser_fichiers_csv():
    if not os.path.exists(CSV_MENU):
        pd.DataFrame({'Designation': ['Exemple'], 'Categorie': ['Cuisine'], 'Stock_Initial': [0], 'Stock_Minimum': [5], 'Prix_Vente_FCFA': [0], 'Prix_Achat_Moyen_FCFA': [0]}).to_csv(CSV_MENU, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_VENTES):
        pd.DataFrame(columns=['Heure', 'Table', 'Designation', 'Matiere_Stock', 'Type_Flux', 'Quantite', 'Prix_Unitaire_Flux', 'Remise_Pourcent', 'Accompagnement', 'Total_FCFA', 'Motif_Remise', 'Statut', 'Ref_Bon']).to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_BONS):
        pd.DataFrame(columns=['Ref_Bon', 'Date', 'Type', 'Article', 'Quantite', 'Prix_Unitaire', 'Total', 'Fournisseur']).to_csv(CSV_BONS, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_Z_HISTORIQUE):
        pd.DataFrame(columns=['Ref_Z', 'Date_Cloture', 'Caissier', 'Recette_Encaissee', 'Montant_Verse', 'Ecart_Caisse', 'Articles_Vendus', 'Tables_Servies', 'Fond_De_Caisse', 'Observations']).to_csv(CSV_Z_HISTORIQUE, index=False, encoding='utf-8-sig')
    if not os.path.exists(CSV_UTILISATEURS):
        pd.DataFrame({'Identifiant': ['admin'], 'Mot_De_Passe': ['admin123'], 'Role': ['Administrateur']}).to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')

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

def sauvegarder_utilisateurs(): st.session_state.base_utilisateurs.to_csv(CSV_UTILISATEURS, index=False, encoding='utf-8-sig')
def sauvegarder_menu(): st.session_state.base_menu.to_csv(CSV_MENU, index=False, encoding='utf-8-sig')
def sauvegarder_ventes(): st.session_state.historique_ventes.to_csv(CSV_VENTES, index=False, encoding='utf-8-sig')

def consolider_stocks_et_marges():
    df_art = st.session_state.base_menu.copy()
    df_vnt = st.session_state.historique_ventes.copy()
    if not df_vnt.empty:
        df_sorties = df_vnt[(df_vnt['Type_Flux'] == 'Sortie') & (df_vnt['Statut'] != 'Annulé')].groupby('Matiere_Stock')['Quantite'].sum().reset_index(name='Total_Sorties').rename(columns={'Matiere_Stock': 'Designation'})
        df_entrees = df_vnt[df_vnt['Type_Flux'] == 'Réappro'].groupby('Matiere_Stock')['Quantite'].sum().reset_index(name='Total_Entrees').rename(columns={'Matiere_Stock': 'Designation'})
    else:
        df_sorties, df_entrees = pd.DataFrame(columns=['Designation', 'Total_Sorties']), pd.DataFrame(columns=['Designation', 'Total_Entrees'])
    df_res = df_art.merge(df_sorties, on='Designation', how='left').merge(df_entrees, on='Designation', how='left')
    df_res['Total_Sorties'] = df_res['Total_Sorties'].fillna(0)
    df_res['Total_Entrees'] = df_res['Total_Entrees'].fillna(0)
    df_res['Quantite_Dispo'] = df_res['Stock_Initial'] + df_res['Total_Entrees'] - df_res['Total_Sorties']
    return df_res

# ==========================================
# 4. GESTION DE L'AUTHENTIFICATION
# ==========================================
if 'authentifie' not in st.session_state: st.session_state.authentifie = False
if 'role_utilisateur' not in st.session_state: st.session_state.role_utilisateur = None
if 'nom_utilisateur' not in st.session_state: st.session_state.nom_utilisateur = None

OPTIONS_PAR_ROLE = {
    "Serveur": ["📝 Prise de Commande"],
    "Responsable Caisse": ["📝 Prise de Commande", "🧾 Commandes & Additions", "📦 Stocks & Approvisionnements"],
    "Administrateur": ["📝 Prise de Commande", "🧾 Commandes & Additions", "📦 Stocks & Approvisionnements"]
}

if not st.session_state.authentifie:
    _, col_centre, _ = st.columns([1, 1.2, 1])
    with col_centre:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>Connexion</h3>", unsafe_allow_html=True)
            id_in = st.text_input("👤 Identifiant :")
            mdp_in = st.text_input("🔑 Mot de passe :", type="password")
            if st.button("Se connecter au système 🚀", use_container_width=True, type="primary"):
                utilisateurs = st.session_state.base_utilisateurs
                match = utilisateurs[(utilisateurs['Identifiant'] == id_in) & (utilisateurs['Mot_De_Passe'] == mdp_in)]
                if not match.empty:
                    st.session_state.authentifie = True
                    st.session_state.role_utilisateur = match.iloc[0]['Role']
                    st.session_state.nom_utilisateur = match.iloc[0]['Identifiant']
                    st.rerun()
    st.stop()

st.sidebar.title("🍳 Menu Easygest")
options_disponibles = OPTIONS_PAR_ROLE.get(st.session_state.role_utilisateur, ["📝 Prise de Commande"])
choix_vue = st.sidebar.radio("Navigation :", options_disponibles)

# ==========================================
# VUE : PRISE DE COMMANDE CONSOLIDÉE
# ==========================================
def vue_prise_commande():
    st.subheader("📝 Écran Serveur : Prise de Commande Rapide & Options")
    df_global = consolider_stocks_et_marges()

    col1, col2 = st.columns([1, 1])
    with col1:
        dict_menu = {}
        dict_categories = {}
        
        for _, r in st.session_state.base_menu.iterrows():
            designation_upper = str(r['Designation']).upper().strip()
            
            # FILTRE SÉCURISÉ TOTAL : Élimine les matières premières et TOUT article contenant le mot "LIQUEUR"
            if designation_upper in MATIERES_PREMIERES_CIBLES or "LIQUEUR" in designation_upper:
                continue

            label = f"[{r['Categorie']}] {r['Designation']} ({int(r['Prix_Vente_FCFA'])} FCFA)"
            dict_menu[label] = r['Designation']
            dict_categories[label] = r['Categorie']

        if not dict_menu:
            st.info("Aucun plat ou boisson disponible à la vente.")
            return

        table_choisie = st.selectbox("Sélectionner la Table :", [f"Table {i}" for i in range(1, 31)])
        item_choisi = st.selectbox("Article demandé :", list(dict_menu.keys()))
        
        categorie_active = dict_categories[item_choisi] if item_choisi else "Cuisine"
        accomp_choisi = "-"
        if categorie_active == "Cuisine":
            accomp_choisi = st.selectbox("Accompagnement gratuit :", ["Alloco", "Attiéké", "Frites", "Riz Blanc", "Sans"])

        with st.form("form_commande_strict", clear_on_submit=True):
            quantite = st.number_input("Quantité :", min_value=1, value=1)
            opt_remise = st.selectbox("Taux de remise :", [0, 5, 10, 15, 20])
            
            if st.form_submit_button("Envoyer la commande 🚀"):
                designation_plat = dict_menu[item_choisi]
                item_details = df_global[df_global['Designation'] == designation_plat].iloc[0]
                
                nom_matiere_brute, coef_defalquage = determiner_matiere_premiere(item_details['Designation'], item_details['Prix_Vente_FCFA'])
                
                matiere_a_deduire = designation_plat
                target_details = item_details
                quantite_a_deduire = float(quantite)
                
                if nom_matiere_brute:
                    match_brute = df_global[df_global['Designation'].str.upper().str.strip() == nom_matiere_brute.upper()]
                    if not match_brute.empty:
                        matiere_a_deduire = match_brute.iloc[0]['Designation']
                        target_details = match_brute.iloc[0]
                        quantite_a_deduire = float(quantite) * coef_defalquage

                if quantite_a_deduire > target_details['Quantite_Dispo']:
                    st.error(f"❌ Stock insuffisant ! (Dispo {target_details['Designation']}: {target_details['Quantite_Dispo']} | Demandé: {quantite_a_deduire})")
                else:
                    total_net = (quantite * item_details['Prix_Vente_FCFA']) * (1 - (opt_remise / 100))
                    
                    nouvelle_ligne = pd.DataFrame([{
                        'Heure': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Table': table_choisie, 
                        'Designation': designation_plat, 'Matiere_Stock': matiere_a_deduire, 
                        'Type_Flux': 'Sortie', 'Quantite': quantite_a_deduire, 
                        'Prix_Unitaire_Flux': item_details['Prix_Vente_FCFA'], 'Remise_Pourcent': opt_remise, 
                        'Accompagnement': accomp_choisi, 'Total_FCFA': total_net,
                        'Motif_Remise': 'Aucun', 'Statut': 'En cours', 'Ref_Bon': '-'
                    }])
                    st.session_state.historique_ventes = pd.concat([st.session_state.historique_ventes, nouvelle_ligne], ignore_index=True)
                    sauvegarder_ventes()
                    st.success(f"Commande validée ! Stock déduit sur : {target_details['Designation']}")
                    st.rerun()
                    
    with col2:
        st.info(f"👤 Connecté : **{st.session_state.nom_utilisateur}**")

if choix_vue == "📝 Prise de Commande": vue_prise_commande()
