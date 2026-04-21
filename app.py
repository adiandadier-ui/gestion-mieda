import streamlit as st
import pandas as pd
import io

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="APPLICATION DE GESTION MIEDA", layout="wide")

# 2. STYLE VISUEL (Bouton Bleu et Onglets)
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

# 3. GESTION DE LA MÉMOIRE DYNAMIQUE (Session State)
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
    if "Abidjan Sud" not in regions_existantes: regions_existantes.append("Abidjan Sud")
    
    col_a, col_b = st.columns(2)
    region_sel = col_a.selectbox("🌍 Région :", regions_existantes)
    mois_sel = col_a.selectbox("📅 Mois :", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"])
    district_sel = col_b.text_input("📍 District :", placeholder="Nom du district")

# --- ONGLET RAPPORT DÎME (Structure conservée selon photo) ---
with tab_dime:
    dime_mois = st.number_input("Dîme du mois:", value=2421800)
    loyer_temple = st.number_input("Loyer temple:", value=240000)
    loyer_res = st.number_input("Loyer résidence Pasteurs:", value=510000)
    autres_ch = st.number_input("Autres charges:", value=0)
    frais_transf = st.number_input("Frais de transfert:", value=0)
    frais_transp = st.number_input("Frais de transport:", value=0)
    perdiem = st.number_input("Perdiem Gestion:", value=0)
    autres_ress = st.number_input("Autres ressources/appro.:", value=0)

# --- ONGLET OFFRANDES (Structure conservée selon photo) ---
with tab_offr:
    offr_ord = st.number_input("Offrandes ordinaires:", value=0)
    dep_offr = st.number_input("Dépenses sur offr. ord.:", value=0)
    act_grace1 = st.number_input("1ère Action de Grâce:", value=0)
    sout_dist = st.number_input("Soutien aux districts:", value=0)
    sout_insp = st.number_input("Soutien Inspectorat:", value=0)
    sout_soc = st.number_input("Soutien Aff. Sociales:", value=0)
    admin = st.number_input("Administration:", value=0)
    evang = st.number_input("Evangélisation:", value=0)
    act_grace2 = st.number_input("2ème Action de Grâce:", value=0)
    
    total_offr_net = (offr_ord - dep_offr) + act_grace1 + act_grace2 + sout_dist + sout_insp + sout_soc + admin + evang

# --- ONGLET LISTE PASTEURS ---
with tab_past:
    st.write(f"### Soutiens pour la région : {region_sel}")
    p_reg = {k: v for k, v in st.session_state.base_pasteurs.items() if v[2] == region_sel}
    saisies_soutiens = {}
    for nom, infos in p_reg.items():
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{nom}** ({infos[0]})")
        saisies_soutiens[nom] = c2.number_input("Salaire versé", value=infos[1], key=f"v_{nom}", label_visibility="collapsed")

# --- ONGLET CONFIGURATION (Ajout de pasteurs) ---
with tab_config:
    st.subheader("⚙️ Ajouter un nouveau pasteur")
    with st.form("new_member"):
        n_nom = st.text_input("Nom et Prénoms")
        n_grade = st.selectbox("Grade", ["Pasteur", "Evangéliste", "Missionnaire"])
        n_prevu = st.number_input("Montant prévu", value=50000, step=5000)
        n_reg = st.selectbox("Région d'affectation", ["Abidjan Nord", "Abidjan Sud", "Bouaké", "San-Pedro"])
        if st.form_submit_button("Enregistrer"):
            if n_nom:
                st.session_state.base_pasteurs[n_nom.upper()] = [n_grade, n_prevu, n_reg]
                st.rerun()

# --- GÉNÉRATION DU RAPPORT FINAL ---
st.divider()
if st.button("Générer le Bilan Intégral"):
    # Calcul de la dîme nette (moins 10% de prélèvement)
    dime_nette = dime_mois * 0.90
    
    st.success("Bilan généré avec succès !")
    
    # TABLEAU 1 : BILAN GLOBAL
    st.subheader("📊 Tableau de Synthèse Régionale")
    df_bilan = pd.DataFrame([{
        "Mois": mois_sel,
        "Region": region_sel,
        "Dimes": f"{int(dime_nette):,} F",
        "Offrande": f"{int(total_offr_net):,} F"
    }])
    st.table(df_bilan)

    # TABLEAU 2 : DÉTAIL PASTEURS
    st.subheader("👨‍💼 Détail des Soutiens Versés")
    liste_p = []
    for nom, salaire in saisies_soutiens.items():
        liste_p.append({"Pasteur": nom, "Salaire": f"{int(salaire):,} F"})
    
    df_pasteurs = pd.DataFrame(liste_p)
    st.table(df_pasteurs)

    # EXPORT EXCEL
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_bilan.to_excel(writer, sheet_name='Bilan Global', index=False)
        df_pasteurs.to_excel(writer, sheet_name='Détail Pasteurs', index=False)
    
    st.download_button(
        label="📥 Télécharger le Rapport (Excel)",
        data=output.getvalue(),
        file_name=f"Rapport_MIEDA_{region_sel}_{mois_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
