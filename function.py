import pandas as pd
import numpy as np

def sigmoid_normalize(x, alpha=1):
    """Normalisation sigmoïde sûre, remplace les NA par 0"""
    x_filled = x.fillna(0)
    x_mean = x_filled.mean()
    x_std = x_filled.std()
    z = (x_filled - x_mean) / (x_std + 1e-9)  # standardisation
    return 1 / (1 + np.exp(-alpha * z))


def compute_df_score(df_product, df_rating):
    # Copies des DataFrames pour ne pas modifier les originaux
    df_product_copy = df_product[['url', 'product_id', 'name', 'price', 'category']].copy()
    df_rating_copy = df_rating.copy()

    # Convertir les colonnes numériques et remplacer NA par 0
    for col in ['rating', 'gout', 'efficacite', 'rapport_qualite_prix']:
        df_rating_copy[col] = pd.to_numeric(df_rating_copy[col], errors='coerce').fillna(0)

    # Initialiser les listes
    nb_rating_1 = []
    nb_rating_2 = []
    nb_rating_3 = []
    nb_rating_4 = []
    nb_rating_5 = []
    nb_reviews = []
    avg_rating = []
    avg_gout = []
    avg_efficacite = []
    avg_rapport_qualite_prix = []

    # Calcul pour chaque produit
    for _, row in df_product_copy.iterrows():
        product_ratings = df_rating_copy[df_rating_copy['product_id'] == row['product_id']]

        if product_ratings.empty:
            nb_rating_1.append(0)
            nb_rating_2.append(0)
            nb_rating_3.append(0)
            nb_rating_4.append(0)
            nb_rating_5.append(0)
            nb_reviews.append(0)
            avg_rating.append(0)
            avg_gout.append(0)
            avg_efficacite.append(0)
            avg_rapport_qualite_prix.append(0)
        else:
            nb_rating_1.append((product_ratings['rating'] == 1).sum())
            nb_rating_2.append((product_ratings['rating'] == 2).sum())
            nb_rating_3.append((product_ratings['rating'] == 3).sum())
            nb_rating_4.append((product_ratings['rating'] == 4).sum())
            nb_rating_5.append((product_ratings['rating'] == 5).sum())
            nb_reviews.append(len(product_ratings))

            avg_rating.append(product_ratings['rating'].mean())
            avg_gout.append(product_ratings['gout'].mean())
            avg_efficacite.append(product_ratings['efficacite'].mean())
            avg_rapport_qualite_prix.append(product_ratings['rapport_qualite_prix'].mean())

    # Ajouter les colonnes
    df_product_copy['nb_rating_1'] = nb_rating_1
    df_product_copy['nb_rating_2'] = nb_rating_2
    df_product_copy['nb_rating_3'] = nb_rating_3
    df_product_copy['nb_rating_4'] = nb_rating_4
    df_product_copy['nb_rating_5'] = nb_rating_5
    df_product_copy['nb_reviews'] = nb_reviews
    df_product_copy['avg_rating'] = avg_rating
    df_product_copy['avg_gout'] = avg_gout
    df_product_copy['avg_efficacite'] = avg_efficacite
    df_product_copy['avg_rapport_qualite_prix'] = avg_rapport_qualite_prix

    df_product_copy = df_product_copy[df_product_copy['nb_reviews'] != 0]
    # Calcul NPS sécurisé
    df_product_copy['NPS'] = (
        (df_product_copy['nb_rating_5'] / df_product_copy['nb_reviews'].replace(0, 1) * 100) -
        ((df_product_copy['nb_rating_1'] + df_product_copy['nb_rating_2'] + df_product_copy['nb_rating_3']) /
         df_product_copy['nb_reviews'].replace(0, 1) * 100)
    )

    # Bayesian smoothing
    seuil_rating = 20
    df_product_copy['rating_bayesian'] = (
        df_product_copy['avg_rating'] * df_product_copy['nb_reviews'] +
        df_product_copy['avg_rating'].mean() * seuil_rating
    ) / (df_product_copy['nb_reviews'] + seuil_rating)

    df_product_copy['NPS_bayesian'] = (
        df_product_copy['NPS'] * df_product_copy['nb_reviews'] +
        df_product_copy['NPS'].mean() * seuil_rating
    ) / (df_product_copy['nb_reviews'] + seuil_rating)

    # Normalisation sigmoïde
    df_product_copy['rating_bayesian_normalized'] = sigmoid_normalize(df_product_copy['rating_bayesian'], alpha=1)
    df_product_copy['NPS_bayesian_normalized'] = sigmoid_normalize(df_product_copy['NPS_bayesian'], alpha=1)
    df_product_copy['nb_reviews_normalized'] = sigmoid_normalize(df_product_copy['nb_reviews'], alpha=0.5)

    # Score final
    df_product_copy['score'] = (
        0.40 * df_product_copy['rating_bayesian_normalized'] +
        0.40 * df_product_copy['NPS_bayesian_normalized'] +
        0.2 * df_product_copy['nb_reviews_normalized']
    )

    # Trier par score décroissant
    df_product_copy.sort_values(by='score', ascending=False, inplace=True)

    return df_product_copy[['name', 'category', 'score', 'avg_rating', 'nb_reviews', 'price', 'url', 'product_id']]
