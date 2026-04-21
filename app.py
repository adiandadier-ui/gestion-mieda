import streamlit as st
import pandas as pd
import io

# Configuration de la page
st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# Style CSS pour le bouton bleu
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

# Base de données
if 'base_pasteurs' not in st.session_state:
    st.session_state.base_pasteurs = {
        "KOKORA JONAS": ["Pasteur", 100000, "Abidjan Nord"],
        "KOUAKOU Shadrac": ["Pasteur", 60000, "Abidjan Nord"],
        "HEDILON YAO": ["Pasteur", 100000, "Abidjan Nord"],
    }

st.title("🛡️ APPLICATION DE GESTION MIEDA")

# Onglets
tab_gen, tab_dime, tab_offr, tab_past = st.tabs(["🌍 Général", "💰 Rapport Dîme", "🕊️ Offrandes", "👨‍💼 Pasteurs"])

with tab_gen:
    col1, col2 = st.columns(2)
    region_sel = col1.selectbox("🌍 Région :", ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"])
    mois_sel = col1.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = col2.text_input("📍 District :")

with tab_dime:
    # Saisie selon votre structure
    d_mois = st.number_input("Dîme du mois:", value=2421800)
    l_temple = st.number_input("Loyer temple:", value=240000)
    l_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    a_ch = st.number_input("Autres charges:", value=0)
    f_transf = st.number_input("Frais de transfert:", value=0)
    f_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    a_ress = st.number_input("Autres ressources/appro.:", value=0)

with tab_offr:
    # Saisie selon votre structure
    o_ord = st.number_input("Offrandes ordinaires:", value=0)
    d_offr = st.number_input("Dépenses sur offr. ord.:", value=0)
    g1 = st.number_input("1ère Action de Grâce:", value=0)
    s_dist = st.number_input("Soutien aux districts:", value=0)
    s_insp = st.number_input("Soutien Inspectorat:", value=0)
    s_soc = st.number_input("Soutien Aff. Sociales:", value=0)
    admin = st.number_input("Administration:", value=0)
    evang = st.number_input("Evangélisation:", value=0)
    g2 = st.number_input("2ème Action de Grâce:", value=0)

with tab_past:
    st.write(f"### Versements : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    saisies_v = {}
    for nom, infos in p_reg.items():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{nom}**")
        saisies_v[nom] = c2.number_input("Versé", value=infos[1], key=f"s_{nom}", label_visibility="collapsed")

# GÉNÉRATION DU RAPPORT UNIQUE DÉTAILLÉ
st.divider()
if st.button("Générer le Bilan Intégral"):
    st.success(f"Rapport consolidé pour {region_sel} - {mois_sel}")
    
    # 1. Préparation des données Dîmes (avec prélèvement 10%)
    dime_10 = d_mois * 0.10
    d_rows = [
        ("Dîme du mois", d_mois), ("Dîme des Dîmes (10%)", -dime_10), ("Loyer temple", -l_temple),
        ("Loyer résidence Pasteurs", -l_res), ("Autres charges", -a_ch), 
        ("Frais transfert/transport", -(f_transf + f_transp)), ("Autres ressources", a_ress)
    ]
    
    # 2. Préparation des données Offrandes
    o_rows = [
        ("Offrandes ordinaires", o_ord), ("Dépenses sur offrandes", -d_offr), ("1ère Action de Grâce", g1),
        ("2ème Action de Grâce", g2), ("Soutien aux districts", s_dist), ("Soutien Inspectorat", s_insp),
        ("Soutien Aff. Sociales", s_soc), ("Administration / Evang.", admin + evang)
    ]
    
    # 3. Création du tableau fusionné (Mois, Region, Libellé Dimes, Montant Dimes, Libellé Offrande, Montant Offrande)
    consolidated = []
    for i in range(max(len(d_rows), len(o_rows))):
        l_d, m_d = d_rows[i] if i < len(d_rows) else ("", "")
        l_o, m_o = o_rows[i] if i < len(o_rows) else ("", "")
        consolidated.append({
            "Mois": mois_sel, "Region": region_sel,
            "Libellé Dimes": l_d, "Montant Dimes": f"{int(m_d):,} F" if m_d != "" else "",
            "Libellé Offrande": l_o, "Montant Offrande": f"{int(m_o):,} F" if m_o != "" else ""
        })
    
    df_unique = pd.DataFrame(consolidated)
    st.subheader("📊 Rapport Intégral Détaillé")
    st.table(df_unique)

    # 4. Section Soutiens aux Pasteurs
    st.subheader("👨‍💼 Détail des Soutiens aux Pasteurs")
    df_p = pd.DataFrame([{"Pasteur": k, "Salaire Versé": f"{v:,} F"} for k, v in saisies_v.items()])
    st.table(df_p)

    # Export Excel (Correction du bug xlsxwriter)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_unique.to_excel(writer, sheet_name='Bilan Detaillé', index=False)
        df_p.to_excel(writer, sheet_name='Soutiens Pasteurs', index=False)
    
    st.download_button(
        label="📥 Télécharger le Rapport Excel",
        data=output.getvalue(),
        file_name=f"Rapport_MIEDA_{region_sel}_{mois_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
