import cv2
import numpy as np
import requests
import xml.etree.ElementTree as ET
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import joblib
import shap
import pandas as pd
import os
import logging
import random
from datetime import datetime, timedelta

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- KONFIGURASI APLIKASI ---
UPLOAD_FOLDER = 'uploads/pdfs'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///agrisensa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
db = SQLAlchemy(app)

# --- Model Database ---
class NpkReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    n_value = db.Column(db.Integer)
    p_value = db.Column(db.Integer)
    k_value = db.Column(db.Integer)

# --- Perintah Inisialisasi Database via CLI ---
@app.cli.command("init-db")
def init_db_command():
    """Membuat tabel database yang diperlukan."""
    with app.app_context():
        db.create_all()
    app.logger.info("Database berhasil diinisialisasi dengan semua tabel.")

# --- Pemuatan Model ML ---
def get_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def load_model(path):
    absolute_path = get_path(path)
    if os.path.exists(absolute_path):
        try:
            model = joblib.load(absolute_path)
            app.logger.info(f"Berhasil MEMUAT model dari: {absolute_path}")
            return model
        except Exception as e:
            app.logger.error(f"GAGAL MEMUAT model dari {absolute_path}: {e}", exc_info=True)
    app.logger.warning(f"PERINGATAN: File model '{absolute_path}' TIDAK DITEMUKAN.")
    return None

bwd_model = load_model('bwd_model.pkl')
recommendation_model = load_model('recommendation_model.pkl')
crop_recommendation_model = load_model('crop_recommendation_model.pkl')
yield_prediction_model = load_model('yield_prediction_model.pkl') # <-- PERBAIKAN DI SINI
advanced_yield_model = load_model('advanced_yield_model.pkl')
shap_explainer = load_model('shap_explainer.pkl')

# --- BASIS DATA PENGETAHUAN LENGKAP ---
KNOWLEDGE_BASE = {
    "padi": { "name": "Padi", "icon": "🌾", "data": {"Persiapan Lahan": ["Olah tanah sempurna: Bajak sedalam 20-25 cm, lalu garu.", "Perbaikan pH: Jika masam (pH < 6), aplikasikan Dolomit 1-2 ton/ha.", "Pupuk Dasar: Berikan kompos 5-10 ton/ha dan SP-36."], "Persemaian & Penanaman": ["Perlakuan Benih: Rendam benih dalam larutan PGPR.", "Sistem Tanam: Terapkan Jajar Legowo untuk meningkatkan populasi.", "Umur Bibit: Pindahkan bibit pada umur 15-21 HSS."], "Pemupukan Susulan": ["Fase Vegetatif (7-10 HST): Fokus pada Nitrogen (Urea).", "Fase Generatif (30-35 HST): Berikan NPK seimbang.", "Fase Pengisian Bulir (50-60 HST): Fokus pada Kalium (KCL)."], "Hama & Penyakit": ["Wereng: Gunakan varietas tahan.", "Blas: Hindari pemupukan N berlebih.", "Tikus: Terapkan sanitasi lingkungan."]} },
    "cabai": { "name": "Cabai", "icon": "🌶️", "data": {"Persiapan Lahan": ["Buat bedengan tinggi (30-40 cm).", "Pastikan pH di rentang 6.0 - 7.0 dengan Dolomit.", "Gunakan mulsa plastik perak-hitam."], "Pembibitan & Penanaman": ["Gunakan media semai steril.", "Pindah tanam setelah bibit berumur 25-30 HSS.", "Jarak tanam 60x70 cm."], "Pemupukan & Perawatan": ["Gunakan sistem kocor setiap 7-10 hari.", "Fase Vegetatif: Fokus pupuk N tinggi.", "Fase Generatif: Ganti ke pupuk P dan K tinggi.", "Lakukan perempelan tunas air."], "Hama & Penyakit": ["Antraknosa (Patek): Jaga kebersihan kebun & gunakan fungisida preventif.", "Thrips & Tungau: Aplikasikan akarisida/pestisida nabati.", "Lalat Buah: Gunakan perangkap petrogenol."]} },
    "jagung": { "name": "Jagung", "icon": "🌽", "data": {"Persiapan Lahan": ["Bajak tanah sedalam 15-20 cm.", "Berikan pupuk kandang/kompos sebagai pupuk dasar."], "Penanaman": ["Jarak tanam 70x20 cm, 1-2 benih per lubang.", "Tanam di awal musim hujan."], "Pemupukan Susulan": ["Jagung 'rakus' Nitrogen.", "Pemupukan ke-1 (15 HST): Urea dan KCL.", "Pemupukan ke-2 (30-35 HST): Sisa dosis Urea."], "Hama & Penyakit": ["Ulat Grayak: Lakukan monitoring intensif.", "Bulai: Gunakan benih yang sudah diberi perlakuan fungisida.", "Penggerek Batang: Lakukan sanitasi sisa tanaman."]} }
}
CHILI_GUIDE = {
    "name": "Cabai (Capsicum sp.)", "icon": "🌶️",
    "description": "Cabai adalah komoditas hortikultura bernilai ekonomi tinggi yang membutuhkan manajemen intensif. Pemanfaatan teknologi presisi dapat meningkatkan efisiensi dan profitabilitas secara signifikan.",
    "sop": {
        "1. Persiapan Lahan (30 Hari Sebelum Tanam)": ["Buat bedengan dengan tinggi 30-40 cm dan lebar 100-120 cm untuk drainase optimal.", "Ukur pH tanah. Jika di bawah 6.0, aplikasikan Dolomit sebanyak 1.5-2 ton/ha dan campurkan dengan tanah.", "Berikan pupuk dasar organik (pupuk kandang ayam/sapi yang matang) sebanyak 15-20 ton/ha.", "Tambahkan pupuk dasar anorganik seperti SP-36 (150-250 kg/ha) dan KCL (100-150 kg/ha).", "Tutup bedengan dengan mulsa plastik perak-hitam untuk menekan gulma dan hama."],
        "2. Persemaian (25-30 Hari)": ["Gunakan media semai steril (campuran tanah, kompos, arang sekam dengan perbandingan 1:1:1).", "Semai benih unggul bersertifikat di dalam tray semai.", "Jaga kelembaban media semai, jangan sampai kering atau terlalu basah.", "Bibit siap pindah tanam setelah memiliki 4-5 helai daun sejati."],
        "3. Penanaman": ["Buat lubang tanam pada mulsa dengan jarak tanam ideal (60x70 cm atau 70x70 cm).", "Lakukan pindah tanam pada sore hari untuk mengurangi stres pada bibit.", "Siram bibit yang baru ditanam secukupnya."],
        "4. Pemeliharaan": ["Lakukan pemupukan susulan dengan sistem kocor setiap 7-10 hari sekali, dimulai pada 1 minggu setelah tanam.", "Fase Vegetatif (1-45 HST): Gunakan pupuk dengan kandungan N tinggi (NPK 25-7-7 atau sejenisnya).", "Fase Generatif (45 HST - Panen): Ganti ke pupuk P dan K tinggi (NPK 16-16-16, MKP, KNO3 Putih).", "Lakukan perempelan (wiwil) tunas air yang tumbuh di bawah cabang utama (cabang Y) untuk fokus pada pertumbuhan generatif."],
        "5. Pengendalian Hama & Penyakit (PHT)": ["Lakukan monitoring rutin untuk deteksi dini.", "Antraknosa (Patek): Jaga kebersihan kebun dan lakukan penyemprotan fungisida (kontak & sistemik) secara preventif saat kelembaban tinggi.", "Thrips & Tungau: Gunakan insektisida/akarisida dengan rotasi bahan aktif (Abamektin, Spinetoram, Imidakloprid) untuk mencegah resistensi.", "Lalat Buah: Pasang perangkap yang mengandung metil eugenol."],
        "6. Panen & Pasca-Panen": ["Panen pertama biasanya dimulai pada umur 75-90 HST, tergantung varietas.", "Lakukan pemetikan pada pagi hari setelah embun kering.", "Panen bisa dilakukan setiap 3-7 hari sekali, tergantung kepadatan buah.", "Sortir buah berdasarkan kualitas (Grade A, B, C) untuk meningkatkan nilai jual."]
    },
    "business_analysis": {
        "title": "Analisis Usaha Tani Cabai per 1000 m²",
        "assumptions": {"Luas Lahan": "1000 meter persegi (0.1 ha)", "Jarak Tanam": "60 x 70 cm", "Populasi Tanaman": "~2,400 tanaman"},
        "costs": [{"item": "Benih Unggul", "amount": "1 sachet (10 gram)", "cost": 200000}, {"item": "Pupuk Kandang Ayam", "amount": "1,500 kg (1.5 ton)", "cost": 1500000}, {"item": "Dolomit", "amount": "200 kg", "cost": 150000}, {"item": "Pupuk Anorganik (SP-36, KCL, NPK)", "amount": "Total ~100 kg", "cost": 800000}, {"item": "Mulsa Plastik", "amount": "1 rol", "cost": 500000}, {"item": "Ajir / Lanjaran Bambu", "amount": "2,400 batang", "cost": 1200000}, {"item": "Pestisida & Fungisida", "amount": "1 siklus tanam", "cost": 1000000}, {"item": "Tenaga Kerja (Olah Tanah - Panen)", "amount": "~50 HOK", "cost": 5000000}],
        "yield_potential": [{"scenario": "Konservatif", "yield_per_plant_kg": 0.5, "total_yield_kg": 1200}, {"scenario": "Optimal", "yield_per_plant_kg": 1.0, "total_yield_kg": 2400}],
        "revenue_scenarios": [{"price_level": "Harga Rendah (saat panen raya)", "price_per_kg": 20000}, {"price_level": "Harga Sedang (normal)", "price_per_kg": 40000}, {"price_level": "Harga Tinggi (di luar musim)", "price_per_kg": 60000}]
    }
}
FERTILIZER_DOSAGE_DB = {
    "padi": { "name": "Padi", "anorganik_kg_ha": {"Urea": 225, "SP-36": 125, "KCL": 75}, "organik_ton_ha": {"Pupuk Kandang Sapi": 10, "Pupuk Kandang Ayam": 5}, "dolomit_ton_ha_asam": 1.5 },
    "cabai": { "name": "Cabai", "anorganik_kg_ha": {"Urea": 150, "SP-36": 250, "KCL": 200}, "organik_ton_ha": {"Pupuk Kandang Sapi": 15, "Pupuk Kandang Ayam": 10}, "dolomit_ton_ha_asam": 2.0 },
    "jagung": { "name": "Jagung", "anorganik_kg_ha": {"Urea": 250, "SP-36": 125, "KCL": 75}, "organik_ton_ha": {"Pupuk Kandang Sapi": 10, "Pupuk Kandang Ayam": 7}, "dolomit_ton_ha_asam": 1.5 }
}
SIMULATED_PRICES = {
    "cabai_merah_keriting": {"name": "Cabai Merah Keriting", "unit": "kg", "prices": {"Pasar Induk": 45000, "Supermarket": 55000, "Ekspor": 75000}},
    "bawang_merah": {"name": "Bawang Merah", "unit": "kg", "prices": {"Pasar Induk": 30000, "Supermarket": 40000, "Ekspor": 50000}}
}
KNOWLEDGE_BASE_REKOMENDASI = {
    "bibit": {
        "dataran_tinggi": "Varietas yang adaptif suhu sejuk dan membutuhkan fluktuasi suhu harian untuk rasa optimal (misal: Stroberi, Kentang, Apel).",
        "dataran_rendah": "Varietas yang tahan panas dan kelembaban tinggi, serta tahan penyakit tular tanah (misal: Tomat Hibrida Tahan Layu Bakteri, Padi Sawah).",
        "tropis": "Varietas 'Day-Neutral' yang pembungaannya tidak bergantung pada panjang hari (misal: Stroberi tipe Day-Neutral, Pepaya).",
        "subtropis": "Varietas yang membutuhkan sinyal perubahan musim dan memiliki periode dormansi ringan (misal: Jeruk, Anggur)."
    },
    "pemupukan": {
        "vegetatif": "Fokus pada pupuk dengan kandungan Nitrogen (N) tinggi untuk merangsang pertumbuhan daun dan batang. Contoh: Urea, MOL Keong, pupuk daun dengan N tinggi.",
        "generatif": "Fokus pada pupuk dengan kandungan Fosfor (P) dan Kalium (K) tinggi untuk merangsang pembungaan, pembuahan, dan meningkatkan kualitas buah. Contoh: NPK Mutiara 16-16-16, MKP, MOL Bonggol Pisang."
    },
    "penyemprotan": {
        "thrips": "Lakukan pergiliran bahan aktif dari Grup IRAC yang berbeda. Siklus 1: Abamektin (Grup 6). Siklus 2: Spinetoram (Grup 5). Gunakan perekat dan lakukan penyemprotan di sore hari.",
        "antraknosa": "Penyakit jamur (patek). Lakukan tindakan preventif dengan menjaga kebersihan kebun. Gunakan fungisida berbahan aktif Mankozeb (kontak) atau Propineb, bisa dirotasi dengan fungisida sistemik seperti Heksakonazol.",
        "default": "Lakukan monitoring rutin. Identifikasi hama/penyakit secara spesifik sebelum melakukan penyemprotan. Terapkan prinsip Pengendalian Hama Terpadu (PHT)."
    }
}
SPRAYING_PROTOCOL = {
    "title": "Protokol Penyemprotan Profesional",
    "steps": [
        "**Waktu Penyemprotan Terbaik:** Lakukan penyemprotan pada pagi hari (sebelum pukul 09:00) atau sore hari (setelah pukul 15:00) saat stomata daun terbuka dan suhu tidak terlalu panas.",
        "**Urutan Pencampuran (WAJIB):** 1. Isi tangki dengan setengah air. 2. Ukur pH air. 3. Masukkan & aduk larutan pembuat asam (jika pH > 7) hingga pH mencapai 5.5-6.5. 4. Baru masukkan pestisida. 5. Tambahkan perekat/perata. 6. Penuhi tangki dengan air.",
        "**Gunakan Perekat & Perata:** Selalu tambahkan perekat, perata, dan penembus untuk memaksimalkan efektivitas pestisida, terutama di musim hujan.",
        "**Kalibrasi Alat Semprot:** Pastikan nozel sprayer Anda menghasilkan kabut yang halus dan merata untuk cakupan yang sempurna."
    ]
}
PESTICIDE_STRATEGY_DB = {
    "thrips": {
        "name": "Strategi Pengendalian Thrips (Penyebab Daun Keriting)",
        "description": "Siklus rotasi 9 minggu ini dirancang untuk mencegah resistensi dengan mengganti Mode of Action (MoA) insektisida setiap 3 minggu.",
        "cycles": [
            { "weeks": "Minggu 1-3", "level": "Level 1: Kontak & Translaminar", "active_ingredient": "Abamektin", "irac_code": "Grup 6", "sop": "Gunakan Abamektin untuk mengendalikan populasi awal. Aplikasikan setiap 5-7 hari sekali." },
            { "weeks": "Minggu 4-6", "level": "Level 2: Sistemik Lokal (MoA Berbeda)", "active_ingredient": "Spinetoram atau Spinosad", "irac_code": "Grup 5", "sop": "Beralih TOTAL ke bahan aktif ini untuk menyerang hama yang selamat dari Grup 6. Aplikasikan setiap 5-7 hari sekali." },
            { "weeks": "Minggu 7-9", "level": "Level 3: Sistemik Penuh (Pukulan Pamungkas)", "active_ingredient": "Imidakloprid atau Tiametoksam", "irac_code": "Grup 4A", "sop": "Gunakan bahan aktif sistemik kuat ini untuk memberantas sisa populasi. Aplikasikan setiap 7-10 hari sekali. JANGAN gunakan grup ini lebih dari satu siklus berturut-turut." }
        ]
    }
}
PH_KNOWLEDGE_BASE = {
    "title": "Ilmu Fundamental pH Tanah", "icon": "🧪",
    "sections": {
        "Definisi-Pentingnya": {"title": "Apa itu pH & Mengapa Penting?", "content": ["pH (potential of Hydrogen) adalah skala untuk mengukur tingkat keasaman atau kebasaan (alkalinitas) larutan tanah.", "Skala pH berkisar dari 0-14, dengan 7 sebagai titik netral. Di bawah 7 bersifat asam, di atas 7 bersifat basa.", "pH disebut sebagai **'Master Variable'** dalam ilmu tanah karena ia mengontrol hampir semua reaksi kimia, terutama ketersediaan unsur hara bagi tanaman."]},
        "Pengaruh-Pupuk": {"title": "pH & Penyerapan Pupuk", "content": ["Tanaman menyerap unsur hara yang larut dalam air. pH tanah menentukan apakah pupuk akan larut atau 'terkunci' menjadi senyawa yang tidak bisa diserap.", "**Rentang Optimal:** Ketersediaan unsur hara tertinggi berada pada rentang pH **sedikit asam hingga netral (6.0 - 7.0)**.", "Di luar rentang ini, efisiensi pemupukan menurun drastis, tidak peduli seberapa banyak pupuk yang Anda berikan."]},
        "Tanah-Asam": {"title": "Masalah Tanah Asam (pH < 6.0)", "content": ["**Pengikatan Fosfor (P):** Fosfor bereaksi dengan Aluminium (Al) dan Besi (Fe), membentuk senyawa tidak larut. Pupuk SP-36 Anda menjadi sia-sia.", "**Kekurangan Hara Sekunder:** Ketersediaan Kalsium (Ca) dan Magnesium (Mg) menurun drastis.", "**Keracunan Logam:** Aluminium (Al) dan Mangan (Mn) menjadi terlalu larut dan bersifat racun bagi akar.", "**Solusi Utama:** Aplikasi **Kapur Pertanian (Dolomit atau Kalsit)** untuk menaikkan pH."]},
        "Tanah-Basa": {"title": "Masalah Tanah Basa (pH > 7.2)", "content": ["**Pengikatan Unsur Mikro:** Unsur mikro esensial seperti **Besi (Fe), Mangan (Mn), dan Seng (Zn)** menjadi tidak larut.", "**Gejala:** Daun muda menguning (klorosis) meskipun unsur tersebut ada di dalam tanah.", "**Pengikatan Fosfor (P) oleh Kalsium:** Fosfor kembali terikat, kali ini oleh Kalsium (Ca) yang melimpah.", "**Solusi Utama:** Aplikasi bahan pembenah tanah yang bersifat asam seperti **Belerang (Sulfur)** atau memperbanyak bahan organik."]}
    }
}


# --- Fungsi Helper & Logika Bisnis ---
def analyze_leaf_with_ml(image_data):
    if bwd_model is None: raise RuntimeError("Model BWD tidak dimuat.")
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None: return None, None, None
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([30, 40, 40]); upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv_image, lower_green, upper_green)
    if cv2.countNonZero(mask) == 0: return None, None, None
    avg_hue = cv2.mean(hsv_image, mask=mask)[0]
    input_data = np.array([[avg_hue]])
    predicted_score = bwd_model.predict(input_data)[0]
    confidence = np.max(bwd_model.predict_proba(input_data)) * 100
    return avg_hue, int(predicted_score), confidence

def get_fertilizer_recommendation(data):
    if recommendation_model is None: raise RuntimeError("Model Rekomendasi tidak dimuat.")
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
    
    input_df = np.array([[data['ph_tanah'], data['skor_bwd'], data['kelembaban_tanah'], data['umur_tanaman_hari']]])
    prediksi_ml = recommendation_model.predict(input_df)[0]
    rekomendasi_pupuk_ml = {
        "Rekomendasi N (kg/ha)": round(float(prediksi_ml[0]), 2),
        "Rekomendasi P (kg/ha)": round(float(prediksi_ml[1]), 2),
        "Rekomendasi K (kg/ha)": round(float(prediksi_ml[2]), 2)
    }
    return {"rekomendasi_utama": rekomendasi_utama, "rekomendasi_pupuk_ml": rekomendasi_pupuk_ml, "peringatan_penting": list_peringatan}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_historical_prices(commodity_id, days):
    price_db = {
        "cabai_merah_keriting": {"name": "Cabai Merah Keriting", "base_price": 45000},
        "bawang_merah": {"name": "Bawang Merah", "base_price": 30000},
        "jagung_pipilan": {"name": "Jagung Pipilan", "base_price": 5500},
        "beras_medium": {"name": "Beras Medium", "base_price": 12000}
    }
    base_info = price_db.get(commodity_id)
    if not base_info: return None, None
    labels = []; prices = []; current_price = base_info["base_price"]; today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=i)
        labels.append(date.strftime('%d %b'))
        prices.append(current_price)
        change_percent = random.uniform(-0.05, 0.05)
        current_price = int(current_price * (1 + change_percent))
        if current_price < 0: current_price = 0
    return list(reversed(labels)), list(reversed(prices))

# --- Definisi Endpoint API ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_bwd_endpoint():
    try:
        if 'file' not in request.files: return jsonify({'success': False, 'error': 'Tidak ada file'}), 400
        file = request.files['file']
        if file.filename == '': return jsonify({'success': False, 'error': 'File tidak dipilih'}), 400
        hue, score, confidence = analyze_leaf_with_ml(file.read())
        if score is None: return jsonify({'success': False, 'message': 'Tidak ada objek daun'}), 400
        return jsonify({'success': True, 'bwd_score': score, 'avg_hue_value': round(hue, 2), 'confidence_percent': round(confidence, 2)})
    except Exception as e:
        app.logger.error(f"Error di /analyze: {e}", exc_info=True)
        return jsonify({'error': 'Kesalahan internal saat menganalisis gambar.'}), 500

@app.route('/recommendation', methods=['POST'])
def recommendation_endpoint():
    try:
        data = request.get_json()
        recommendation = get_fertilizer_recommendation(data)
        return jsonify({'success': True, 'recommendation': recommendation})
    except Exception as e:
        app.logger.error(f"Error di /recommendation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat menghitung rekomendasi.'}), 500

@app.route('/analyze-npk', methods=['POST'])
def analyze_npk_endpoint():
    try:
        data = request.get_json()
        n, p, k = int(data['n_value']), int(data['p_value']), int(data['k_value'])
        new_reading = NpkReading(n_value=n, p_value=p, k_value=k)
        db.session.add(new_reading)
        db.session.commit()
        analysis = { "Nitrogen (N)": {"label": "Optimal" if 100 <= n <= 200 else ("Rendah" if n < 100 else "Berlebih"), "rekomendasi": "Jaga level N."}, "Fosfor (P)": {"label": "Optimal" if 20 <= p <= 40 else ("Rendah" if p < 20 else "Berlebih"), "rekomendasi": "Penting untuk akar & bunga."}, "Kalium (K)": {"label": "Optimal" if 150 <= k <= 250 else ("Rendah" if k < 150 else "Berlebih"), "rekomendasi": "Penting untuk buah."} }
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        app.logger.error(f"Error di /analyze-npk: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Kesalahan internal saat menyimpan data.'}), 500
        
@app.route('/get-prices', methods=['POST'])
def get_prices_endpoint():
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        price_data = SIMULATED_PRICES.get(commodity_id)
        if not price_data: return jsonify({'success': False, 'error': 'Data harga tidak ditemukan'})
        mutable_price_data = price_data.copy()
        mutable_price_data["prices"] = price_data["prices"].copy()
        for market in mutable_price_data["prices"]:
            mutable_price_data["prices"][market] = random.randint(int(price_data["prices"][market] * 0.95), int(price_data["prices"][market] * 1.05))
        return jsonify({'success': True, 'data': mutable_price_data})
    except Exception as e:
        app.logger.error(f"Error di /get-prices: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal pada data harga.'}), 500

@app.route('/get-knowledge', methods=['POST'])
def get_knowledge_endpoint():
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        knowledge_data = KNOWLEDGE_BASE.get(commodity_id)
        if not knowledge_data: return jsonify({'success': False, 'error': 'Informasi tidak ditemukan'})
        return jsonify({'success': True, 'data': knowledge_data})
    except Exception as e:
        app.logger.error(f"Error di /get-knowledge: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal pada basis pengetahuan.'}), 500

@app.route('/calculate-fertilizer', methods=['POST'])
def calculate_fertilizer_endpoint():
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        area_sqm = float(data.get('area_sqm', 0))
        ph_tanah = float(data.get('ph_tanah', 7.0))
        if not commodity_id or area_sqm <= 0: return jsonify({'success': False, 'error': 'Input tidak valid.'})
        dosage_data = FERTILIZER_DOSAGE_DB.get(commodity_id)
        if not dosage_data: return jsonify({'success': False, 'error': 'Data dosis tidak ditemukan.'})
        area_ha = area_sqm / 10000.0
        results = {"anorganik": {}, "organik": {}, "perbaikan_tanah": {}}
        for fert, dose in dosage_data["anorganik_kg_ha"].items(): results["anorganik"][fert] = round(dose * area_ha, 2)
        for fert, dose in dosage_data["organik_ton_ha"].items(): results["organik"][fert] = round((dose * 1000) * area_ha, 2)
        if ph_tanah < 6.0:
            dose_dolomit = dosage_data.get("dolomit_ton_ha_asam", 0)
            results["perbaikan_tanah"]["Dolomit"] = round((dose_dolomit * 1000) * area_ha, 2)
        return jsonify({'success': True, 'data': results, 'commodity_name': dosage_data['name'], 'area_sqm': area_sqm})
    except Exception as e:
        app.logger.error(f"Error di /calculate-fertilizer: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat menghitung.'}), 500

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf_endpoint():
    if 'file' not in request.files: return jsonify({'success': False, 'error': 'Tidak ada file'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'success': False, 'error': 'File tidak dipilih'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': True, 'message': f'File {filename} berhasil diunggah.'})
    return jsonify({'success': False, 'error': 'Tipe file tidak diizinkan. Harap unggah PDF.'}), 400

@app.route('/get-pdfs', methods=['GET'])
def get_pdfs_endpoint():
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
        return jsonify({'success': True, 'files': sorted(files)})
    except Exception as e:
        app.logger.error(f"Error di /get-pdfs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Gagal memuat daftar dokumen.'}), 500

@app.route('/view-pdf/<path:filename>')
def view_pdf_endpoint(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get-integrated-recommendation', methods=['POST'])
def get_integrated_recommendation_endpoint():
    try:
        data = request.get_json()
        ketinggian = data.get('ketinggian'); iklim = data.get('iklim'); fase = data.get('fase'); masalah = data.get('masalah')
        recommendation_data = {"bibit": "Pilih varietas sesuai kondisi.", "pemupukan": "Sesuaikan dengan fase.", "penyemprotan": "Lakukan berdasarkan target."}
        if ketinggian in KNOWLEDGE_BASE_REKOMENDASI['bibit']: recommendation_data['bibit'] = KNOWLEDGE_BASE_REKOMENDASI['bibit'][ketinggian]
        if fase in KNOWLEDGE_BASE_REKOMENDASI['pemupukan']: recommendation_data['pemupukan'] = KNOWLEDGE_BASE_REKOMENDASI['pemupukan'][fase]
        if masalah in KNOWLEDGE_BASE_REKOMENDASI['penyemprotan']: recommendation_data['penyemprotan'] = KNOWLEDGE_BASE_REKOMENDASI['penyemprotan'][masalah]
        else: recommendation_data['penyemprotan'] = KNOWLEDGE_BASE_REKOMENDASI['penyemprotan']['default']
        return jsonify({'success': True, 'data': recommendation_data})
    except Exception as e:
        app.logger.error(f"Error di /get-integrated-recommendation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat memproses rekomendasi.'}), 500

@app.route('/get-spraying-recommendation', methods=['POST'])
def get_spraying_recommendation_endpoint():
    try:
        data = request.get_json()
        pest = data.get('pest')
        if not pest: return jsonify({'success': False, 'error': 'Hama/penyakit tidak dipilih'})
        strategy = PESTICIDE_STRATEGY_DB.get(pest)
        if not strategy: return jsonify({'success': False, 'error': 'Strategi tidak ditemukan.'})
        full_recommendation = {"strategy": strategy, "protocol": SPRAYING_PROTOCOL}
        return jsonify({'success': True, 'data': full_recommendation})
    except Exception as e:
        app.logger.error(f"Error di /get-spraying-recommendation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat memproses rekomendasi.'}), 500

@app.route('/get-ticker-prices', methods=['GET'])
def get_ticker_prices_endpoint():
    try:
        TICKER_DATA = {"cabai_merah_keriting": {"name": "Cabai Merah", "price": 45000, "unit": "kg"}, "bawang_merah": {"name": "Bawang Merah", "price": 30000, "unit": "kg"}, "jagung_pipilan": {"name": "Jagung Pipilan", "price": 5500, "unit": "kg"}, "beras_medium": {"name": "Beras Medium", "price": 12000, "unit": "kg"}}
        live_data = []
        for key, value in TICKER_DATA.items():
            new_price = random.randint(int(value["price"] * 0.98), int(value["price"] * 1.02))
            live_data.append({"name": value["name"], "price": new_price, "unit": value["unit"]})
        return jsonify({'success': True, 'data': live_data})
    except Exception as e:
        app.logger.error(f"Error di /get-ticker-prices: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Gagal memuat data ticker.'}), 500

@app.route('/get-historical-prices', methods=['POST'])
def get_historical_prices_endpoint():
    try:
        data = request.get_json()
        commodity_id = data.get('commodity')
        time_range = int(data.get('range', 30))
        if not commodity_id: return jsonify({'success': False, 'error': 'Komoditas tidak dipilih'}), 400
        labels, prices = generate_historical_prices(commodity_id, time_range)
        if labels is None: return jsonify({'success': False, 'error': 'Data historis tidak ditemukan'}), 404
        return jsonify({'success': True, 'labels': labels, 'prices': prices})
    except Exception as e:
        app.logger.error(f"Error di /get-historical-prices: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat memuat data historis.'}), 500
    
@app.route('/get-commodity-guide', methods=['POST'])
def get_commodity_guide_endpoint():
    try:
        data = request.get_json()
        commodity = data.get('commodity')
        if commodity == 'cabai':
            return jsonify({'success': True, 'data': CHILI_GUIDE})
        else:
            return jsonify({'success': False, 'error': 'Panduan untuk komoditas ini belum tersedia.'})
    except Exception as e:
        app.logger.error(f"Error di /get-commodity-guide: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat memuat panduan.'}), 500

@app.route('/get-ph-info', methods=['GET'])
def get_ph_info_endpoint():
    try:
        return jsonify({'success': True, 'data': PH_KNOWLEDGE_BASE})
    except Exception as e:
        app.logger.error(f"Error di /get-ph-info: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat memuat informasi pH.'}), 500
        
@app.route('/recommend-crop', methods=['POST'])
def recommend_crop_endpoint():
    try:
        if crop_recommendation_model is None:
            raise RuntimeError("Model Rekomendasi Tanaman tidak bisa dimuat. Jalankan train_crop_model.py")
        data = request.get_json()
        features = [float(data.get(k, 0)) for k in ['n_value', 'p_value', 'k_value', 'temperature', 'humidity', 'ph', 'rainfall']]
        input_data = np.array([features])
        prediction = crop_recommendation_model.predict(input_data)[0]
        return jsonify({'success': True, 'recommended_crop': prediction.capitalize()})
    except Exception as e:
        app.logger.error(f"Error di /recommend-crop: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat membuat rekomendasi tanaman.'}), 500

@app.route('/predict-yield', methods=['POST'])
def predict_yield_endpoint():
    try:
        if yield_prediction_model is None:
            raise RuntimeError("Model Prediksi Panen tidak bisa dimuat. Jalankan train_yield_model.py")
        data = request.get_json()
        features = [float(data.get(k, 0)) for k in ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'rainfall', 'ph']]
        input_data = np.array([features])
        prediction = yield_prediction_model.predict(input_data)[0]
        return jsonify({'success': True, 'predicted_yield_ton_ha': round(float(prediction) / 1000, 2)})
    except Exception as e:
        app.logger.error(f"Error di /predict-yield: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat membuat prediksi panen.'}), 500
        
@app.route('/predict-yield-advanced', methods=['POST'])
def predict_yield_advanced_endpoint():
    try:
        if advanced_yield_model is None or shap_explainer is None:
            raise RuntimeError("Model Prediksi Panen Lanjutan atau SHAP explainer tidak bisa dimuat.")

        data = request.get_json()
        
        feature_names = ['Nitrogen', 'Phosphorus', 'Potassium', 'Temperature', 'Rainfall', 'pH']
        features = [float(data.get(name.lower(), 0)) for name in feature_names]
        
        input_data = pd.DataFrame([features], columns=feature_names)
        
        prediction = advanced_yield_model.predict(input_data)[0]

        importances = advanced_yield_model.feature_importances_
        feature_importance_dict = sorted(zip(feature_names, [float(i) for i in importances]), key=lambda x: x[1], reverse=True)

        shap_values = shap_explainer.shap_values(input_data)
        shap_dict = {name: round(float(val), 2) for name, val in zip(feature_names, shap_values[0])}

        return jsonify({
            'success': True, 
            'predicted_yield_ton_ha': round(float(prediction) / 1000, 2),
            'feature_importances': feature_importance_dict,
            'shap_values': shap_dict,
            'base_value': round(float(shap_explainer.expected_value) / 1000, 2)
        })

    except Exception as e:
        app.logger.error(f"Error di /predict-yield-advanced: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Kesalahan internal saat membuat prediksi XAI.'}), 500

# --- Menjalankan Aplikasi (Hanya untuk lokal) ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

