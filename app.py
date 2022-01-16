#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import load_functions as fn
import utils_functions as utils

#temporaire certif ssl HS
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(layout="wide")
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;} </style>', unsafe_allow_html=True)
STREAMLIT_GLOBAL_SHOW_WARNING_ON_DIRECT_EXECUTION=False

###-----MAPPING DICTS---###
dict_vac_statut = {'Primo dose récente': 'Primo dose',
                   'Primo dose efficace': 'Primo dose',
                   'Complet entre 3 mois et 6 mois - sans rappel': '2 doses sans rappel',
                   'Complet de moins de 3 mois - avec rappel': '3 doses',
                   'Complet de moins de 3 mois - sans rappel': '2 doses sans rappel',
                   'Complet entre 3 mois et 6 mois - avec rappel': '3 doses',
                   'Complet de 6 mois et plus - sans rappel': '2 doses sans rappel',
                   'Complet de 6 mois et plus - avec rappel': '3 doses',
                   'Non-vaccinés': 'Non-vaccinés'}
dict_vac_statut_new_colors = {'Non-vaccinés': 'rgb(44, 160, 44)', #green
          '3 doses': 'rgb(255, 127, 14)', #orange
          '2 doses sans rappel': 'rgb(31, 119, 180)', #blue
          'Primo dose': 'rgb(214, 39, 40)'} #red
dict_ageclasse = {9: "[0-9]", 19: "[10-19]", 29: "[20-29]", 39: "[30-39]", 49: "[40-49]", 59: "[50-59]", 69: "[60-69]", 79: "[70-79]", 89: "[80-89]", 90: "[90-...]"}
dict_ageclasse_group = {9: "[0-29]", 19: "[0-29]", 29: "[0-29]", 39: "[30-59]", 49: "[30-59]", 59: "[30-59]", 69: "[60-79]", 79: "[60-79]", 89: "[80-...]", 90: "[80-...]"} 
dict_regions = {1: 'GUADELOUPE',2: 'MARTINIQUE',3: 'GUYANNE',4: 'LA RÉUNION',6: 'MAYOTTE',
                11: 'ILE-DE-FRANCE',24: 'CENTRE-VAL DE LOIRE',27: 'BOURGOGNE-FRANCHE-COMTÉ',28: 'NORMANDIE',
                32: 'HAUTS-DE-FRANCE',44: 'GRAND EST',52:'PAYS DE LA LOIRE',53: 'BRETAGNE', 75: 'NOUVELLE-AQUITAINE',
                76: 'OCCITANIE',84:'AUVERGNE-RHÔNE-ALPES',93:  'PROVENCE-ALPES-CÔTE D\'AZUR',94:'CORSE'}
dict_scansante_classes_ages = {'[0-16]': '[0-25]','[17-25]': '[0-25]','[26-45]': '[26-55]','[46-55]': '[26-55]','[56-70]': '[56-80]','[70-80]': '[56-80]','[80-…]': '[80-...]','[80-...]': '[80-...]'}
dict_radio_var = {"Nombre de décès de patients hospitalisés":"dc",
                  "Nombre d'entrées en soins critiques":"sc",
                  "Nombre d'entrées de patients en hospitalisation complète":"hc",
                  "Nombre de tests PCR positifs prélevés":"nb_pcr0",
                  "Nombre de tests PCR prélevés":"nb_pcr"}
dict_select_month = {"Décembre":"-12-",
                     "Novembre":"-11-",
                     "Octobre":"-10-",
                     "Septembre":"-09-",
                     "Août":"-08-",
                     "Juillet": "-07-",
                     "Juin": "-06-",
                     "Mai": "-05-",
                     "Avril": "-04-",
                     "Mars": "-03-",
                     "Février": "-02-",
                     "Janvier": "-01-"}

###-----DATA PROCESSING FUNCTIONS---###
def prepare_covidappa_data(data):
    df = pd.json_normalize(data["records"], max_level=1)
    df = df.drop(['datasetid','record_timestamp','recordid'], axis=1)
    df.columns = [x.replace('fields.', '') for x in df.columns if 'fields' in x]
    df["vac_statut_new"] = df["vac_statut"].map(dict_vac_statut)
    df["annee"] = df['date'].apply(lambda x: x.partition("-")[0])
    df = utils.calcul_rate(df,'positive_rate','nb_pcr','nb_pcr0')
    return df

def prepare_covidhebdo_data(data):
    df= data.loc[data['cl_age90'] == 0]
    df["subst_annee"] = df['Semaine'].apply(lambda x: x.partition("-")[0])
    df["substr_semaine"] = df['Semaine'].apply(lambda x: x.partition("-")[2])
    return df

def prepare_covidhebdopivot_data(data,year,start,end):
    df = data.loc[data['cl_age90'] != 0]
    df["annee"] = df['Semaine'].apply(lambda x: x.partition("-")[0])
    df['reg_label'] = df["reg"].map(dict_regions)
    df['cl_age90_classe'] = df['cl_age90'].map(dict_ageclasse)
    df['cl_age90_group'] = df['cl_age90'].map(dict_ageclasse_group)
    return df[(df.annee == year) & (df.Semaine >= year+"-"+start) & (df.Semaine <= year+"-"+end)].groupby(['reg_label','cl_age90_group']).NewAdmHospit.sum().unstack().reset_index()

###-----PARAMS---###
DATADREES_DATA_API = 'https://data.drees.solidarites-sante.gouv.fr/api/records/1.0/search/'
DATASET_COVIDAPPA = 'covid-19-resultats-issus-des-appariements-entre-si-vic-si-dep-et-vac-si'
DATAGOUV_DATA_API = 'https://www.data.gouv.fr/fr/datasets/r/'
DATASET_COVIDHEBDO = 'dc7663c7-5da9-4765-a98b-ba4bc9de9079'
SCANSANTE_DATA_URL = 'https://www.scansante.fr/applications/caracteristiques-des-sejours-par-region/submit'
LOCALDATA_SCANSANTE_PATIENTS_SEJOURS = 'scansante_sejours_patiens_regions_2018-2020'
LOCALDATA_SCANSANTE_PATIENTS_SEJOURS_AGES = 'scansante_sejours_regions_ages_2018-2020'
LOCALDATA_SCANSANTE_CMD = 'scansante_activite_cmd_2018_2020'

###-----DATAFRAMES---###
df_covidappa = fn.chain(fn.load_json_data(DATADREES_DATA_API,DATASET_COVIDAPPA,3000), prepare_covidappa_data).convert_dtypes()
df_covidhebdo = fn.chain(fn.load_csv_data(DATAGOUV_DATA_API,DATASET_COVIDHEBDO), prepare_covidhebdo_data).convert_dtypes()
df_local_scansante = fn.load_excel_data(LOCALDATA_SCANSANTE_PATIENTS_SEJOURS)
df_local_scansante_age = fn.load_excel_data(LOCALDATA_SCANSANTE_PATIENTS_SEJOURS_AGES)
df_scrap_scansante = fn.html_scrapper(SCANSANTE_DATA_URL,{'annee': 2021,'type_etab': 0, 'type_restit': 2},1)
df_scrap_age1 = fn.html_scrapper(SCANSANTE_DATA_URL,{'annee': 2021,'type_etab': 0, 'type_restit': 4},1)
df_scrap_age2 =  fn.html_scrapper(SCANSANTE_DATA_URL,{'annee': 2021,'type_etab': 0, 'type_restit': 4},2)
df_local_scansante_cmd = fn.load_excel_data(LOCALDATA_SCANSANTE_CMD)

###-----LAYOUT---###

#Sidebar
st.sidebar.markdown('''
# Paramètres des graphiques
### Graphiques en aires
''')
selected_norm = st.sidebar.radio('Selectionner un type de données', ["Données normalisées","Données brutes"])

st.sidebar.markdown('''
# Sections
### Covid
- [Chiffres-clés par date et selon le statut vaccinal](#chiffres-cl-s-par-date-et-selon-le-statut-vaccinal-2-me-semestre-2021)
  - [Nombre d'hospitalisations, d'entrées en soins critiques et de décès](#nombre-de-tests-pcr-d-hospitalisations-d-entr-es-en-soins-critiques-et-de-d-c-s)
  - [Taux de positivité](#taux-de-positivit)
- [Nombre hebdomadaire de nouvelles hospitalisations : totaux par régions, structures par classes d'âge, comparatifs 2020-2021](#nombre-hebdomadaire-de-nouvelles-hospitalisations-totaux-par-r-gions-structures-par-classes-d-ge-comparatifs-2020-2021)
  - [Totaux hebdomadaires de nouvelles hospitalisations](#totaux-hebdomadaires-de-nouvelles-hospitalisations)
  - [Nouvelles hospitalisations : totaux par régions, structure par classes d'âge](#nouvelles-hospitalisations-totaux-par-r-gions-structure-par-classes-d-ge)
### Activité hospitalière globale 2018-2021
- [Caractéristiques des séjours et patients par région et par classes d'âge](#caract-ristiques-des-s-jours-et-patients-par-r-gion-et-par-classes-d-ge)
  - [Totaux de séjours et de patients par région](#totaux-de-s-jours-et-de-patients-par-r-gion)
  - [Séjours : totaux par région, structure par classes d'âges (détail des plus de 16 ans)](#s-jours-totaux-par-r-gion-structure-par-classes-d-ges-d-tail-des-plus-de-16-ans)
- [Fiche nationale toutes activités, champ MCO](#fiche-nationale-toutes-activit-s-champ-mco)
  - [Séjours : Déclinaison par catégorie majeure de diagnostic, taux de progression 2018/2019 et 2019/2020](#s-jours-d-clinaison-par-cat-gorie-majeure-de-diagnostic-taux-de-progression-2018-2019-et-2019-2020)
''', unsafe_allow_html=True)

st.sidebar.markdown('''
***
##### Code source
[https://github.com/gegedenice/covid-nodramadata](https://github.com/gegedenice/covid-nodramadata)
##### Licence
MIT Licence
''')

#main section 1
st.title('Données Covid')
#section 1.1
st.header("Chiffres-clés par date et selon le statut vaccinal (à partir du 2ème semestre 2021)")
with st.expander("Cliquer pour développer et voir les données - Source des données : Data.drees.solidarites-sante.gouv.fr - "):
     st.write("""
         **Données statistiques publiques en santé et social**

         * url du jeu de données : [https://data.drees.solidarites-sante.gouv.fr/explore/dataset/covid-19-resultats-issus-des-appariements-entre-si-vic-si-dep-et-vac-si/information/](https://data.drees.solidarites-sante.gouv.fr/explore/dataset/covid-19-resultats-issus-des-appariements-entre-si-vic-si-dep-et-vac-si/information/)
         * Méthodo commentée : [https://drees.solidarites-sante.gouv.fr/communique-de-presse/exploitation-des-appariements-entre-les-bases-si-vic-si-dep-et-vac-si-des](https://drees.solidarites-sante.gouv.fr/communique-de-presse/exploitation-des-appariements-entre-les-bases-si-vic-si-dep-et-vac-si-des)
        
         **Collecte des données**

         L'intégralité du dataset est récupéré en json par requête sur l'API (documentée [ici](https://data.drees.solidarites-sante.gouv.fr/explore/dataset/covid-19-resultats-issus-des-appariements-entre-si-vic-si-dep-et-vac-si/api/?disjunctive.vac_statut&sort=-date))
         
         **Retraitements effectués**
         * Ajout d'une variable : regroupement des statuts vaccinaux en catégories plus larges Primo dose, 2 doses sans rappel, 3 doses, Non-vaccinés
         * Ajout d'une variable : taux de positivité (pourcentage des PCR positifs par rapport aux PCR effectués) calculé pour chque enregistrement
     """)
     st.dataframe(df_covidappa) 
#sub-section 1.1.1
with st.container():
    st.subheader("Nombre de tests PCR, d'hospitalisations, d'entrées en soins critiques et de décès")
    st.caption("Période : données du 31 mai 2021 à J-7")
    selected_var = st.radio('Selectionner une variable ',dict_radio_var.keys())
    selected_vactype = st.radio('Selectionner le type de statut vaccinal', ["Statut vaccinal - regroupements de catégories","Statut vaccinal - catégories d'origine"])
    st.warning('Variables choisies :  **'+selected_var+', '+selected_vactype+'**')
    col1,col2 = st.columns((3,1))
    with col1:
        if selected_vactype == "Statut vaccinal - catégories d'origine":
            fig111_bar = px.bar(df_covidappa, x='date', y=dict_radio_var[selected_var], color='vac_statut', template='xgridoff', labels={dict_radio_var[selected_var]: selected_var}, height=600)
        elif selected_vactype == "Statut vaccinal - regroupements de catégories":
            df_agg = df_covidappa.groupby(['date', 'vac_statut_new']).agg(data_sum=(dict_radio_var[selected_var], 'sum')).reset_index()
            fig111_bar = px.bar(df_agg, x='date', y='data_sum', color='vac_statut_new',color_discrete_map=dict_vac_statut_new_colors, labels={'data_sum': selected_var}, height=600)
        fig111_bar.update_layout(legend_title_text=selected_vactype)
        fig111_bar.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))
        fig111_bar.update_layout(autosize=True)
        st.plotly_chart(fig111_bar,use_container_width=True)
    with col2:
        st.markdown('''##### Synthèse mensuelle''')
        selected_year = st.selectbox("Sélectionner une année",["2021","2022"])
        selected_month = st.selectbox("Sélectionner un mois de l'année",dict_select_month.keys())
        df_month = df_covidappa.loc[(df_covidappa['date'].str.contains(dict_select_month[selected_month], case=False, regex=False, na=False)) & (df_covidappa['annee'] == selected_year)]
        fig111_pie = px.pie(df_month, names='vac_statut_new', values=dict_radio_var[selected_var],color='vac_statut_new',color_discrete_map=dict_vac_statut_new_colors,height=400)
        #fig111_pie.update_layout(legend_title_text='Statut vaccinal - regroupements de catégories')
        fig111_pie.update_layout(legend=dict(orientation="h"))
        fig111_pie.update_layout(autosize=True)
        st.plotly_chart(fig111_pie,use_container_width=True)

#sub-section 1.1.2
with st.container():
    st.subheader("Taux de positivité")
    st.caption("Période : données du 31 mai 2021 à J-7")
    fig112 = px.line(df_covidappa.sort_values(by=['date'], ascending=[True]), x='date', y='positive_rate', color='vac_statut')
    fig112.update_traces(mode='lines+markers')
    fig112.update_yaxes(title_text='taux de positivité')
    fig112.update_layout(legend_title_text="Statut vaccinal - catégories d'origine")
    fig112.update_layout(autosize=True)
    st.plotly_chart(fig112,use_container_width=True)

#section 1.2
st.header("Nombre hebdomadaire de nouvelles hospitalisations : totaux par régions, structures par classes d'âge, comparatifs 2020-2021")
with st.expander("Cliquer pour développer - Source des données : data.gouv.fr - "):
     st.write("""
         **Données hospitalières relatives à l'épidémie de COVID-19**

         * url d'accès aux jeux de données : [https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/](https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/)
         * Dataset : [donnees-hospitalieres-classe-age-hebdo-covid](https://www.data.gouv.fr/fr/datasets/r/dc7663c7-5da9-4765-a98b-ba4bc9de9079)
         
         **Collecte des données**
         
         L'intégralité du dataset est récupéré dynamiquement en csv par import à partir de son [url pérenne](https://www.data.gouv.fr/fr/datasets/r/dc7663c7-5da9-4765-a98b-ba4bc9de9079) 

         **Retraitements effectués**
 
         * Ajout d'une variable pour les totaux segmentés par classes d'âge : regroupement de classes d'âge en catégories plus larges [0-29], [30-59], [60-79], [80-...]
     """)
#sub-section 1.2.1
with st.container():
    st.subheader("Totaux hebdomadaires de nouvelles hospitalisations")
    with st.expander("Cliquer pour voir les données"):
        st.dataframe(df_covidhebdo)
    st.caption("Période : données de mars 2020 à 2021 S-1")
    df_semaine = df_covidhebdo.groupby(['substr_semaine', 'subst_annee']).agg(NewAdmHospit_sum=('NewAdmHospit', 'sum')).reset_index()
    fig121 = px.bar(df_semaine, x='substr_semaine', y='NewAdmHospit_sum', color='subst_annee', template='xgridoff',barmode='group')
    fig121.update_xaxes(title_text="semaines de l'année")
    fig121.update_yaxes(title_text='nouvelles hospitalisations')
    fig121.update_xaxes(categoryorder='category ascending')
    fig121.update_layout(legend_title_text="Année")
    fig121.update_layout(autosize=True)
    st.plotly_chart(fig121,use_container_width=True)
#sub-section 1.2.2
with st.container():
    st.subheader("Nouvelles hospitalisations : totaux par régions, structure par classes d'âge")
    st.caption("Période : données de mars 2020 à 2021, voir https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19 pour la dernière date de mise à jour des données 2021")
    col1, col2 = st.columns(2)
    cols = {1: col1, 2: col2}
    years = {1: "2020", 2: "2021"}
    datafs = {}
    v = {}
    for x in cols:
        with cols[x]:
            st.subheader(years[x])
            with st.expander("Cliquer pour voir les données"):
                st.dataframe(prepare_covidhebdopivot_data(fn.load_csv_data(DATAGOUV_DATA_API,DATASET_COVIDHEBDO),years[x],"S01","S53"))
            v["start_{0}".format(years[x])], v["end_{0}".format(years[x])] = st.select_slider('Sélectionner un intervalle',
                                                  options=df_covidhebdo[df_covidhebdo["subst_annee"] == years[x]]["substr_semaine"].unique(),
                                                  value=(df_covidhebdo[df_covidhebdo["subst_annee"] == years[x]]["substr_semaine"].unique()[0], df_covidhebdo[df_covidhebdo["subst_annee"] == years[x]]["substr_semaine"].unique()[-1]))
            st.write('Vous avez sélectionné les données de la semaine ', v["start_{0}".format(years[x])], ' à la semaine ', v["end_{0}".format(years[x])])
            datafs["df_covidhebdo4chart{0}".format(years[x])] = prepare_covidhebdopivot_data(fn.load_csv_data(DATAGOUV_DATA_API,DATASET_COVIDHEBDO),years[x],v["start_{0}".format(years[x])],v["end_{0}".format(years[x])])
            if selected_norm == "Données brutes":
                fig122 = px.area(datafs["df_covidhebdo4chart{0}".format(years[x])], x='reg_label', y=['[0-29]', '[30-59]', '[60-79]', '[80-...]'], template='xgridoff')               
            elif selected_norm == "Données normalisées":
                fig122 = px.area(datafs["df_covidhebdo4chart{0}".format(years[x])], x='reg_label', y=['[0-29]', '[30-59]', '[60-79]', '[80-...]'], groupnorm='percent', template='xgridoff')
            fig122.update_xaxes(title_text="régions")
            fig122.update_layout(legend_title_text="Classes d'âge")
            fig122.update_yaxes(title_text='nouvelles hospitalisations')
            fig122.update_layout(autosize=True)
            st.plotly_chart(fig122,use_container_width=True)

#main section 2
st.title('Activité hospitalière globale 2018-2021')
#section 2.1
st.header("Caractéristiques des séjours et patients par région et par classes d'âge")
with st.expander("Cliquer pour développer - Source des données : https://www.scansante.fr/"):
        st.write("""
        **Les données hospitalières**

        * url d'accès : [https://www.scansante.fr/applications/caracteristiques-des-sejours-par-region](https://www.scansante.fr/applications/caracteristiques-des-sejours-par-region)
        * Méthodo commentée : [https://www.scansante.fr/sites/www.scansante.fr/files/content/80/notice_caracteristiques_des_sejours_par_region_0.pdf](https://www.scansante.fr/sites/www.scansante.fr/files/content/80/notice_caracteristiques_des_sejours_par_region_0.pdf)

        **Retraitements effectués**

        * Compilation des nombres de séjours et nombre de patients des tableaux 2018, 2019, 2020 et 2021 en un seul dataset
        * Compilation manuelle pour la période 2018-2020, données incrémentales dynamiques (en temps réel) pour 2021
        * Ajout d'une variable : regroupement de classes d'âge en catégories plus larges [0-25], [26-55], [56-80], [80-...]
        """)
#section 2.1.1
with st.container():
    st.subheader("Totaux de séjours et de patients par région")
    temp = utils.remove_cols(df_scrap_scansante,[1,3,4,6])
    temp.columns = ['reg', 'sejours', 'patients']
    temp["annee"] = 2021
    df_scansante = utils.change_cols_type(df_local_scansante.append(temp))
    df_scansante["annee"] = df_scansante["annee"].astype(str)
    with st.expander("Cliquer pour voir les données"):
        st.dataframe(df_scansante)
    st.caption("Période : données de 2018 à 2021, voir https://www.scansante.fr/ pour la dernière date de mise à jour des données 2021")
    selected_criteria = st.radio('Selectionner une variable ', ["sejours","patients"])
    st.warning('Variable choisie :  **'+selected_criteria+'**')
    fig211 = px.bar(df_scansante.sort_values(by=['reg'], ascending=[True]), x='reg', y=selected_criteria, color='annee', barmode='group', template='xgridoff',category_orders={"annee": ["2018", "2019", "2020", "2021"]})
    fig211.update_layout(legend_title_text="Année")
    fig211.update_xaxes(title_text="régions")
    fig211.update_layout(autosize=True)
    st.plotly_chart(fig211,use_container_width=True)

#section 2.1.2
with st.container():
    st.subheader("Séjours : totaux par région, structure par classes d'âges (détail des plus de 16 ans)")
    d = {}
    dfs = {1: df_scrap_age1, 2: df_scrap_age2}
    for x in [1,2]:
        d["temp_age{0}".format(x)] = utils.remove_cols(dfs[x],[2,4,6,8,10,12,14])
        d["temp_age{0}".format(x)].columns = ['reg','[0-16]', '[17-25]', '[26-45]','[46-55]','[56-70]','[70-80]','[80-...]']
        d["temp_age{0}".format(x)] = utils.change_cols_type(d["temp_age{0}".format(x)])
    temp_age = (d["temp_age1"].drop("reg",axis=1)).add(d["temp_age2"].drop("reg",axis=1))
    temp_age["reg"] = d["temp_age1"]["reg"]
    temp_age["annee"] = 2021
    temp_melt = temp_age.melt(id_vars=["reg", "annee"], 
        var_name="cl_age", 
        value_name="sejours")
    df_scansante_age =  df_local_scansante_age.append(temp_melt)
    df_scansante_age['cl_age_group'] = df_scansante_age['cl_age'].map(dict_scansante_classes_ages)
    df_scansante_age["annee"] = df_scansante_age["annee"].astype(str)
    with st.expander("Cliquer pour voir les données"):
        st.dataframe(df_scansante_age)   
    def grid1x2(year):
        df_scansante_age4chart = df_scansante_age[df_scansante_age['annee'] == str(year)].groupby(['reg','cl_age_group']).agg(sejours_sum=('sejours', 'sum')).unstack().reset_index()
        df_scansante_age4chart.columns = ["_".join([str(index) for index in multi_index]) for multi_index in df_scansante_age4chart.columns.ravel()]
        if selected_norm == "Données brutes":
            fig212 = px.area(df_scansante_age4chart, x="reg_", y=['sejours_sum_[0-25]','sejours_sum_[26-55]','sejours_sum_[56-80]','sejours_sum_[80-...]'], title=year, template='xgridoff')
        elif selected_norm == "Données normalisées":
            fig212 = px.area(df_scansante_age4chart, x="reg_", y=['sejours_sum_[0-25]','sejours_sum_[26-55]','sejours_sum_[56-80]','sejours_sum_[80-...]'], groupnorm='percent', title=year, template='xgridoff') 
        fig212.update_xaxes(title_text="régions")
        fig212.update_yaxes(title_text='séjours')
        fig212.update_layout(legend_title_text="Classes d'âge", title_x=0.2)
        fig212.update_layout(autosize=True)
        return st.plotly_chart(fig212)
    col2021, col2020, col2019,col2018 = st.columns((1,1,1,1))
    tcols = {2021: col2021, 2020: col2020, 2019: col2019, 2018: col2018}
    for x in tcols:
        with tcols[x]:
            grid1x2(x)

#section 2.2
st.header("Fiche nationale toutes activités, champ MCO (Médecine-Chirurgie-Obstétrique)")
with st.expander("Cliquer pour développer - Source des données : https://www.scansante.fr/"):
    st.write("""
        **Les données hospitalières**

        * url d'accès : [https://www.scansante.fr/applications/analyse-activite-nationale](https://www.scansante.fr/applications/analyse-activite-nationale)
        * Jeu de données : 2020 MCO

        **Retraitements effectués**
        Compilation manuelle à partir du jeu de données sous Excel (onglet CMD_hs)
        """)
    st.dataframe(df_local_scansante_cmd)
#section 2.2.1
with st.container():
    st.subheader("Séjours : Déclinaison par catégorie majeure de diagnostic, taux de progression 2018/2019 et 2019/2020")
    fig221 = px.bar(df_local_scansante_cmd, y='cmd', x='taux', color='annees_ref', barmode='group', height=900)
    fig221.update_xaxes(title_text="Pourcentage d'augmentation du nombre de séjours")
    fig221.update_yaxes(title_text='catégories majeures de diagnostics')
    fig221.update_layout(legend_title_text="Années comparées")
    fig221.update_layout(autosize=True)
    st.plotly_chart(fig221,use_container_width=True)


