import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# --- LANGKAH 1: PERSIAPAN ---
# Tentukan path ke file dataset dan di mana model akan disimpan
DATASET_PATH = 'Crop_recommendation.csv'
MODEL_SAVE_PATH = 'crop_recommendation_model.pkl'

def train_and_save_model():
    """
    Fungsi utama untuk memuat data, melatih model,
    mengevaluasi, dan menyimpannya.
    """
    # Cek apakah file dataset ada
    if not os.path.exists(DATASET_PATH):
        print(f"Error: File dataset '{DATASET_PATH}' tidak ditemukan.")
        print("Harap pastikan file Crop_recommendation.csv berada di folder yang sama.")
        return

    # --- LANGKAH 2: MEMUAT DAN MEMPROSES DATA ---
    try:
        print(f"Memuat dataset dari '{DATASET_PATH}'...")
        dataset = pd.read_csv(DATASET_PATH)

        # Memisahkan fitur (X) dan target/label (y)
        # Fitur (X) adalah semua kolom kecuali 'label'
        X = dataset.drop('label', axis=1)
        # Target (y) adalah kolom 'label' yang ingin kita prediksi
        y = dataset['label']
        print("Dataset berhasil dimuat dan diproses.")
        print(f"Dataset memiliki {len(dataset)} baris data.")

    except Exception as e:
        print(f"Error saat memuat atau memproses data: {e}")
        return

    # --- LANGKAH 3: MELATIH MODEL MACHINE LEARNING ---
    # Membagi data menjadi data latih (80%) dan data uji (20%)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Jumlah data training: {len(X_train)}, Jumlah data testing: {len(X_test)}")

    # Kita akan menggunakan RandomForestClassifier, sebuah model yang kuat untuk masalah klasifikasi
    print("Melatih model RandomForestClassifier...")
    # n_estimators=100 berarti model akan membangun 100 'pohon keputusan'
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("Model berhasil dilatih.")

    # --- LANGKAH 4: MENGEVALUASI & MENYIMPAN MODEL ---
    # Menguji akurasi model pada data yang belum pernah dilihatnya
    print("Mengevaluasi akurasi model...")
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Akurasi model pada data test: {accuracy * 100:.2f}%")

    # Menyimpan model yang sudah terlatih ke dalam sebuah file
    try:
        joblib.dump(model, MODEL_SAVE_PATH)
        print(f"Model berhasil disimpan sebagai '{MODEL_SAVE_PATH}'.")
        print("\nProses pelatihan selesai. Anda sekarang bisa mengintegrasikan model ini ke aplikasi web Anda.")
    except Exception as e:
        print(f"Error saat menyimpan model: {e}")

# Jalankan fungsi utama saat skrip dieksekusi
if __name__ == '__main__':
    train_and_save_model()

