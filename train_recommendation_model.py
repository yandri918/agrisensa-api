import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

print("Memuat dataset rekomendasi pemupukan...")
dataset = pd.read_csv('fertilizer_data.csv')

# Pisahkan fitur input (X) dan target output (y)
features = ['ph_tanah', 'skor_bwd', 'kelembaban_tanah', 'umur_tanaman_hari']
targets = ['rekomendasi_N', 'rekomendasi_P', 'rekomendasi_K']

X = dataset[features]
y = dataset[targets]

print("Melatih model RandomForestRegressor...")
# RandomForestRegressor sangat baik untuk hubungan non-linear yang kompleks
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Simpan model yang sudah terlatih
joblib.dump(model, 'recommendation_model.pkl')
print("Model rekomendasi berhasil dilatih dan disimpan sebagai recommendation_model.pkl")
