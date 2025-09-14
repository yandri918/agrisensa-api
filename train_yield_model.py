import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import os

# --- LANGKAH 1: PERSIAPAN ---
DATASET_PATH = 'EDA_500.csv'
MODEL_SAVE_PATH = 'yield_prediction_model.pkl'

def train_yield_prediction_model():
    """
    Fungsi untuk melatih model yang memprediksi hasil panen (Yield).
    """
    if not os.path.exists(DATASET_PATH):
        print(f"Error: File dataset '{DATASET_PATH}' tidak ditemukan.")
        return

    # --- LANGKAH 2: MEMUAT DAN MEMBERSIHKAN DATA ---
    print(f"Memuat dataset dari '{DATASET_PATH}'...")
    dataset = pd.read_csv(DATASET_PATH)

    # --- PERBAIKAN DIMULAI DI SINI ---
    print("Membersihkan data...")
    # Paksa kolom 'Yield' menjadi numerik. 
    # Jika ada nilai yang bukan angka (seperti 'neutral'), ubah menjadi NaN (Not a Number).
    dataset['Yield'] = pd.to_numeric(dataset['Yield'], errors='coerce')
    
    # Hapus semua baris yang memiliki nilai NaN di kolom 'Yield'.
    initial_rows = len(dataset)
    dataset.dropna(subset=['Yield'], inplace=True)
    cleaned_rows = len(dataset)
    print(f"{initial_rows - cleaned_rows} baris dengan data yield yang tidak valid telah dihapus.")
    # --- PERBAIKAN BERAKHIR DI SINI ---


    # Memilih fitur yang paling relevan untuk prediksi
    features = ['Nitrogen', 'Phosphorus', 'Potassium', 'Temperature', 'Rainfall', 'pH']
    target = 'Yield'

    X = dataset[features]
    y = dataset[target]
    print("Dataset berhasil dimuat dan fitur telah dipilih.")

    # --- LANGKAH 3: MELATIH MODEL REGRESI ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Jumlah data training: {len(X_train)}, Jumlah data testing: {len(X_test)}")

    # Kita gunakan RandomForestRegressor, sangat baik untuk prediksi numerik
    print("Melatih model RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("Model berhasil dilatih.")

    # --- LANGKAH 4: MENGEVALUASI & MENYIMPAN MODEL ---
    predictions = model.predict(X_test)
    # R-squared score mengukur seberapa baik model bisa menjelaskan variasi data
    # (semakin dekat ke 1, semakin baik)
    r2 = r2_score(y_test, predictions)
    print(f"R-squared (R²) score model pada data test: {r2:.4f}")

    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"Model berhasil disimpan sebagai '{MODEL_SAVE_PATH}'.")

if __name__ == '__main__':
    train_yield_prediction_model()

