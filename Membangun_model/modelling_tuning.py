import os
import json
import pickle
import dagshub
import mlflow
import mlflow.sklearn
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, ConfusionMatrixDisplay,
    balanced_accuracy_score, log_loss, matthews_corrcoef
)
from mlflow.models.signature import infer_signature
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Setup DAGsHub tracking
dagshub.init(repo_owner="permataa", repo_name="personality-prediction", mlflow=True)
mlflow.set_tracking_uri("https://dagshub.com/permataa/personality-prediction.mlflow")
mlflow.set_experiment("Personality Prediction")

# Utilitas: simpan confusion matrix sebagai gambar
def simpan_conf_matrix(y_true, y_pred, filename):
    disp = ConfusionMatrixDisplay(confusion_matrix(y_true, y_pred))
    disp.plot()
    plt.savefig(filename)
    plt.close()

# Utilitas: simpan parameter model dalam bentuk HTML
def buat_html_model(model, filepath):
    isi = f"""
    <html><body>
    <h2>Parameter Model: RandomForestClassifier</h2>
    <ul>
      <li>n_estimators: {model.n_estimators}</li>
      <li>max_depth: {model.max_depth}</li>
      <li>random_state: {model.random_state}</li>
    </ul>
    </body></html>
    """
    with open(filepath, "w") as f:
        f.write(isi)

# Main pipeline training & logging
def jalankan_training():
    df = pd.read_csv("personality.csv")
    X = df.drop(columns=["Personality"])
    y = df["Personality"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    kombinasi_hyper = {'n_estimators': [50, 100], 'max_depth': [5, 10]}

    os.makedirs("model", exist_ok=True)

    for n in kombinasi_hyper["n_estimators"]:
        for d in kombinasi_hyper["max_depth"]:
            with mlflow.start_run():
                clf = RandomForestClassifier(n_estimators=n, max_depth=d, random_state=42)
                clf.fit(X_train, y_train)

                y_pred = clf.predict(X_test)
                y_proba = clf.predict_proba(X_test)[:, 1]

                metrik = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred),
                    "recall": recall_score(y_test, y_pred),
                    "f1_score": f1_score(y_test, y_pred),
                    "roc_auc": roc_auc_score(y_test, y_proba),
                    "balanced_acc": balanced_accuracy_score(y_test, y_pred),
                    "log_loss": log_loss(y_test, y_proba),
                    "matthews_corr": matthews_corrcoef(y_test, y_pred)
                }

                # Logging parameter & metrik
                mlflow.log_param("n_estimators", n)
                mlflow.log_param("max_depth", d)
                for nama_metrik, nilai in metrik.items():
                    mlflow.log_metric(nama_metrik, nilai)

                # Logging model
                signature = infer_signature(X_train, clf.predict(X_train))
                mlflow.sklearn.log_model(clf, "model")

                # Simpan model.pkl manual
                with open("model/model.pkl", "wb") as f:
                    pickle.dump(clf, f)
                mlflow.log_artifact("model/model.pkl", artifact_path="model")

                # Simpan estimator dalam HTML
                buat_html_model(clf, "estimator.html")
                mlflow.log_artifact("estimator.html")

                # Simpan confusion matrix
                simpan_conf_matrix(y_test, y_pred, "conf_matrix.png")
                mlflow.log_artifact("conf_matrix.png")

                # Simpan semua metrik ke file JSON
                with open("metric_info.json", "w") as f:
                    json.dump(metrik, f)
                mlflow.log_artifact("metric_info.json")

                print(f" Model selesai (n={n}, depth={d}) - Akurasi: {metrik['accuracy']:.4f}")

if __name__ == "__main__":
    jalankan_training()
