covid-nodramadata - Prototype simple de visualisation des données de l'activité hospitalière liée à la Covid (mais pas que)
========================================================

![](img/made-with-streamlit.svg)

## Accès

L'application est déployée et accessible sur le PaaS Heroku

[https://covid-nodramadata.herokuapp.com/](https://covid-nodramadata.herokuapp.com/)

## Installation locale

Comme pour toute application Python il est recommandé de créer un environnement virtuel sous lequel installer les packages nécessaires.

```
git clone https://github.com/gegedenice/covid-nodramadata.git
virtualenv YOUR_VENV_NAME
cd YOUR_VENV_NAME/Scripts && activate (Windows)
source YOUR_VENV_NAME/bin/activate (Linux)
pip install -r requirements.txt
streamlit run app.py
```

## Source des données

Les données spécifiques à l'épidémie de Covid sont issues de jeux de données publics dans le domaine de la santé disponibles en Open Data sur [data.gouv.fr](https://www.data.gouv.fr/fr/pages/donnees-sante/) et [data.drees.solidarites-sante.gouv.fr/](https://data.drees.solidarites-sante.gouv.fr/explore/?refine.theme=Sant%C3%A9+et+Syst%C3%A8me+de+soins&sort=modified).

L'autre partie des données concernant l'analyse de l'activité hospitalière nationale proviennent de l'application [ScanSanté](https://www.scansante.fr/applications/analyse-activite-nationale) maintenue et alimentée par l'Agence Technique de l'Information sur l'Hospitalisation ([ATIH](https://www.atih.sante.fr/))


    
