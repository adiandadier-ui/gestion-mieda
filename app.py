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
    }
    </style>
    """, unsafe_allow_html=True)

# 3. BASE DE DONNÉES (Session State pour conserver les ajouts)
if 'base_pasteurs' not in st.session_state:
    st.session_state.base_pasteurs = {
        "KOKORA JONAS": ["Pasteur", 100000, "Abidjan Nord"],
        "KOUAKOU Shadrac": ["Pasteur", 60000, "Abidjan Nord"],
        "HEDILON YAO": ["Pasteur", 100000, "Abidjan Nord"],
    }

st.title("🛡️ APPLICATION DE GESTION MIEDA")

# 4. STRUCTURE DES ONGLETS (Réintégration de l'onglet Configuration)
tab_gen, tab_dime, tab_offr, tab_past, tab_config = st.tabs([
    "🌍 Général", "💰 Rapport Dîme", "🕊️ Offrandes", "👨‍💼 Pasteurs", "⚙️ Configuration"
])

# --- ONGLET GÉNÉRAL ---
with tab_gen:
    col1, col2 = st.columns(2)
    regions_dispo = ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"]
    region_sel = col1.selectbox("🌍 Région :", regions_dispo)
    mois_sel = col1.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = col2.text_input("📍 District :")

# --- ONGLET RAPPORT DÎME ---
with tab_dime:
    d_mois = st.number_input("Dîme du mois:", value=2421800)
    l_temple = st.number_input("Loyer temple:", value=240000)
    l_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    a_ch = st.number_input("Autres charges:", value=0)
    f_transf = st.number_input("Frais de transfert:", value=0)
    f_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    a_ress = st.number_input("Autres ressources/appro.:", value=0)

# --- ONGLET OFFRANDES ---
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

# --- ONGLET PASTEURS (Saisie des versements) ---
with tab_past:
    st.write(f"### Versements : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    saisies_v = {}
    for nom, infos in p_reg.items():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{nom}** ({infos[0]})")
        saisies_v[nom] = c2.number_input("Versé", value=infos[1], key=f"s_{nom}", label_visibility="collapsed")

# --- ONGLET CONFIGURATION (AJOUT DE PASTEUR) ---
with tab_config:
    st.subheader("⚙️ Ajouter un nouveau Pasteur")
    with st.form("form_ajout_pasteur"):
        c_nom = st.text_input("Nom et Prénoms")
        c_grade = st.selectbox("Grade", ["Pasteur", "Evangéliste", "Stagiaire"])
        c_montant = st.number_input("Montant prévu (Salaire de base)", value=50000)
        c_region = st.selectbox("Région d'affectation", regions_dispo)
        
        submit_add = st.form_submit_button("Ajouter à la liste")
        
        if submit_add and c_nom:
            st.session_state.base_pasteurs[c_nom.upper()] = [c_grade, c_montant, c_region]
            st.success(f"{c_nom} ajouté avec succès !")
            st.rerun()

# --- GÉNÉRATION DU BILAN ---
st.divider()
if st.button("Générer le Bilan Intégral"):
    st.success(f"Rapport consolidé pour {region_sel} - {mois_sel}")
    
    # 1. Préparation des données Dîmes (avec prélèvement 10%)
    dime_10 = d_mois * 0.10
    d_rows = [
        ("Dîme du mois", d_mois), ("Dîme des Dîmes (10%)", -dime_10), ("Loyer temple", -l_temple),
        ("Loyer résidence Pasteurs", -l_res), ("Autres charges", -a_ch), 
        ("Frais transfert/transport", -(f_transf + f_transp)), ("Perdiem Gestion", -perdiem), ("Autres ressources", a_ress)
    ]
    
    # 2. Préparation des données Offrandes
    o_rows = [
        ("Offrandes ordinaires", o_ord), ("Dépenses sur offrandes", -d_offr), ("1ère Action de Grâce", g1),
        ("2ème Action de Grâce", g2), ("Soutien aux districts", s_dist), ("Soutien Inspectorat", s_insp),
        ("Soutien Aff. Sociales", s_soc), ("Administration / Evang.", admin + evang)
    ]
    
    # 3. Création du tableau fusionné
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

    # EXPORT EXCEL (Utilise xlsxwriter - n'oubliez pas de l'ajouter au requirements.txt)
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
