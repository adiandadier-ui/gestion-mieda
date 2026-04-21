import streamlit as st
import pandas as pd
import io

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# 2. STYLE VISUEL (Bouton Bleu et Interface)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #1565C0;
        color: white;
        height: 3em;
        font-weight: bold;
        border-radius: 5px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1565C0 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. GESTION DE LA BASE DE DONNÉES (Session State)
if 'base_pasteurs' not in st.session_state:
    st.session_state.base_pasteurs = {
        "KOKORA JONAS": ["Pasteur", 100000, "Abidjan Nord"],
        "KOUAKOU Shadrac": ["Pasteur", 60000, "Abidjan Nord"],
        "KOUAME Ange": ["Evangéliste", 50000, "Abidjan Nord"],
        "HEDILON YAO": ["Pasteur", 100000, "Abidjan Nord"],
        "AHOUTOU Narcisse": ["Evangéliste", 80000, "Abidjan Nord"],
        "GNAGNE Paul": ["Pasteur", 100000, "Abidjan Nord"],
    }

st.title("🛡️ APPLICATION DE GESTION MIEDA")

# 4. STRUCTURE DES ONGLETS
tab_gen, tab_dime, tab_offr, tab_past, tab_config = st.tabs([
    "🌍 Général", 
    "💰 Rapport Dîme", 
    "🕊️ Offrandes", 
    "👨‍💼 Liste Pasteurs",
    "⚙️ Configuration"
])

# --- ONGLET GÉNÉRAL ---
with tab_gen:
    col1, col2 = st.columns(2)
    with col1:
        # Récupération dynamique des régions
        regions_existantes = sorted(list(set([v[2] for v in st.session_state.base_pasteurs.values()])))
        region_sel = st.selectbox("🌍 Région :", regions_existantes)
        mois_sel = st.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    with col2:
        district_sel = st.text_input("📍 District :", placeholder="Ex: Cocody")

# --- ONGLET RAPPORT DÎME ---
with tab_dime:
    st.subheader("Saisie des flux de Dîmes")
    dime_mois = st.number_input("Dîme du mois:", value=2421800)
    loyer_temple = st.number_input("Loyer temple:", value=240000)
    loyer_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    autres_ch = st.number_input("Autres charges:", value=0)
    frais_transf = st.number_input("Frais de transfert:", value=0)
    frais_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    autres_ress = st.number_input("Autres ressources/appro.:", value=0)

# --- ONGLET OFFRANDES ---
with tab_offr:
    st.subheader("Saisie des flux d'Offrandes")
    offr_ord = st.number_input("Offrandes ordinaires:", value=0)
    dep_offr = st.number_input("Dépenses sur offr. ord.:", value=0)
    action_grace1 = st.number_input("1ère Action de Grâce:", value=0)
    soutien_dist = st.number_input("Soutien aux districts:", value=0)
    soutien_insp = st.number_input("Soutien Inspectorat:", value=0)
    soutien_soc = st.number_input("Soutien Aff. Sociales:", value=0)
    admin = st.number_input("Administration:", value=0)
    evang = st.number_input("Evangélisation:", value=0)
    action_grace2 = st.number_input("2ème Action de Grâce:", value=0)

# --- ONGLET LISTE PASTEURS ---
with tab_past:
    st.subheader(f"Soutiens pour la région : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    
    saisies_pasteurs = {}
    if p_reg:
        for nom, infos in p_reg.items():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{nom}** ({infos[0]})")
            saisies_pasteurs[nom] = c2.number_input("Versé", value=0, key=f"p_{nom}", label_visibility="collapsed")
    else:
        st.info("Aucun pasteur enregistré dans cette région.")

# --- ONGLET CONFIGURATION ---
with tab_config:
    st.subheader("⚙️ Paramètres de la base")
    with st.form("ajout_pasteur"):
        st.write("Ajouter un nouveau pasteur")
        n_nom = st.text_input("Nom complet")
        n_grade = st.selectbox("Grade", ["Pasteur", "Evangéliste", "Missionnaire"])
        n_montant = st.number_input("Montant de soutien prévu", value=50000, step=5000)
        n_reg = st.selectbox("Région", ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"])
        if st.form_submit_button("Enregistrer"):
            if n_nom:
                st.session_state.base_pasteurs[n_nom.upper()] = [n_grade, n_montant, n_reg]
                st.success(f"{n_nom} ajouté !")
                st.rerun()

# --- CALCULS ET GÉNÉRATION DU BILAN ---
st.divider()
if st.button("Générer le Bilan Intégral"):
    # Logique métier : Prélèvement de 10%
    dime_10 = dime_mois * 0.10
    total_charges = loyer_temple + loyer_res + autres_ch + frais_transf + frais_transp + perdiem
    total_dispo = (dime_mois - dime_10) - total_charges + autres_ress
    
    st.success("Bilan généré !")
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Dîme des Dîmes (10%)", f"{int(dime_10):,} F")
    col_res2.metric("Total Disponible", f"{int(total_dispo):,} F")

    # --- OPTIONS DE TÉLÉCHARGEMENT ---
    st.subheader("📥 Téléchargement des Rapports")
    
    # Création du DataFrame pour l'export
    data_export = {
        "Libellé": ["Dîme du mois", "Prélèvement 10%", "Charges Totales", "Ressources Suppl.", "Bilan Net"],
        "Montant (F CFA)": [dime_mois, -dime_10, -total_charges, autres_ress, total_dispo]
    }
    df_bilan = pd.DataFrame(data_export)

    # Export CSV
    csv = df_bilan.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger le Rapport CSV (Excel)",
        data=csv,
        file_name=f"Bilan_{region_sel}_{mois_sel}.csv",
        mime="text/csv"
    )
    
    st.info("Note : Pour le PDF, utilisez la fonction 'Imprimer' (Ctrl+P) de votre navigateur sur la page générée pour un rendu propre.")
