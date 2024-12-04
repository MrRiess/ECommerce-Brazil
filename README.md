# Dicoding E-Commerce Public
## Setup Environmet - Anaconda
```sh
conda create --name main-ds python=3.13.1
conda activate main-ds
pip install -r requirements.txt
```
## Setup Environmet - Shell/Terminal
```sh
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```
## Run streamlit app
```sh
streamlit run dashboard.py
```