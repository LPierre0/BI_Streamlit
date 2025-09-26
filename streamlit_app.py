from function import compute_df_score
import streamlit as st
import pandas as pd
import openpyxl

# Chemin vers ton fichier Excel déjà présent
excel_file = "./alltricks.xlsx"

# Charger les données dans session_state si ce n'est pas déjà fait
if "df_product" not in st.session_state:
    st.session_state.df_product = pd.read_excel(excel_file, sheet_name="Product")
    st.session_state.df_rating = pd.read_excel(excel_file, sheet_name="Rating")
    st.session_state.df_author_grouped = pd.read_excel(excel_file, sheet_name="Author")
    st.success("Fichier chargé avec succès !")


# --- Afficher et filtrer df_author_grouped par Age, Level, FashionStyle, Gender ---
if "df_author_grouped" in st.session_state:
    st.subheader("Filtrer les auteurs")

    # Filtre Age
    age_options = ["Tous", "17orUnder", "18to24", "25to34", "35to44", "45to54", "55to64", "65orOver"]
    selected_age = st.multiselect("Sélectionnez un ou plusieurs groupes d'âge", age_options, default=["Tous"])
    
    # Filtre Level (anciennement BodyType)
    level_options = ["Tous"] + st.session_state.df_author_grouped['Level'].dropna().unique().tolist()
    selected_level = st.multiselect("Sélectionnez un ou plusieurs Level", level_options, default=["Tous"])
    
    # Filtre FashionStyle
    fashion_options = ["Tous"] + st.session_state.df_author_grouped['FashionStyle'].dropna().unique().tolist()
    selected_fashion = st.multiselect("Sélectionnez un ou plusieurs FashionStyle", fashion_options, default=["Tous"])
    
    # Appliquer tous les filtres
    df_author_filtered = st.session_state.df_author_grouped.copy()
    
    if "Tous" not in selected_age:
        df_author_filtered = df_author_filtered[df_author_filtered['Age'].isin(selected_age)]
    if "Tous" not in selected_level:
        df_author_filtered = df_author_filtered[df_author_filtered['Level'].isin(selected_level)]
    if "Tous" not in selected_fashion:
        df_author_filtered = df_author_filtered[df_author_filtered['FashionStyle'].isin(selected_fashion)]

    # Affichage
    st.subheader("Auteurs sélectionnés")
    st.dataframe(df_author_filtered)

    # --- Statistiques de volume ---
    st.subheader("Volume des auteurs filtrés")
    st.markdown(f"**Nombre total d'auteurs : {len(df_author_filtered)}**")

    # Distribution par Age
    st.markdown("**Distribution par Age**")
    st.bar_chart(df_author_filtered['Age'].value_counts())

    # Distribution par Level
    st.markdown("**Distribution par Level**")
    st.bar_chart(df_author_filtered['Level'].value_counts())

    # Distribution par FashionStyle
    st.markdown("**Distribution par FashionStyle**")
    st.bar_chart(df_author_filtered['FashionStyle'].value_counts())

# --- Calculer df_compute via compute_df_score ---
if st.button("Calculer Score"):
    if "df_product" in st.session_state and "df_rating" in st.session_state:
        # Filtrer df_rating pour ne garder que les author_id présents dans df_author_filtered
        df_filtered_rating = st.session_state.df_rating[
            st.session_state.df_rating['author_id'].isin(df_author_filtered['author_id'])
        ]
        
        # Calculer df_compute avec le df_rating filtré
        st.session_state.df_compute = compute_df_score(
            st.session_state.df_product, df_filtered_rating
        )
        st.success("df_compute calculé avec les avis filtrés !")

# --- Affichage du df_compute si disponible ---
if "df_compute" in st.session_state:
    st.subheader("Score des produits")

    # --- Filtrage par catégorie ---
    categories = ["Tous"] + st.session_state.df_compute['category'].dropna().unique().tolist()
    selected_categories = st.multiselect(
        "Sélectionnez une ou plusieurs catégories",
        options=categories,
        default=["Tous"]
    )

    # Filtrer le DataFrame selon la sélection
    df_filtered = st.session_state.df_compute.copy()
    if "Tous" not in selected_categories:
        df_filtered = df_filtered[df_filtered['category'].isin(selected_categories)]

    # Afficher les produits filtrés
    st.dataframe(df_filtered)

    # --- Score moyen par catégorie ---
    st.subheader("Score moyen par catégorie")
    df_category_score = (
        df_filtered.groupby('category', as_index=False)['score']
        .mean()
        .sort_values(by='score', ascending=False)
    )
    st.dataframe(df_category_score)