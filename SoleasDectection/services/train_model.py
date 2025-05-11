import pickle
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA

def entrainer_modele(dataset_path, algorithme, modele_pkl_path, pca=False):
    # Charger le dataset
    df = pd.read_csv(dataset_path)
    X = df.select_dtypes(include=['int64', 'float64'])

    #normalisation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    # Pipeline steps
    steps = []

    # Ajouter PCA si demandé
    if pca:
        steps.append(('pca', PCA(n_components=2)))

    # Ajouter le modèle
    if algorithme == 'isolation_forest':
        model = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
    elif algorithme == 'svm':
        model = OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
    elif algorithme == 'kmeans':
        model = KMeans(n_clusters=3, random_state=42)
    else:
        raise ValueError("Algorithme non supporté")

    steps.append(('model', model))

    # Créer pipeline
    pipeline = Pipeline(steps)

    # Entraîner le pipeline
    pipeline.fit(X)

    # Sauvegarder le pipeline complet
    with open(modele_pkl_path, "wb") as f:
        pickle.dump(pipeline, f)

    return modele_pkl_path