import os
import subprocess
from datetime import datetime
import pandas as pd
import streamlit as st

# ==============================================================================
# 1. EN-TÊTE ET CONFIGURATION DE LA PAGE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="EASYGEST APPS - Système de Ventes",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. INITIALISATION AUTOMATIQUE DU STOCKAGE SUR LE BUREAU
# ==============================================================================

# Récupération automatique du chemin du Bureau de l'utilisateur connecté
bureau_path = os.path.join(os.path.expanduser("~"), "Desktop")
NOM_DOSSIER = "EASYGEST APPS"

# Chemin absolu ciblé sur le Bureau Windows
DOSSIER_CIBLE = os.path.join(bureau_path, NOM_DOSSIER)

# Sécurité de repli automatique (si droits administrateur restreints ou OneDrive bloquant)
try:
    if not os.path.exists(DOSSIER_CIBLE):
        os.makedirs(DOSSIER_CIBLE)
    storage_info = f"Dossier actif sur le Bureau"
    mode_repli = False
except Exception:
    # Solution de secours : Crée un dossier à côté du script Python
    DOSSIER_CIBLE = os.path.abspath(f"./{NOM_DOSSIER}_LOCAL")
    if not os.path.exists(DOSSIER_CIBLE):
        os.makedirs(DOSSIER_CIBLE)
    storage_info = f"Mode repli sécurisé (Dossier local)"
    mode_repli = True

# Définition des chemins dynamiques et exclusifs vers les fichiers CSV
CSV_MENU = os.path.join(DOSSIER_CIBLE, "easygest_base_menu.csv")
CSV_VENTES = os.path.join(DOSSIER_CIBLE, "easygest_ventes.csv")
CSV_BONS = os.path.join(DOSSIER_CIBLE, "easygest_bons.csv")


# ==============================================================================
# 3. VERIFICATION ET CRÉATION DES STRUCTURES DE DONNÉES (CSV)
# ==============================================================================
def initialiser_base_donnees():
    """Vérifie la présence des fichiers CSV et les génère avec leurs en-têtes si absents."""
    # 1. Fichier Menu / Articles
    if not os.path.exists(CSV_MENU):
        df_menu = pd.DataFrame(columns=["Code_Article", "Designation", "Prix_Unitaire", "Categorie"])
        # Données de démonstration initiales
        demo_data = [
            {"Code_Article": "ART001", "Designation": "Article Standard A", "Prix_Unitaire": 1500, "Categorie": "Général"},
            {"Code_Article": "ART002", "Designation": "Article Premium B", "Prix_Unitaire": 3500, "Categorie": "Premium"}
        ]
        pd.DataFrame(demo_data).to_csv(CSV_MENU, index=False, encoding="utf-8")
        
    # 2. Fichier Historique des Lignes de Vente
    if not os.path.exists(CSV_VENTES):
        df_ventes = pd.DataFrame(columns=["Date_Heure", "ID_Commande", "Code_Article", "Designation", "Quantite", "Prix_Unitaire", "Total_Ligne"])
        df_ventes.to_csv(CSV_VENTES, index=False, encoding="utf-8")
        
    # 3. Fichier En-tête des Bons / Factures
    if not os.path.exists(CSV_BONS):
        df_bons = pd.DataFrame(columns=["ID_Commande", "Date", "Client", "Montant_Total", "Mode_Paiement"])
        df_bons.to_csv(CSV_BONS, index=False, encoding="utf-8")

# Exécution de l'initialisation système
initialiser_base_donnees()


# ==============================================================================
# 4. INTERFACE DE LA BARRE LATÉRALE (SIDEBAR) & CONTROLES
# ==============================================================================
with st.sidebar:
    st.title("🚀 EASYGEST CONTROL")
    st.write("---")
    
    st.subheader("📂 Emplacement des Fichiers")
    if not mode_repli:
        st.success(f"📍 {storage_info}")
    else:
        st.warning(f"📍 {storage_info}")
        
    st.caption(f" Chemin : `{DOSSIER_CIBLE}`")
    
    # BOUTON INTERACTIF : Ouvre le dossier physique Windows sur l'écran
    if st.button("📁 OUVRIR LE DOSSIER", use_container_width=True):
        try:
            subprocess.Popen(f'explorer "{DOSSIER_CIBLE}"')
            st.toast("Explorateur Windows ouvert !", icon="📂")
        except Exception as e:
            st.error(f"Erreur d'ouverture : {e}")
            
    st.write("---")
    
    # Menu de navigation principal
    page = st.radio(
        "SÉLECTIONNER UN MODULE :", 
        ["🛒 Prise de Commande", "📦 Gestion du Menu / Articles", "📈 Analyse & Historique"]
    )


# ==============================================================================
# MODULE 1 : PRISE DE COMMANDE & FACTURATION
# ==============================================================================
if page == "🛒 Prise de Commande":
    st.title("🛒 Module de Vente & Facturation")
    st.write("Saisissez les articles pour générer un bon de commande et mettre à jour le fichier des ventes.")
    st.write("---")
    
    # Chargement de la base article pour le formulaire
    df_menu = pd.read_csv(CSV_MENU, encoding="utf-8")
    
    if df_menu.empty:
        st.info("💡 Votre base d'articles est vide. Allez dans l'onglet 'Gestion du Menu' pour ajouter des articles.")
    else:
        # Initialisation du panier en mémoire de session Streamlit
        if "panier" not in st.session_state:
            st.session_state.panier = []
            
        col_form, col_panier = st.columns([1, 1.5])
        
        with col_form:
            st.subheader("➕ Ajouter un article")
            # Sélection de l'article via la liste du CSV
            liste_options = df_menu.apply(lambda r: f"{r['Code_Article']} - {r['Designation']} ({r['Prix_Unitaire']} FCFA)", axis=1).tolist()
            choix = st.selectbox("Sélectionner l'article", options=liste_options)
            
            # Extraction de la ligne sélectionnée
            idx_selection = liste_options.index(choix)
            article_selectionne = df_menu.iloc[idx_selection]
            
            quantite = st.number_input("Quantité", min_value=1, value=1, step=1)
            
            if st.button("Ajouter au panier 📥", use_container_width=True):
                # Calcul de la ligne
                total_ligne = int(article_selectionne["Prix_Unitaire"]) * quantite
                
                # Ajout dans la structure temporaire
                st.session_state.panier.append({
                    "Code_Article": article_selectionne["Code_Article"],
                    "Designation": article_selectionne["Designation"],
                    "Quantite": quantite,
                    "Prix_Unitaire": int(article_selectionne["Prix_Unitaire"]),
                    "Total_Ligne": total_ligne
                })
                st.toast("Article ajouté au panier !", icon="✅")
                st.rerun()

        with col_panier:
            st.subheader("📋 Panier Actuel")
            if st.session_state.panier:
                df_panier = pd.DataFrame(st.session_state.panier)
                st.dataframe(df_panier, use_container_width=True, hide_index=True)
                
                # Calcul du net à payer
                net_a_payer = df_panier["Total_Ligne"].sum()
                st.metric(label="NET À PAYER (FCFA)", value=f"{net_a_payer:,}")
                
                # Informations complémentaires de la facture
                nom_client = st.text_input("Nom du Client / Depot", value="Client Comptant")
                mode_paye = st.selectbox("Mode de règlement", ["Espèces", "Chèque", "Mobile Money", "Virement"])
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("❌ Vider le panier", use_container_width=True):
                        st.session_state.panier = []
                        st.rerun()
                with c2:
                    if st.button("💾 Valider & Enregistrer", variant="primary", use_container_width=True):
                        # Génération d'un ID unique basé sur l'horodatage
                        id_commande = datetime.now().strftime("CMD-%Y%m%d-%H%M%S")
                        date_courante = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 1. Sauvegarde des lignes détaillées dans EASYGEST_VENTES
                        df_ventes_existantes = pd.read_csv(CSV_VENTES, encoding="utf-8")
                        df_panier["ID_Commande"] = id_commande
                        df_panier["Date_Heure"] = date_courante
                        
                        # Réorganisation des colonnes pour matcher exactement le CSV cible
                        ordre_colonnes = ["Date_Heure", "ID_Commande", "Code_Article", "Designation", "Quantite", "Prix_Unitaire", "Total_Ligne"]
                        df_panier = df_panier[ordre_colonnes]
                        
                        df_ventes_final = pd.concat([df_ventes_existantes, df_panier], ignore_index=True)
                        df_ventes_final.to_csv(CSV_VENTES, index=False, encoding="utf-8")
                        
                        # 2. Sauvegarde du récapitulatif global dans EASYGEST_BONS
                        df_bons_existants = pd.read_csv(CSV_BONS, encoding="utf-8")
                        nouveau_bon = pd.DataFrame([{
                            "ID_Commande": id_commande,
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Client": nom_client,
                            "Montant_Total": net_a_payer,
                            "Mode_Paiement": mode_paye
                        }])
                        df_bons_final = pd.concat([df_bons_existants, nouveau_bon], ignore_index=True)
                        df_bons_final.to_csv(CSV_BONS, index=False, encoding="utf-8")
                        
                        # Réinitialisation de session
                        st.session_state.panier = []
                        st.success(f"Commande {id_commande} enregistrée avec succès dans vos CSV !")
                        st.rerun()
            else:
                st.caption("Le panier est actuellement vide.")


# ==============================================================================
# MODULE 2 : GESTION DE LA BASE ARTICLES (MENU)
# ==============================================================================
elif page == "📦 Gestion du Menu / Articles":
    st.title("📦 Configuration du Catalogue Articles (Menu)")
    st.write(f"Mise à jour et consultation directe du fichier : `{CSV_MENU}`")
    st.write("---")
    
    df_menu = pd.read_csv(CSV_MENU, encoding="utf-8")
    
    col_liste, col_ajout = st.columns([1.5, 1])
    
    with col_liste:
        st.subheader("Articles enregistrés")
        st.dataframe(df_menu, use_container_width=True, hide_index=True)
        st.caption(f"Total : {len(df_menu)} article(s) configuré(s).")
        
    with col_ajout:
        st.subheader("✨ Ajouter un nouvel article")
        with st.form("form_nouvel_article", clear_on_submit=True):
            code = st.text_input("Code de l'article (Ex: ART003)").strip()
            designation = st.text_input("Désignation / Nom complet").strip()
            prix = st.number_input("Prix de vente unitaire (FCFA)", min_value=0, step=25)
            cat = st.text_input("Catégorie / Famille", value="Général").strip()
            
            submit = st.form_submit_button("Sauvegarder l'article", use_container_width=True)
            
            if submit:
                if not code or not designation:
                    st.error("Le Code et la Désignation sont obligatoires.")
                elif code in df_menu["Code_Article"].astype(str).values:
                    st.error(f"Le code '{code}' existe déjà dans votre base de données.")
                else:
                    nouvel_art = pd.DataFrame([{"Code_Article": code, "Designation": designation, "Prix_Unitaire": prix, "Categorie": cat}])
                    df_menu_maj = pd.concat([df_menu, nouvel_art], ignore_index=True)
                    df_menu_maj.to_csv(CSV_MENU, index=False, encoding="utf-8")
                    st.success(f"L'article '{designation}' a bien été inséré dans le fichier CSV.")
                    st.rerun()


# ==============================================================================
# MODULE 3 : ANALYSE DES COMPTES ET HISTORIQUE DES FLUX
# ==============================================================================
elif page == "📈 Analyse & Historique":
    st.title("📈 Analyse d'Activité et Visualisation")
    st.write("Consultation consolidée des historiques de ventes et états financiers.")
    st.write("---")
    
    df_ventes = pd.read_csv(CSV_VENTES, encoding="utf-8")
    df_bons = pd.read_csv(CSV_BONS, encoding="utf-8")
    
    if df_bons.empty:
        st.info("Aucune transaction n'a encore été enregistrée dans l'historique.")
    else:
        # KPI Métriques du Tableau de bord
        ca_total = df_bons["Montant_Total"].sum()
        nb_transactions = len(df_bons)
        panier_moyen = ca_total / nb_transactions if nb_transactions > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label="CHIFFRE D'AFFAIRES BRUT", value=f"{ca_total:,} FCFA")
        with c2:
            st.metric(label="VOLUME DE BONS ÉMIS", value=f"{nb_transactions} commandes")
        with c3:
            st.metric(label="PANIER MOYEN CLIENT", value=f"{int(panier_moyen):,} FCFA")
            
        st.write("---")
        
        # Onglets de séparation des données brutes
        tab_bons, tab_lignes_detaillees = st.tabs(["📄 Registre des Bons (En-têtes)", "🔍 Journal des Ventes (Détail)"])
        
        with tab_bons:
            st.subheader("Historique global des factures")
            st.dataframe(df_bons.sort_values(by="ID_Commande", ascending=False), use_container_width=True, hide_index=True)
            
        with tab_lignes_detaillees:
            st.subheader("Lignes de transactions détaillées")
            st.dataframe(df_ventes.sort_values(by="Date_Heure", ascending=False), use_container_width=True, hide_index=True)
