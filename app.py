<<<<<<< HEAD
import cv2
import numpy as np
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify, render_template
import joblib
import os
import sqlite3
import logging
import random

# Konfigurasi logging dasar untuk menampilkan info di terminal
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- Konfigurasi Awal & Pemuatan Model ---
# Memastikan folder 'output' ada
if not os.path.exists('output'):
    os.makedirs('output')

def load_model(path):
    """Fungsi helper untuk memuat model dengan aman."""
    if os.path.exists(path):
        app.logger.info(f"Memuat model dari {path}...")
        return joblib.load(path)
    app.logger.warning(f"PERINGATAN: File model '{path}' tidak ditemukan.")
    return None

bwd_model = load_model('bwd_model.pkl')
recommendation_model = load_model('recommendation_model.pkl')

# --- Inisialisasi Database ---
def init_db():
    conn = sqlite3.connect('agrisensa.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS npk_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            n_value INTEGER,
            p_value INTEGER,
            k_value INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- BASIS DATA PENGETAHUAN & REKOMENDASI ---
KNOWLEDGE_BASE = {
    "padi": {
        "name": "Padi (Oryza sativa)", "icon": "🌾",
        "data": {
            "Persiapan Lahan": ["Olah tanah sempurna: Bajak sedalam 20-25 cm, lalu garu untuk meratakan.", "Perbaikan pH: Jika tanah masam (pH < 6), aplikasikan Dolomit 1-2 ton/ha, 2-4 minggu sebelum tanam.", "Pupuk Dasar: Berikan pupuk kompos atau kandang 5-10 ton/ha dan pupuk anorganik seperti SP-36 sesuai dosis rekomendasi."],
            "Persemaian & Penanaman": ["Perlakuan Benih: Rendam benih dalam larutan PGPR untuk meningkatkan vigor dan ketahanan penyakit.", "Sistem Tanam: Terapkan sistem Jajar Legowo (misal, 2:1 atau 4:1) untuk meningkatkan populasi dan penetrasi sinar matahari.", "Umur Bibit: Pindahkan bibit ke lahan pada umur 15-21 Hari Setelah Semai (HSS)."],
            "Pemupukan Susulan": ["Fase Vegetatif (7-10 HST): Fokus pada Nitrogen (Urea) untuk merangsang anakan.", "Fase Awal Generatif (30-35 HST): Berikan NPK seimbang untuk mendukung pembentukan malai.", "Fase Pengisian Bulir (50-60 HST): Fokus pada Kalium (KCL) untuk pengisian gabah yang optimal."],
            "Hama & Penyakit Umum": ["Wereng Batang Coklat (WBC): Gunakan varietas tahan, tanam serempak, dan lakukan monitoring rutin.", "Penyakit Blas: Hindari pemupukan Nitrogen berlebih, gunakan fungisida hayati (Trichoderma) atau kimia jika serangan tinggi.", "Tikus: Terapkan sanitasi lingkungan dan gropyokan massal sebelum masa tanam."]
        }
    },
    "cabai": {
        "name": "Cabai (Capsicum sp.)", "icon": "🌶️",
        "data": {
            "Persiapan Lahan": ["Bedengan: Buat bedengan dengan lebar 100-120 cm dan tinggi 30-40 cm, beri jarak antar bedengan 60-80 cm.", "pH Tanah: Cabai sangat sensitif terhadap pH masam. Pastikan pH berada di rentang 6.0 - 7.0 dengan aplikasi Dolomit.", "Mulsa: Gunakan mulsa plastik perak-hitam untuk menekan gulma, menjaga kelembaban, dan mengurangi hama."],
            "Pembibitan & Penanaman": ["Media Semai: Gunakan campuran tanah, kompos, dan arang sekam yang steril.", "Pindah Tanam: Bibit siap dipindah tanam setelah berumur 25-30 HSS atau memiliki 4-5 helai daun.", "Jarak Tanam: Umumnya 60x70 cm atau 70x70 cm, tergantung varietas."],
            "Pemupukan & Perawatan": ["Sistem Kocor: Lakukan pemupukan susulan dengan sistem kocor setiap 7-10 hari sekali.", "Fase Vegetatif: Gunakan pupuk dengan kandungan N tinggi (misal, NPK 25-7-7 atau MOL Keong).", "Fase Generatif: Ganti ke pupuk dengan P dan K tinggi (misal, NPK 16-16-16, MKP, atau MOL Bonggol Pisang) untuk merangsang bunga dan buah.", "Perempelan: Buang tunas air yang tumbuh di bawah cabang utama (cabang Y) untuk memaksimalkan pertumbuhan ke atas."],
            "Hama & Penyakit Umum": ["Antraknosa (Patek): Jaga kebersihan kebun, gunakan benih sehat, dan aplikasikan fungisida (hayati atau kimia) secara preventif saat musim hujan.", "Thrips & Tungau: Menyebabkan daun keriting. Aplikasikan akarisida atau pestisida nabati (misal, dari daun mimba).", "Lalat Buah: Gunakan perangkap petrogenol untuk memantau dan mengendalikan populasi."]
        }
    },
    "jagung": {
        "name": "Jagung (Zea mays)", "icon": "🌽",
        "data": {
            "Persiapan Lahan": ["Pengolahan Tanah: Bajak tanah sedalam 15-20 cm untuk menggemburkan tanah.", "Pupuk Dasar: Berikan pupuk kandang atau kompos bersamaan dengan pupuk P dan sebagian pupuk K."],
            "Penanaman": ["Jarak Tanam: Umumnya 70-75 cm antar baris dan 20-25 cm dalam baris, 1-2 benih per lubang.", "Waktu Tanam: Sangat bergantung pada ketersediaan air. Idealnya di awal musim hujan."],
            "Pemupukan Susulan": ["Fokus Nitrogen: Jagung adalah tanaman yang 'rakus' Nitrogen.", "Pemupukan ke-1 (15 HST): Berikan sebagian dosis Urea dan KCL.", "Pemupukan ke-2 (30-35 HST): Berikan sisa dosis Urea untuk mendukung pertumbuhan vegetatif maksimal sebelum pembungaan."],
            "Hama & Penyakit Umum": ["Ulat Grayak (Spodoptera frugiperda): Hama paling merusak. Lakukan monitoring intensif dan aplikasikan insektisida yang direkomendasikan.", "Penyakit Bulai: Disebabkan oleh jamur. Gunakan benih yang sudah diberi perlakuan fungisida (metalaxyl).", "Penggerek Batang: Terapkan sanitasi dengan menghancurkan sisa-sisa tanaman setelah panen."]
        }
    }
}

FERTILIZER_DOSAGE_DB = {
    "padi": {
        "name": "Padi",
        "anorganik_kg_ha": {"Urea": 225, "SP-36": 125, "KCL": 75},
        "organik_ton_ha": {"Pupuk Kandang Sapi": 10, "Pupuk Kandang Ayam": 5},
        "dolomit_ton_ha_asam": 1.5
    },
    "cabai": {
        "name": "Cabai",
        "anorganik_kg_ha": {"Urea": 150, "SP-36": 250, "KCL": 200},
        "organik_ton_ha": {"Pupuk Kandang Sapi": 15, "Pupuk Kandang Ayam": 10},
        "dolomit_ton_ha_asam": 2.0
    },
    "jagung": {
        "name": "Jagung",
        "anorganik_kg_ha": {"Urea": 250, "SP-36": 125, "KCL": 75},
        "organik_ton_ha": {"Pupuk Kandang Sapi": 10, "Pupuk Kandang Ayam": 7},
        "dolomit_ton_ha_asam": 1.5
    }
}


# --- Fungsi Helper & Logika Bisnis ---
def analyze_leaf_with_ml(image_data):
    # ... (Fungsi ini tidak berubah)
    nparr = np.fromstring(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None: return None, None, None
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv_image, lower_green, upper_green)
    if cv2.countNonZero(mask) == 0: return None, None, None
    avg_hue = cv2.mean(hsv_image, mask=mask)[0]
    if bwd_model is None: raise RuntimeError("Model BWD tidak bisa dimuat.")
    input_data = np.array([[avg_hue]])
    predicted_score = bwd_model.predict(input_data)[0]
    confidence = np.max(bwd_model.predict_proba(input_data)) * 100
    return avg_hue, int(predicted_score), confidence

def get_fertilizer_recommendation(data):
    # ... (Fungsi ini tidak berubah)
    ph_tanah = float(data['ph_tanah'])
    rekomendasi_utama = ""
    list_peringatan = []
    if ph_tanah < 6.0:
        rekomendasi_utama = "Prioritaskan aplikasi Dolomit untuk menaikkan pH."
        list_peringatan.append("Peringatan: Ketersediaan Fosfor (P) sangat rendah.")
    elif ph_tanah > 7.2:
        rekomendasi_utama = "Pertimbangkan aplikasi Belerang (Sulfur) untuk menurunkan pH."
        list_peringatan.append("Peringatan: Ketersediaan unsur mikro (Besi, Mangan, Seng) rendah.")
    else:
        rekomendasi_utama = "Kondisi pH tanah optimal. Lanjutkan dengan pemupukan berikut:"
    if recommendation_model is None: raise RuntimeError("Model Rekomendasi tidak bisa dimuat.")
    input_df = np.array([[data['ph_tanah'], data['skor_bwd'], data['kelembaban_tanah'], data['umur_tanaman_hari']]])
    prediksi_ml = recommendation_model.predict(input_df)[0]
    rekomendasi_pupuk_ml = {
        "Rekomendasi N (kg/ha)": round(prediksi_ml[0], 2),
        "Rekomendasi P (kg/ha)": round(prediksi_ml[1], 2),
        "Rekomendasi K (kg/ha)": round(prediksi_ml[2], 2)
    }
    return {"rekomendasi_utama": rekomendasi_utama, "rekomendasi_pupuk_ml": rekomendasi_pupuk_ml, "peringatan_penting": list_peringatan}

# --- Definisi Endpoint API ---

@app.route('/')
def home():
    return render_template('index.html')

# Endpoint Modul 1-6 (tidak berubah)
@app.route('/analyze', methods=['POST'])
def analyze_bwd_endpoint():
    if 'file' not in request.files: return jsonify({'error': 'Tidak ada file'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'File tidak dipilih'}), 400
    try:
        hue, score, confidence = analyze_leaf_with_ml(file.read())
        if score is None: return jsonify({'success': False, 'message': 'Tidak ada objek daun'}), 400
        return jsonify({'success': True, 'bwd_score': score, 'avg_hue_value': round(hue, 2), 'confidence_percent': round(confidence, 2)})
    except Exception as e:
        app.logger.error(f"Error di /analyze: {e}")
        return jsonify({'error': f'Gagal memproses: {str(e)}'}), 500

@app.route('/recommendation', methods=['POST'])
def recommendation_endpoint():
    try:
        data = request.get_json()
        recommendation = get_fertilizer_recommendation(data)
        return jsonify({'success': True, 'recommendation': recommendation})
    except Exception as e:
        app.logger.error(f"Error di /recommendation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analyze-npk', methods=['POST'])
def analyze_npk_endpoint():
    try:
        data = request.get_json()
        n, p, k = int(data['n_value']), int(data['p_value']), int(data['k_value'])
        conn = sqlite3.connect('agrisensa.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO npk_readings (n_value, p_value, k_value) VALUES (?, ?, ?)", (n, p, k))
        conn.commit()
        conn.close()
        analysis = {
            "Nitrogen (N)": {"label": "Optimal" if 100 <= n <= 200 else ("Rendah" if n < 100 else "Berlebih"), "rekomendasi": "Jaga level N untuk pertumbuhan daun."},
            "Fosfor (P)": {"label": "Optimal" if 20 <= p <= 40 else ("Rendah" if p < 20 else "Berlebih"), "rekomendasi": "Penting untuk akar dan bunga."},
            "Kalium (K)": {"label": "Optimal" if 150 <= k <= 250 else ("Rendah" if k < 150 else "Berlebih"), "rekomendasi": "Penting untuk kualitas buah."}
        }
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        app.logger.error(f"Error di /analyze-npk: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
@app.route('/get-prices', methods=['POST'])
def get_prices_endpoint():
    SIMULATED_PRICES = {
        "cabai_merah_keriting": {"name": "Cabai Merah Keriting", "unit": "kg", "prices": {"Pasar Induk Kramat Jati": 45000, "Supermarket Rita": 55000, "Pasar Ekspor (FOB)": 75000}},
        "bawang_merah": {"name": "Bawang Merah", "unit": "kg", "prices": {"Pasar Induk Kramat Jati": 30000, "Supermarket Rita": 40000, "Pasar Ekspor (FOB)": 50000}}
    }
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        if not commodity_id: return jsonify({'success': False, 'error': 'Komoditas tidak dipilih'})
        price_data = SIMULATED_PRICES.get(commodity_id)
        if not price_data: return jsonify({'success': False, 'error': 'Data harga tidak ditemukan'})
        for market in price_data["prices"]: price_data["prices"][market] = random.randint(int(price_data["prices"][market] * 0.95), int(price_data["prices"][market] * 1.05))
        return jsonify({'success': True, 'data': price_data})
    except Exception as e:
        app.logger.error(f"Error di /get-prices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-knowledge', methods=['POST'])
def get_knowledge_endpoint():
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        if not commodity_id: return jsonify({'success': False, 'error': 'Komoditas tidak dipilih'})
        knowledge_data = KNOWLEDGE_BASE.get(commodity_id)
        if not knowledge_data: return jsonify({'success': False, 'error': 'Informasi tidak ditemukan'})
        return jsonify({'success': True, 'data': knowledge_data})
    except Exception as e:
        app.logger.error(f"Error di /get-knowledge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Endpoint BARU untuk Modul 7 ---
@app.route('/calculate-fertilizer', methods=['POST'])
def calculate_fertilizer_endpoint():
    """Endpoint untuk Kalkulator Pupuk Dasar Holistik."""
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        area_sqm = float(data.get('area_sqm', 0))
        ph_tanah = float(data.get('ph_tanah', 7.0)) # Ambil pH, default 7.0 jika tidak ada

        if not commodity_id or area_sqm <= 0:
            return jsonify({'success': False, 'error': 'Input tidak valid.'})

        dosage_data = FERTILIZER_DOSAGE_DB.get(commodity_id)
        if not dosage_data:
            return jsonify({'success': False, 'error': 'Data dosis untuk komoditas ini tidak ditemukan.'})

        area_ha = area_sqm / 10000.0

        # Siapkan dictionary hasil
        results = {
            "anorganik": {},
            "organik": {},
            "perbaikan_tanah": {}
        }

        # Hitung kebutuhan pupuk anorganik
        for fertilizer, dosage_per_ha in dosage_data["anorganik_kg_ha"].items():
            results["anorganik"][fertilizer] = round(dosage_per_ha * area_ha, 2)
        
        # Hitung kebutuhan pupuk organik
        for fertilizer, dosage_per_ha in dosage_data["organik_ton_ha"].items():
            # Konversi ton ke kg (1 ton = 1000 kg)
            required_kg = (dosage_per_ha * 1000) * area_ha
            results["organik"][fertilizer] = round(required_kg, 2)
            
        # Hitung kebutuhan Dolomit jika tanah asam
        if ph_tanah < 6.0:
            dolomit_dosage_ha = dosage_data.get("dolomit_ton_ha_asam", 0)
            required_dolomit_kg = (dolomit_dosage_ha * 1000) * area_ha
            results["perbaikan_tanah"]["Dolomit"] = round(required_dolomit_kg, 2)

        return jsonify({'success': True, 'data': results, 'commodity_name': dosage_data['name'], 'area_sqm': area_sqm})

    except Exception as e:
        app.logger.error(f"Error di /calculate-fertilizer: {e}")
        return jsonify({'success': False, 'error': 'Terjadi kesalahan saat menghitung.'}), 500


# --- Menjalankan Aplikasi ---
if __name__ == '__main__':
    app.run(debug=True)

=======
from flask import Flask

# Membuat instance atau objek dari aplikasi Flask
app = Flask(__name__)

# Mendefinisikan sebuah "route" atau URL endpoint untuk halaman utama ('/')
@app.route('/')
def hello_world():
    # Fungsi ini akan dijalankan saat seseorang mengunjungi halaman utama
    # dan akan mengembalikan teks sebagai respons
    return 'Hello, Agrisensa!'

# Baris ini memastikan server hanya berjalan saat file ini dieksekusi langsung
if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> 8336b2b3454922b5bd96d2e33fe8139ab5a096af
