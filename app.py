import streamlit as st
import pandas as pd
import io

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# 2. STYLE VISUEL
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
    </style>
    """, unsafe_allow_html=True)

# 3. BASE DE DONNÉES (Session State)
if 'base_pasteurs' not in st.session_state:
    st.session_state.base_pasteurs = {
        "KOKORA JONAS": ["Pasteur", 100000, "Abidjan Nord"],
        "KOUAKOU Shadrac": ["Pasteur", 60000, "Abidjan Nord"],
        "KOUAME Ange": ["Evangéliste", 50000, "Abidjan Nord"],
        "HEDILON YAO": ["Pasteur", 100000, "Abidjan Nord"],
    }

st.title("🛡️ APPLICATION DE GESTION MIEDA")

# 4. STRUCTURE DES ONGLETS (Structure conservée selon vidéo et photos)
tab_gen, tab_dime, tab_offr, tab_past, tab_config = st.tabs([
    "🌍 Général", "💰 Rapport Dîme", "🕊️ Offrandes", "👨‍💼 Liste Pasteurs", "⚙️ Configuration"
])

# --- ONGLET GÉNÉRAL ---
with tab_gen:
    regions_existantes = sorted(list(set([v[2] for v in st.session_state.base_pasteurs.values()])))
    col_a, col_b = st.columns(2)
    region_sel = col_a.selectbox("🌍 Région :", regions_existantes)
    mois_sel = col_a.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = col_b.text_input("📍 District :", placeholder="Nom du district")

# --- ONGLET RAPPORT DÎME (Détail conservé selon photo) ---
with tab_dime:
    d_mois = st.number_input("Dîme du mois:", value=2421800)
    l_temple = st.number_input("Loyer temple:", value=240000)
    l_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    a_ch = st.number_input("Autres charges:", value=0)
    f_transf = st.number_input("Frais de transfert:", value=0)
    f_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    a_ress = st.number_input("Autres ressources/appro.:", value=0)

# --- ONGLET OFFRANDES (Détail conservé selon photo) ---
with tab_offr:
    o_ord = st.number_input("Offrandes ordinaires:", value=0)
    d_offr = st.number_input("Dépenses sur offr. ord.:", value=0)
    g1 = st.number_input("1ère Action de Grâce:", value=0)
    s_dist = st.number_input("Soutien aux districts:", value=0)
    s_insp = st.number_input("Soutien Inspectorat:", value=0)
    s_soc = st.number_input("Soutien Aff. Sociales:", value=0)
    admin = st.number_input("Administration:", value=0)
    evang = st.number_input("Evangélisation:", value=0)
    g2 = st.number_input("2ème Action de Grâce:", value=0)

# --- ONGLET LISTE PASTEURS ---
with tab_past:
    st.write(f"### Saisie des versements : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    saisies_v = {}
    for nom, infos in p_reg.items():
        c1, c2 = st.columns([3, 1])
        c1.write(nom)
        saisies_v[nom] = c2.number_input("Versé", value=infos[1], key=f"s_{nom}", label_visibility="collapsed")

# --- ONGLET CONFIGURATION ---
with tab_config:
    with st.form("add"):
        n_nom = st.text_input("Nom")
        n_reg = st.selectbox("Région", ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"])
        n_sal = st.number_input("Montant", value=50000)
        if st.form_submit_button("Ajouter"):
            st.session_state.base_pasteurs[n_nom.upper()] = ["Pasteur", n_sal, n_reg]
            st.rerun()

# --- GÉNÉRATION DU RAPPORT DÉTAILLÉ ---
st.divider()
if st.button("Générer le Bilan Détaillé"):
    st.success(f"Rapport de gestion établi pour {region_sel} - {mois_sel}")
    
    # 1. Détail du Rapport Dîmes
    st.subheader("💰 Détail du Rapport Dîmes")
    dime_10 = d_mois * 0.10 # Prélèvement obligatoire
    df_dime_detail = pd.DataFrame([
        {"Rubrique": "Dîme du mois", "Montant": f"{d_mois:,} F"},
        {"Rubrique": "Dîme des Dîmes (10%)", "Montant": f"-{int(dime_10):,} F"},
        {"Rubrique": "Loyer temple", "Montant": f"-{l_temple:,} F"},
        {"Rubrique": "Loyer résidence Pasteurs", "Montant": f"-{l_res:,} F"},
        {"Rubrique": "Autres charges", "Montant": f"-{a_ch:,} F"},
        {"Rubrique": "Frais de transfert/transport", "Montant": f"-{f_transf + f_transp:,} F"},
        {"Rubrique": "Autres ressources", "Montant": f"{a_ress:,} F"}
    ])
    st.table(df_dime_detail)

    # 2. Détail du Rapport Offrandes
    st.subheader("🕊️ Détail du Rapport Offrandes")
    df_offr_detail = pd.DataFrame([
        {"Rubrique": "Offrandes ordinaires", "Montant": f"{o_ord:,} F"},
        {"Rubrique": "Dépenses sur offrandes", "Montant": f"-{d_offr:,} F"},
        {"Rubrique": "Actions de Grâce (Total)", "Montant": f"{g1 + g2:,} F"},
        {"Rubrique": "Soutiens (Districts/Insp/Social)", "Montant": f"{s_dist + s_insp + s_soc:,} F"},
        {"Rubrique": "Administration & Evangélisation", "Montant": f"{admin + evang:,} F"}
    ])
    st.table(df_offr_detail)

    # 3. Détail des Pasteurs
    st.subheader("👨‍💼 Détail des Soutiens Versés")
    liste_p = [{"Pasteur": k, "Salaire Versé": f"{v:,} F"} for k, v in saisies_v.items()]
    st.table(pd.DataFrame(liste_p))

    # EXPORT EXCEL DÉTAILLÉ
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_dime_detail.to_excel(writer, sheet_name='Detail Dimes', index=False)
        df_offr_detail.to_excel(writer, sheet_name='Detail Offrandes', index=False)
        pd.DataFrame(liste_p).to_excel(writer, sheet_name='Detail Pasteurs', index=False)
    
    st.download_button(
        label="📥 Télécharger le Rapport Complet (Excel)",
        data=output.getvalue(),
        file_name=f"Rapport_Detaille_MIEDA_{region_sel}_{mois_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
