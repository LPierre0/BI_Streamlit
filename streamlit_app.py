from function import compute_df_score
import streamlit as st
import pandas as pd
import openpyxl
import plotly.express as px

# Config page
st.set_page_config(page_title="Analyse des Produits", layout="wide")

# --- Charger les données ---
excel_file = "./alltricks.xlsx"
if "df_product" not in st.session_state:
    st.session_state.df_product = pd.read_excel(excel_file, sheet_name="Product")
    st.session_state.df_rating = pd.read_excel(excel_file, sheet_name="Rating")
    st.session_state.df_author_grouped = pd.read_excel(excel_file, sheet_name="Author")
    st.success("Fichier chargé avec succès !")

# --- Sidebar pour filtrage des auteurs ---
st.sidebar.header("Filtres auteurs")
df_authors = st.session_state.df_author_grouped.copy()

# Filtre Age
age_options = sorted(df_authors['Age'].dropna().unique())
selected_age = st.sidebar.multiselect("Âge", age_options, default=None)

# Filtre Level
level_options = sorted(df_authors['Level'].dropna().unique())
selected_level = st.sidebar.multiselect("Level", level_options, default=None)


# Appliquer les filtres
df_author_filtered = df_authors.copy()
if selected_age:
    df_author_filtered = df_author_filtered[df_author_filtered['Age'].isin(selected_age)]
if selected_level:
    df_author_filtered = df_author_filtered[df_author_filtered['Level'].isin(selected_level)]


# --- Stats auteurs filtrés ---
st.header("Auteurs sélectionnés")
col1, col2, col3 = st.columns(3)
col1.metric("Nombre d'auteurs", len(df_author_filtered))
col2.metric("Âge moyen", round(df_author_filtered['Age'].replace({
    "17orUnder":17, "18to24":21, "25to34":29, "35to44":39, "45to54":49, "55to64":59, "65orOver":70
}).mean()))
col3.metric("Niveaux uniques", df_author_filtered['Level'].nunique())

# 🔹 Définir l’ordre des âges
age_order = ["17orUnder", "18to24", "25to34", "35to44", "45to54", "55to64", "65orOver"]
df_author_filtered["Age"] = pd.Categorical(df_author_filtered["Age"], categories=age_order, ordered=True)

# 🔹 Définir l’ordre des niveaux
level_order = ["Debutant", "Amateur", "Eclaire", "Expert"]
df_author_filtered["Level"] = pd.Categorical(df_author_filtered["Level"], categories=level_order, ordered=True)

# Distribution par Âge
st.markdown("**Distribution par Âge**")
fig_age = px.histogram(
    df_author_filtered,
    x='Age',
    category_orders={'Age': age_order},  # impose l’ordre
    title="Âge des auteurs"
)
st.plotly_chart(fig_age, use_container_width=True)

# Distribution par Level
st.markdown("**Distribution par Level**")
fig_level = px.histogram(
    df_author_filtered,
    x='Level',
    category_orders={'Level': level_order},  # impose l’ordre
    title="Level des auteurs"
)
st.plotly_chart(fig_level, use_container_width=True)


# --- Calculer df_compute ---
if st.button("Calculer Score"):
    if "df_product" in st.session_state and "df_rating" in st.session_state:
        df_filtered_rating = st.session_state.df_rating[
            st.session_state.df_rating['author_id'].isin(df_author_filtered['author_id'])
        ]
        st.session_state.df_compute = compute_df_score(
            st.session_state.df_product, df_filtered_rating
        )
        st.success("Scores calculés !")

# --- Affichage df_compute ---
if "df_compute" in st.session_state:
    st.header("Scores des produits")

    # Filtrage par catégorie
    categories = sorted(st.session_state.df_compute['category'].dropna().unique())
    selected_categories = st.multiselect("Catégories", categories, default=None)

    df_filtered = st.session_state.df_compute.copy()
    if selected_categories:
        df_filtered = df_filtered[df_filtered['category'].isin(selected_categories)]

    # --- Filtrage par Parfum ---
    if 'parfum' in df_filtered.columns:  # vérifier que la colonne existe
        st.subheader("Filtrage par Parfum")
        parfum_options = sorted(df_filtered['parfum'].dropna().unique())
        selected_parfum = st.multiselect("Parfum", parfum_options, default=None)
        if selected_parfum:
            df_filtered = df_filtered[df_filtered['parfum'].isin(selected_parfum)]

    # Tableau produits triés par score
    colonnes_affichage = ['name','category','price','nb_reviews','avg_rating','score']
    if 'parfum' in df_filtered.columns:
        colonnes_affichage.insert(2, 'parfum')  # insérer parfum après category
    st.dataframe(
        df_filtered[colonnes_affichage].sort_values('score', ascending=False),
        height=400
    )

    # --- Stats par catégorie ---
    df_category_score = (
        df_filtered.groupby('category', as_index=False)
        .agg(score_mean=('score','mean'), nb_products=('product_id','count'))
        .round(2)
        .sort_values(by='score_mean', ascending=False)
    )
    st.subheader("Score moyen par Catégorie")
    st.dataframe(df_category_score)

    # --- Stats par Parfum ---
    if 'parfum' in df_filtered.columns:
        df_parfum_score = (
            df_filtered.groupby('parfum', as_index=False)
            .agg(score_mean=('score','mean'), nb_products=('product_id','count'))
            .round(2)
            .sort_values(by='score_mean', ascending=False)
        )
        st.subheader("Score moyen par Parfum")
        st.dataframe(df_parfum_score)

        # Graphique des parfums les plus utilisés (top 10 par nb_products)
        df_parfum_top_usage = df_parfum_score.sort_values(by='nb_products', ascending=False).head(10)
        fig_parfum_usage = px.bar(
            df_parfum_top_usage,
            x='parfum', y='nb_products',
            text='nb_products',
            title="Top 10 Parfums les plus utilisés"
        )
        st.plotly_chart(fig_parfum_usage, use_container_width=True)

        # Produits top pour chaque parfum sélectionné
        if selected_parfum:
            st.subheader("Meilleurs produits du parfum sélectionné")
            for p in selected_parfum:
                st.markdown(f"### {p}")
                top_products = (
                    df_filtered[df_filtered['parfum'] == p]
                    .sort_values('score', ascending=False)
                    .head(5)
                )
                st.dataframe(top_products[['name','category','price','avg_rating','score']])
