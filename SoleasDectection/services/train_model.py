import pickle
import pandas as pd
from collections import Counter
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA

# fontion pour entrainer un modele --------------------------------------------------
def entrainer_modele(dataset_path, algorithme, modele_pkl_path, pca=True, n_components=2):

    # Charger le dataset
    df = pd.read_csv(dataset_path)
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    X_scaled = df[numeric_cols]

    print(">>> Dataset charge avec shape :", X_scaled.shape)

    # Construction du pipeline
    steps = []
    steps.append(('scaler', StandardScaler()))

    # Ajouter PCA si demandé
    if pca:
        steps.append(('pca', PCA(n_components=n_components)))

    # Ajouter le modèle
    if algorithme == 'isolation_forest':
        model = IsolationForest(n_estimators=50, contamination=0.1, random_state=42)
    elif algorithme == 'svm':
        model = OneClassSVM(kernel='rbf', gamma=0.01, nu=0.05)
    elif algorithme == 'kmeans':
        model = KMeans(n_clusters=3, random_state=42)
    else:
        raise ValueError("Algorithme non support : {algorithme}")

    steps.append(('model', model))

    # Créer pipeline
    pipeline = Pipeline(steps=steps)

    # Entraîner le pipeline
    pipeline.fit(X_scaled)

    # Sauvegarder le pipeline complet
    with open(modele_pkl_path, "wb") as f:
        pickle.dump(pipeline, f)

    print(f">>> Modele '{algorithme}' entraine et sauvegarder a : {modele_pkl_path}")

    return modele_pkl_path

# finction pour tester un modele--------------------------
import pandas as pd
import pickle
from collections import Counter

def tester_campagne_test(modele_path, dataset_path):
    # Charger le modèle
    with open(modele_path, "rb") as fichier:
        model = pickle.load(fichier)

    # Charger le dataset nettoyé
    df = pd.read_csv(dataset_path)
    X_scaled = df.select_dtypes(include=['int64', 'float64'])

    # Prédictions
    y_pred = model.predict(X_scaled)

    # Ajouter une colonne "is_fraud" : -1 (fraude) → 1, sinon 0
    df['is_fraud'] = [1 if y == -1 else 0 for y in y_pred]

    # Statistiques pour le graphe
    counter = Counter(y_pred)
    graph_data = {
        'labels': ['Normal (1)', 'Anomalie (-1)'],
        'data': [counter.get(1, 0), counter.get(-1, 0)]
    }

    return df, graph_data
