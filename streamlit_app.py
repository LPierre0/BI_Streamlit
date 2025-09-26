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
age_options = ["Tous"] + sorted(df_authors['Age'].dropna().unique())
selected_age = st.sidebar.multiselect("Âge", age_options, default=["Tous"])

# Filtre Level
level_options = ["Tous"] + sorted(df_authors['Level'].dropna().unique())
selected_level = st.sidebar.multiselect("Level", level_options, default=["Tous"])

# Filtre FashionStyle
fashion_options = ["Tous"] + sorted(df_authors['FashionStyle'].dropna().unique())
selected_fashion = st.sidebar.multiselect("FashionStyle", fashion_options, default=["Tous"])

# Appliquer les filtres
df_author_filtered = df_authors.copy()
if "Tous" not in selected_age:
    df_author_filtered = df_author_filtered[df_author_filtered['Age'].isin(selected_age)]
if "Tous" not in selected_level:
    df_author_filtered = df_author_filtered[df_author_filtered['Level'].isin(selected_level)]
if "Tous" not in selected_fashion:
    df_author_filtered = df_author_filtered[df_author_filtered['FashionStyle'].isin(selected_fashion)]

# --- Stats auteurs filtrés ---
st.header("Auteurs sélectionnés")
col1, col2, col3 = st.columns(3)
col1.metric("Nombre d'auteurs", len(df_author_filtered))
col2.metric("Âge moyen", round(df_author_filtered['Age'].replace({
    "17orUnder":17, "18to24":21, "25to34":29, "35to44":39, "45to54":49, "55to64":59, "65orOver":70
}).mean()))
col3.metric("Niveaux uniques", df_author_filtered['Level'].nunique())

st.markdown("**Distribution par Âge**")
fig_age = px.histogram(df_author_filtered, x='Age', title="Âge des auteurs")
st.plotly_chart(fig_age, use_container_width=True)

st.markdown("**Distribution par Level**")
fig_level = px.histogram(df_author_filtered, x='Level', title="Level des auteurs")
st.plotly_chart(fig_level, use_container_width=True)

st.markdown("**Distribution par FashionStyle**")
fig_fashion = px.histogram(df_author_filtered, x='FashionStyle', title="FashionStyle des auteurs")
st.plotly_chart(fig_fashion, use_container_width=True)

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
    categories = ["Tous"] + sorted(st.session_state.df_compute['category'].dropna().unique())
    selected_categories = st.multiselect("Catégories", categories, default=["Tous"])

    df_filtered = st.session_state.df_compute.copy()
    if "Tous" not in selected_categories:
        df_filtered = df_filtered[df_filtered['category'].isin(selected_categories)]

    # Tableau produits triés par score
    st.dataframe(
        df_filtered[['name','category','price','nb_reviews','avg_rating','score']].sort_values('score', ascending=False),
        height=400
    )


# Calcul du score moyen par catégorie + nombre de produits
df_category_score = (
    df_filtered.groupby('category', as_index=False)
    .agg(score_mean=('score','mean'), nb_products=('product_id','count'))
    .round(2)
    .sort_values(by='score_mean', ascending=False)
)

st.dataframe(df_category_score)

