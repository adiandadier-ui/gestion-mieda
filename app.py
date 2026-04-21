import streamlit as st
import pandas as pd

st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# --- STYLE CSS ---
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

# --- GESTION DE LA MÉMOIRE DYNAMIQUE ---
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

# --- STRUCTURE DES ONGLETS ---
tab_gen, tab_dime, tab_offr, tab_past, tab_admin = st.tabs([
    "🌍 Général", 
    "💰 Rapport Dîme", 
    "🕊️ Offrandes", 
    "👨‍💼 Liste Pasteurs",
    "⚙️ Configuration"
])

with tab_gen:
    regions_dispo = list(set([v[2] for v in st.session_state.base_pasteurs.values()]))
    if "Abidjan Sud" not in regions_dispo: regions_dispo.append("Abidjan Sud")
    
    region_sel = st.selectbox("🌍 Région :", sorted(regions_dispo))
    mois_sel = st.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = st.text_input("📍 District :", placeholder="Nom du district")

with tab_dime:
    # Structure exacte selon la photo
    dime_mois = st.number_input("Dîme du mois:", value=2421800)
    loyer_temple = st.number_input("Loyer temple:", value=240000)
    loyer_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    autres_ch = st.number_input("Autres charges:", value=0)
    frais_transf = st.number_input("Frais de transfert:", value=0)
    frais_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    autres_ress = st.number_input("Autres ressources/appro.:", value=0)

with tab_offr:
    # Structure exacte selon la photo
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
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    
    if not p_reg:
        st.warning("Aucun pasteur enregistré dans cette région.")
    
    saisies = {}
    for nom, infos in p_reg.items():
        col_n, col_v = st.columns([3, 1])
        col_n.write(f"**{nom}** ({infos[0]}) - Prévu: {infos[1]:,} F")
        saisies[nom] = col_v.number_input("Versé:", value=0, key=f"v_{nom}", label_visibility="collapsed")

with tab_admin:
    st.subheader("➕ Ajouter un nouveau membre")
    with st.form("new_pastor_form"):
        new_nom = st.text_input("Nom et Prénoms")
        col_a, col_b = st.columns(2)
        new_grade = col_a.selectbox("Grade", ["Pasteur", "Evangéliste", "Gestionnaire Distri"])
        new_prevu = col_b.number_input("Montant Prévu (F CFA)", step=5000)
        # Utilisation des districts de Côte d'Ivoire gérés par l'utilisateur
        new_region = st.selectbox("Région d'affectation", ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"])
        
        submit = st.form_submit_button("ENREGISTRER DANS LA BASE")
        
        if submit and new_nom:
            st.session_state.base_pasteurs[new_nom.upper()] = [new_grade, new_prevu, new_region]
            st.success(f"{new_nom} ajouté avec succès !")

# --- BOUTON FINAL ---
if st.button("Générer le Bilan Intégral"):
    st.success("Bilan généré avec succès !")
    # Calcul basé sur la règle des 5 semaines pour les alertes stocks mais appliqué ici au bilan financier mensuel
    dime_10 = dime_mois * 0.10 
    dispo = (dime_mois - dime_10) - (loyer_temple + loyer_res + autres_ch + frais_transf + frais_transp + perdiem) + autres_ress
    st.metric("Total disponible après prélèvement 10%", f"{int(dispo):,} F CFA")
