import streamlit as st
import pandas as pd

# 1. Configuration pour masquer les menus inutiles et forcer le style
st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# Style CSS pour ressembler à la vidéo (bouton bleu, onglets larges)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #1565C0;
        color: white;
        height: 3em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Base de données complète
base_pasteurs = {
    "KOKORA JONAS": ["Pasteur", 100000, "Abidjan Nord"],
    "KOUAKOU Shadrac": ["Pasteur", 60000, "Abidjan Nord"],
    "KOUAME Ange": ["Evangéliste", 50000, "Abidjan Nord"],
    "HEDILON YAO": ["Pasteur", 100000, "Abidjan Nord"],
    "KOUAME Etienne": ["Pasteur", 50000, "Abidjan Nord"],
    "KRAH Yacinthe": ["Pasteur", 100000, "Abidjan Nord"],
    "AKA YAO": ["Pasteur", 120000, "Abidjan Nord"],
    "DIGBE Martial": ["Pasteur", 50000, "Abidjan Nord"],
    "YOBOUE Virginie": ["Pasteur", 60000, "Abidjan Nord"],
    "DJEHA Josué": ["Pasteur", 80000, "Abidjan Nord"],
    "AHOUTOU Narcisse": ["Evangéliste", 80000, "Abidjan Nord"],
    "KONGO KOUAME": ["Pasteur", 80000, "Abidjan Nord"],
}

st.title("🛡️ APPLICATION DE GESTION MIEDA")

# 3. Structure des onglets (Exactement comme la vidéo)
tab_gen, tab_dime, tab_offr, tab_past = st.tabs([
    "🌍 Général", 
    "💰 Rapport Dîme", 
    "🕊️ Offrandes", 
    "👨‍💼 Liste Pasteurs"
])

with tab_gen:
    region_sel = st.selectbox("🌍 Région :", ["Abidjan Nord", "Abidjan Sud"])
    mois_sel = st.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = st.text_input("📍 District :", placeholder="Nom du district")

with tab_dime:
    dime_mois = st.number_input("Dîme du mois:", value=2421800)
    loyer_temple = st.number_input("Loyer temple:", value=240000)
    loyer_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    autres_ch = st.number_input("Autres charges:", value=0)
    frais_transf = st.number_input("Frais de transfert:", value=0)
    frais_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    autres_ress = st.number_input("Autres ressources/appro.:", value=0)

with tab_offr:
    st.number_input("Offrandes ordinaires:", value=0)
    st.number_input("Dépenses sur offr. ord.:", value=0)
    st.number_input("1ère Action de Grâce:", value=0)
    st.number_input("Soutien aux districts:", value=0)
    st.number_input("Soutien Inspectorat:", value=0)
    st.number_input("Soutien Aff. Sociales:", value=0)
    st.number_input("Administration:", value=0)
    st.number_input("Evangélisation:", value=0)
    st.number_input("2ème Action de Grâce:", value=0)

with tab_past:
    st.write(f"### Soutiens pour la région : {region_sel}")
    p_reg = {k: v for k, v in base_pasteurs.items() if v[2] == region_sel}
    saisies = {}
    for nom, infos in p_reg.items():
        col_n, col_v = st.columns([3, 1])
        col_n.write(f"**{nom}** ({infos[0]})")
        saisies[nom] = col_v.number_input("Versé:", value=0, key=f"v_{nom}", label_visibility="collapsed")

# Bouton de validation (Large et Bleu)
if st.button("Générer le Bilan Intégral"):
    st.success("Bilan généré avec succès !")
    # Calcul simplifié pour l'exemple
    dispo = (dime_mois * 0.9) - (loyer_temple + loyer_res)
    st.metric("Total disponible", f"{int(dispo):,} F CFA")
