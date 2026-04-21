import pandas as pd
import ipywidgets as widgets
from IPython.display import display, clear_output

# --- 1. BASE DE DONNÉES COMPLÈTE DES PASTEURS ---
# Structure : "Nom": [Grade, Soutien Prévu, Région]
base_pasteurs_data = {
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
    "Yoboué Celestin": ["Gestionnaire Distri", 50000, "Abidjan Nord"],
    "BOUA Clémentine": ["Evangéliste", 100000, "Abidjan Nord"],
    "KOUAKOU Kouamé": ["Evangéliste", 100000, "Abidjan Nord"],
    "Colette": ["Evangéliste", 100000, "Abidjan Nord"],
    "GNAGNE Paul": ["Pasteur", 100000, "Abidjan Nord"],
    "Yao Pierre": ["Pasteur", 50000, "Abidjan Nord"],
    "EXEMPLE SUD 1": ["Pasteur", 75000, "Abidjan Sud"],
}

# --- 2. CRÉATION DES WIDGETS DE L'INTERFACE ---
style = {'description_width': '180px'}
layout_large = widgets.Layout(width='450px')

# ONGLET 1 : GÉNÉRAL & RÉGION
region_select = widgets.Dropdown(options=["Abidjan Nord", "Abidjan Sud"], value="Abidjan Nord", description="🌍 Région :", style=style, layout=layout_large)
mois_select = widgets.Dropdown(options=["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"], description="📅 Mois :", style=style, layout_large=layout_large)
district_w = widgets.Text(placeholder='Nom du district', description="📍 District :", style=style, layout=layout_large)

# ONGLET 2 : RAPPORT DÎME
dime_mois = widgets.IntText(value=2421800, description="Dîme du mois:", style=style)
loyer_temple = widgets.IntText(value=240000, description="Loyer temple:", style=style)
loyer_res_p = widgets.IntText(value=510000, description="Loyer rés. Pasteurs:", style=style)
autres_charges = widgets.IntText(value=0, description="Autres charges:", style=style)
fr_transfert = widgets.IntText(value=0, description="Frais de transfert:", style=style)
fr_transport = widgets.IntText(value=0, description="Frais de transport:", style=style)
perdiem = widgets.IntText(value=0, description="Perdiem Gestion:", style=style)
appro_ress = widgets.IntText(value=0, description="Autres ressources/appro.:", style=style)

# ONGLET 3 : RAPPORT OFFRANDES
offr_ord = widgets.IntText(value=0, description="Offrandes ordinaires:", style=style)
dep_offr_ord = widgets.IntText(value=0, description="Dépenses sur offr. ord.:", style=style)
offr_1_ag = widgets.IntText(value=0, description="1ère Action de Grâce:", style=style)
sout_district = widgets.IntText(value=0, description="Soutien aux districts:", style=style)
sout_insp = widgets.IntText(value=0, description="Soutien Inspectorat:", style=style)
sout_social = widgets.IntText(value=0, description="Soutien Aff. Sociales:", style=style)
sout_admin = widgets.IntText(value=0, description="Soutien Administration:", style=style)
sout_evang = widgets.IntText(value=0, description="Soutien Evangélisation:", style=style)
offr_2_ag = widgets.IntText(value=0, description="2ème Action de Grâce:", style=style)

# ONGLET 4 : LISTE EXHAUSTIVE PASTEURS (DYNAMIQUE)
container_saisies_p = widgets.VBox([])

def rafraichir_liste_p(change):
    region_choisie = region_select.value
    pasteurs_region = {k: v for k, v in base_pasteurs_data.items() if v[2] == region_choisie}
    widgets_liste = []
    for nom in pasteurs_region:
        label = widgets.Label(value=f"{nom} ({pasteurs_region[nom][0]})", layout=widgets.Layout(width='280px'))
        saisie = widgets.IntText(value=0, description="Versé:", style={'description_width': '50px'})
        saisie.add_class("input-soutien") # Classe pour identifier les widgets de saisie
        widgets_liste.append(widgets.HBox([label, saisie]))
    container_saisies_p.children = widgets_liste

region_select.observe(rafraichir_liste_p, names='value')
rafraichir_liste_p(None) # Init

# --- 3. LOGIQUE DE CALCUL GLOBAL ---
btn_generer = widgets.Button(description="Générer le Bilan Intégral", button_style='primary', layout=widgets.Layout(width='98%', height='40px', margin='10px 0px'))
out_final = widgets.Output()

def calculer_tout(b):
    with out_final:
        clear_output()
        
        # 1. Calculs Financiers (Dîme & Offrandes)
        d_10 = dime_mois.value * 0.10
        reste_apres_10 = dime_mois.value - d_10
        total_dep_dime = loyer_temple.value + loyer_res_p.value + autres_charges.value + fr_transfert.value + fr_transport.value + perdiem.value
        total_dispo = (reste_apres_10 - total_dep_dime) + appro_ress.value
        total_offr_spec = offr_1_ag.value + sout_district.value + sout_insp.value + sout_social.value + sout_admin.value + sout_evang.value + offr_2_ag.value
        
        # 2. Traitement Liste Pasteurs
        resultats_p = []
        total_verse_region = 0
        for hbox in container_saisies_p.children:
            nom_p = hbox.children[0].value.split(" (")[0]
            m_verse = hbox.children[1].value
            grade_p = base_pasteurs_data[nom_p][0]
            prevu_p = base_pasteurs_data[nom_p][1]
            total_verse_region += m_verse
            resultats_p.append([nom_p, grade_p, f"{prevu_p:,}", f"{m_verse:,}", f"{m_verse - prevu_p:,}"])

        # 3. Affichage
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📊 BILAN CONSOLIDÉ - {mois_select.value.upper()} | RÉGION : {region_select.value.upper()}")
        if district_w.value: print(f"📍 DISTRICT : {district_w.value}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Tableau 1 : Synthèse Financière
        df_finance = pd.DataFrame({
            "Rubrique": ["Dîme du mois", "Dîme des Dîmes (10%)", "RESSOURCE DISPONIBLE", "TOTAL OFFRANDES SPÉCIALES", "TOTAL SOUTIENS VERSÉS"],
            "Montant (F CFA)": [f"{dime_mois.value:,}", f"{d_10:,}", f"{total_dispo:,}", f"{total_offr_spec:,}", f"{total_verse_region:,}"]
        })
        display(df_finance)
        
        print(f"\n📋 DÉTAIL EXHAUSTIF DES SOUTIENS (Région {region_select.value})")
        df_p = pd.DataFrame(resultats_p, columns=["Nom et Prénom", "Grade", "Soutien Prévu", "Soutien Versé", "Écart"])
        display(df_p)

btn_generer.on_click(calculer_tout)

# --- 4. ASSEMBLAGE DES ONGLETS ---
tab_gen = widgets.VBox([region_select, mois_select, district_w])
tab_dime = widgets.VBox([dime_mois, loyer_temple, loyer_res_p, autres_charges, fr_transfert, fr_transport, perdiem, appro_ress])
tab_offr = widgets.VBox([offr_ord, dep_offr_ord, offr_1_ag, sout_district, sout_insp, sout_social, sout_admin, sout_evang, offr_2_ag])
tab_past = widgets.VBox([widgets.HTML("<b>Saisir les soutiens pour la région sélectionnée :</b>"), container_saisies_p])

tabs = widgets.Tab(children=[tab_gen, tab_dime, tab_past, tab_past]) # Note: tab_past est utilisé pour l'onglet exhaustif
tabs = widgets.Tab(children=[tab_gen, tab_dime, tab_offr, tab_past])

tabs.set_title(0, '🌍 Général')
tabs.set_title(1, '💰 Rapport Dîme')
tabs.set_title(2, '🕊️ Offrandes')
tabs.set_title(3, '👨‍💼 Liste Pasteurs')

display(widgets.HTML("<h2>📝 APPLICATION DE GESTION MIEDA</h2>"), tabs, btn_generer, out_final)
