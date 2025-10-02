from function import compute_df_score
import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px
import ast

# Config page
st.set_page_config(page_title="Analyse des Produits", layout="wide")

# --- Charger les données ---
excel_file = "./alltricks.xlsx"
if "df_product" not in st.session_state:
    st.session_state.df_product = pd.read_excel(excel_file, sheet_name="Product")
    st.session_state.df_rating = pd.read_excel(excel_file, sheet_name="Rating")
    st.session_state.df_author_grouped = pd.read_excel(excel_file, sheet_name="Author")

    # 🔹 Convertir parfum_list en liste si stocké comme string ou gérer les NA
    if "parfum_list" in st.session_state.df_product.columns:
        st.session_state.df_product["parfum_list"] = st.session_state.df_product["parfum_list"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )
        st.session_state.df_product["parfum_list"] = st.session_state.df_product["parfum_list"].apply(
            lambda x: x if isinstance(x, list) else []
        )

    st.success("Fichier chargé avec succès !")

# --- Sidebar pour tous les filtres ---
st.sidebar.header("Filtres & Calcul")

# --- Filtres auteurs ---
df_authors = st.session_state.df_author_grouped.copy()
age_options = sorted(df_authors['Age'].dropna().unique())
selected_age = st.sidebar.multiselect("Âge", age_options, default=None)

df_author_filtered = df_authors.copy()
if selected_age:
    df_author_filtered = df_author_filtered[df_author_filtered['Age'].isin(selected_age)]

# --- Initialisation df_filtered pour éviter NameError ---
df_filtered = None
selected_categories = []
selected_parfums = []

# --- Filtres produits (si df_compute existe) ---
if "df_compute" in st.session_state:
    df_filtered = st.session_state.df_compute.copy()

    # Catégories
    categories = sorted(df_filtered['category'].dropna().unique())
    selected_categories = st.sidebar.multiselect("Catégories", categories, default=None)
    if selected_categories:
        df_filtered = df_filtered[df_filtered['category'].isin(selected_categories)]

    # Parfums
    if 'parfum_list' in df_filtered.columns:
        # Remplacer tout non-liste par liste vide
        df_filtered['parfum_list'] = df_filtered['parfum_list'].apply(lambda x: x if isinstance(x, list) else [])

        # Extraire tous les parfums uniques
        unique_parfums = sorted({p for sublist in df_filtered['parfum_list'] for p in sublist})
        selected_parfums = st.sidebar.multiselect("Parfums", unique_parfums, default=None)

        if selected_parfums:
            # Garder les produits qui contiennent tous les parfums sélectionnés
            df_filtered = df_filtered[df_filtered['parfum_list'].apply(
                lambda lst: all(p in lst for p in selected_parfums)
            )]

# --- Bouton Calculer Score en bas de la sidebar ---
st.sidebar.markdown("<div style='position:fixed; bottom:20px; width:230px;'>", unsafe_allow_html=True)
calculate_pressed = st.sidebar.button("✅ Calculer Score")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

if calculate_pressed and "df_product" in st.session_state and "df_rating" in st.session_state:
    df_filtered_rating = st.session_state.df_rating[
        st.session_state.df_rating['author_id'].isin(df_author_filtered['author_id'])
    ]
    st.session_state.df_compute = compute_df_score(st.session_state.df_product, df_filtered_rating)
    st.success("Scores calculés !")

# --- Page principale ---

# Stats auteurs
st.header("Auteurs sélectionnés")
col1, col2 = st.columns(2)
col1.metric("Nombre d'auteurs", len(df_author_filtered))
col2.metric("Âge moyen", round(df_author_filtered['Age'].replace({
    "17orUnder":17, "18to24":21, "25to34":29, "35to44":39, "45to54":49, "55to64":59, "65orOver":70
}).mean()))

# 🔹 Distribution Âge
age_order = ["17orUnder", "18to24", "25to34", "35to44", "45to54", "55to64", "65orOver"]
df_author_filtered["Age"] = pd.Categorical(df_author_filtered["Age"], categories=age_order, ordered=True)

st.markdown("**Distribution par Âge**")
fig_age = px.histogram(df_author_filtered, x='Age', category_orders={'Age': age_order}, title="Âge des auteurs")
st.plotly_chart(fig_age, use_container_width=True)

# Affichage df_compute si disponible
if df_filtered is not None:
    st.header("Scores des produits")
    colonnes_affichage = ['name','category','price','nb_reviews','avg_rating','score']
    if 'parfum_list' in df_filtered.columns:
        colonnes_affichage.insert(2, 'parfum_list')
    st.dataframe(df_filtered[colonnes_affichage].sort_values('score', ascending=False), height=400)

    # Stats par catégorie
    df_category_score = (
        df_filtered.groupby('category', as_index=False)
        .agg(score_mean=('score','mean'), nb_products=('product_id','count'))
        .round(2)
        .sort_values(by='score_mean', ascending=False)
    )
    st.subheader("Score moyen par Catégorie")
    st.dataframe(df_category_score)

    # Stats et top parfums
    if 'parfum_list' in df_filtered.columns:
        # Exploser les listes de parfums pour stats individuelles
        df_exploded = df_filtered.explode('parfum_list')

        df_parfum_score = (
            df_exploded.groupby('parfum_list', as_index=False)
            .agg(score_mean=('score','mean'), nb_products=('product_id','count'))
            .round(2)
            .sort_values(by='score_mean', ascending=False)
        )
        st.subheader("Score moyen par Parfum")
        st.dataframe(df_parfum_score)

        # Top 10 des parfums les plus fréquents
        df_parfum_top_usage = df_parfum_score.sort_values(by='nb_products', ascending=False).head(10)
        fig_parfum_usage = px.bar(df_parfum_top_usage, x='parfum_list', y='nb_products', text='nb_products',
                                  title="Top 10 Parfums les plus utilisés")
        st.plotly_chart(fig_parfum_usage, use_container_width=True)

        # Produits top pour les parfums sélectionnés
        if selected_parfums:
            st.subheader("Meilleurs produits avec les parfums sélectionnés")
            top_products = df_filtered.sort_values('score', ascending=False).head(10)
            st.dataframe(top_products[['name','category','price','avg_rating','score','parfum_list']])
