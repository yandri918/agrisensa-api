# train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC # Kita akan gunakan Support Vector Classifier
from sklearn.metrics import accuracy_score
import joblib # Untuk menyimpan model

# 1. Muat Dataset
print("Memuat dataset...")
dataset = pd.read_csv('bwd_dataset.csv')

# 2. Pisahkan Fitur (X) dan Target (y)
X = dataset[['avg_hue_value']] # Fitur input
y = dataset['bwd_score']       # Label yang ingin diprediksi

# 3. Pisahkan Data Training dan Data Testing
# 80% untuk melatih model, 20% untuk menguji akurasinya
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Jumlah data training: {len(X_train)}, Jumlah data testing: {len(X_test)}")

# 4. Inisialisasi dan Latih Model Machine Learning
print("Melatih model SVM...")
# SVC adalah model klasifikasi yang kuat dan cocok untuk dataset kecil
model = SVC(kernel='linear', probability=True) 
model.fit(X_train, y_train)

# 5. Uji Akurasi Model
print("Menguji akurasi model...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Akurasi model pada data test: {accuracy * 100:.2f}%")

# 6. Simpan Model yang Sudah Terlatih
# Ini langkah terpenting. Kita simpan model ke sebuah file.
joblib.dump(model, 'bwd_model.pkl')
print("Model berhasil dilatih dan disimpan sebagai bwd_model.pkl")