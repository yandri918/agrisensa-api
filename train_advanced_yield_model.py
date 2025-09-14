import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb
from sklearn.metrics import r2_score
import joblib
import shap
import os

# --- LANGKAH 1: PERSIAPAN ---
DATASET_PATH = 'EDA_500.csv'
MODEL_SAVE_PATH = 'advanced_yield_model.pkl'
EXPLAINER_SAVE_PATH = 'shap_explainer.pkl'

def train_advanced_model():
    """
    Fungsi untuk melatih model LightGBM dan SHAP explainer.
    """
    if not os.path.exists(DATASET_PATH):
        print(f"Error: File dataset '{DATASET_PATH}' tidak ditemukan.")
        return

    # --- LANGKAH 2: MEMUAT DAN MEMBERSIHKAN DATA ---
    print(f"Memuat dataset dari '{DATASET_PATH}'...")
    dataset = pd.read_csv(DATASET_PATH)
    
    dataset['Yield'] = pd.to_numeric(dataset['Yield'], errors='coerce')
    dataset.dropna(subset=['Yield'], inplace=True)
    
    features = ['Nitrogen', 'Phosphorus', 'Potassium', 'Temperature', 'Rainfall', 'pH']
    target = 'Yield'
    X = dataset[features]
    y = dataset[target]
    print("Dataset berhasil dimuat dan dibersihkan.")

    # --- LANGKAH 3: MELATIH MODEL GRADIENT BOOSTING ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Melatih model LightGBM Regressor...")
    model = lgb.LGBMRegressor(random_state=42)
    model.fit(X_train, y_train)
    print("Model berhasil dilatih.")

    # --- LANGKAH 4: MENGEVALUASI & MENYIMPAN MODEL ---
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    print(f"R-squared (R²) score model: {r2:.4f}")

    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"Model berhasil disimpan sebagai '{MODEL_SAVE_PATH}'.")

    # --- LANGKAH 5: MEMBUAT DAN MENYIMPAN SHAP EXPLAINER ---
    print("Membuat SHAP explainer...")
    # TreeExplainer adalah metode yang paling efisien untuk model berbasis pohon seperti LightGBM
    explainer = shap.TreeExplainer(model)
    joblib.dump(explainer, EXPLAINER_SAVE_PATH)
    print(f"SHAP explainer berhasil disimpan sebagai '{EXPLAINER_SAVE_PATH}'.")

if __name__ == '__main__':
    train_advanced_model()
