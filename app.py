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
    ains que le coefficient de décalquage (consommation de stock).
    Retourne un tuple: (nom_matiere_premiere, coefficient_defalquage)
    """
    nom_article_up = str(nom_article).upper().strip()
    
    # --- CAS DES POISSONS (Par défaut coefficient 1) ---
    if "POISSON" in nom_article_up:
        coef = 1.0
        if prix_unitaire == 2000:
            return "PETIT POISSON", coef
        elif prix_unitaire == 4000:
            return "MOYEN POISSON", coef
        elif prix_unitaire == 6000:
            return "GROS POISSON", coef
        else:
            if "PETIT" in nom_article_up: return "PETIT POISSON", coef
            if "MOYEN" in nom_article_up: return "MOYEN POISSON", coef
            if "GROS" in nom_article_up: return "GROS POISSON", coef
            return None, 0.0
            
    # --- CAS DES VIANDES FRACTIONNÉES (POULET, PINTADE, LAPIN) ---
    base_viande = None
    if "POULET" in nom_article_up:
        base_viande = "POULET"
    elif "LAPIN" in nom_article_up:
        base_viande = "LAPIN"
    elif "PINTADE" in nom_article_up:
        base_viande = "PINTADE"

    if base_viande:
        # Analyse de la portion/fraction dans le nom de l'article
        if "1/4" in nom_article_up or "QUART" in nom_article_up:
            return base_viande, 0.25
        elif "1/2" in nom_article_up or "DEMI" in nom_article_up:
            return base_viande, 0.50
        else:
            # Par défaut, si rien n'est spécifié, on retire 1 entier
            return base_viande, 1.0
        
    return None, 0.0

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

# Initialisation de la variable de message de succès de commande
if 'message_succes_commande' not in st.session_state:
    st.session_state.message_succes_commande = None

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
    
    # Affichage du message de succès s'il existe dans la session
    if st.session_state.message_succes_commande:
        st.success(st.session_state.message_succes_commande)
        # On vide la variable pour éviter qu'il s'affiche indéfiniment lors d'autres actions
        st.session_state.message_succes_commande = None

    if len(st.session_state.base_menu) == 0 or (len(st.session_state.base_menu) == 1 and "Exemple" in st.session_state.base
