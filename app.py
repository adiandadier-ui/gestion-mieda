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

# 4. STRUCTURE DES ONGLETS
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

# --- ONGLET RAPPORT DÎME (Détail conservé) ---
with tab_dime:
    d_mois = st.number_input("Dîme du mois:", value=2421800)
    l_temple = st.number_input("Loyer temple:", value=240000)
    l_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    a_ch = st.number_input("Autres charges:", value=0)
    f_transf = st.number_input("Frais de transfert:", value=0)
    f_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    a_ress = st.number_input("Autres ressources/appro.:", value=0)

# --- ONGLET OFFRANDES (Détail conservé) ---
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
    st.write(f"### Versements : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    for nom, infos in p_reg.items():
        st.write(f"**{nom}** ({infos[0]})")

# --- GÉNÉRATION DU TABLEAU UNIQUE ---
st.divider()
if st.button("Générer le Bilan Consolidé"):
    st.success(f"Rapport consolidé pour {region_sel} - {mois_sel}")
    
    # 1. Préparation des listes de données détaillées
    # On calcule la Dîme des Dîmes (10%) pour l'inclure dans le détail
    dime_10 = d_mois * 0.10
    
    dimes_list = [
        ("Dîme du mois", d_mois),
        ("Dîme des Dîmes (10%)", -dime_10),
        ("Loyer temple", -l_temple),
        ("Loyer résidence Pasteurs", -l_res),
        ("Autres charges", -a_ch),
        ("Frais transfert/transport", -(f_transf + f_transp)),
        ("Perdiem Gestion", -perdiem),
        ("Autres ressources", a_ress)
    ]
    
    offrandes_list = [
        ("Offrandes ordinaires", o_ord),
        ("Dépenses sur offrandes", -d_offr),
        ("1ère Action de Grâce", g1),
        ("2ème Action de Grâce", g2),
        ("Soutien aux districts", s_dist),
        ("Soutien Inspectorat", s_insp),
        ("Soutien Aff. Sociales", s_soc),
        ("Administration / Evang.", admin + evang)
    ]
    
    # 2. Création du tableau fusionné (alignement des lignes)
    consolidated_data = []
    max_rows = max(len(dimes_list), len(offrandes_list))
    
    for i in range(max_rows):
        lib_dime, mont_dime = dimes_list[i] if i < len(dimes_list) else ("", "")
        lib_offr, mont_offr = offrandes_list[i] if i < len(offrandes_list) else ("", "")
        
        consolidated_data.append({
            "Mois": mois_sel,
            "Region": region_sel,
            "Libellé Dimes": lib_dime,
            "Montant Dimes": f"{int(mont_dime):,} F" if mont_dime != "" else "",
            "Libellé Offrande": lib_offr,
            "Montant Offrande": f"{int(mont_offr):,} F" if mont_offr != "" else ""
        })
    
    df_unique = pd.DataFrame(consolidated_data)
    
    # 3. Affichage du tableau unique
    st.subheader("📊 Rapport Intégral (Dîmes & Offrandes)")
    st.table(df_unique)

    # EXPORT EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_unique.to_excel(writer, sheet_name='Bilan Consolidé', index=False)
    
    st.download_button(
        label="📥 Télécharger le Rapport Unique (Excel)",
        data=output.getvalue(),
        file_name=f"Rapport_Consolide_MIEDA_{region_sel}_{mois_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
