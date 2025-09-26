# 🌾 Dasbor Cerdas Agrisensa

Selamat datang di repositori **Agrisensa API**, backend dan dashboard untuk platform pertanian cerdas yang dirancang untuk mendukung petani Indonesia dalam pengambilan keputusan berbasis data. Proyek ini adalah bagian dari portofolio saya sebagai lulusan *Bachelor in Computer Engineering* dari Utel University of Mexico, menunjukkan keahlian dalam pengembangan *full-stack*, integrasi AI, dan solusi teknologi untuk ketahanan pangan.

## 📖 Tentang Proyek

**Dasbor Cerdas Agrisensa** adalah platform berbasis web yang menggabungkan pengetahuan agronomi tradisional dengan teknologi modern seperti AI dan analisis data. Tujuannya adalah membantu petani kecil hingga menengah di Indonesia untuk:
- Mendiagnosis kesehatan tanaman.
- Mengoptimalkan pemupukan berdasarkan analisis tanah.
- Memprediksi hasil panen dengan model AI.
- Memantau tren harga pasar komoditas pertanian.
- Mengakses basis pengetahuan tentang nutrisi tanaman, agen hayati, dan hormon alami.

Proyek ini terinspirasi oleh kebutuhan untuk pertanian berkelanjutan dan efisien, dengan fokus pada solusi organik seperti mikroorganisme lokal (MOL) dan biofungisida seperti *Trichoderma*. Dashboard ini memiliki 19 modul modular, termasuk Kalkulator Pupuk Holistik, Agrimap AI untuk rekomendasi tanaman, dan Intelijen Prediktif dengan Explainable AI (XAI).

## 🚀 Fitur Utama

- **Dokter Tanaman**: Diagnosa gejala tanaman berdasarkan input pengguna (dalam pengembangan).
- **Asisten Agronomi**: Rekomendasi pemupukan berdasarkan analisis tanah dan jenis tanaman.
- **Analisis NPK Manual**: Menghitung kebutuhan Nitrogen, Fosfor, dan Kalium untuk tanaman.
- **Intelijen Harga Pasar**: Menampilkan data harga komoditas pertanian (integrasi data eksternal dalam pengembangan).
- **Pusat Pengetahuan Pertanian**: Basis pengetahuan tentang nutrisi (N, P, K), agen hayati (*Trichoderma*, PGPR, Mikoriza), dan hormon alami (Auksin, Sitokinin, Giberelin).
- **Agrimap AI**: Rekomendasi tanaman berbasis AI berdasarkan data tanah dan iklim.
- **Intelijen Prediktif (XAI)**: Prediksi hasil panen dengan penjelasan transparan tentang logika AI.
- **Kalkulator Konversi Pupuk**: Mengubah kebutuhan unsur hara menjadi dosis pupuk praktis.

## 🛠 Tech Stack

- **Backend**: Node.js + Express.js (atau Python + Flask, tergantung implementasi Anda; sesuaikan jika berbeda).
- **Frontend**: HTML, CSS, JavaScript (dengan rencana untuk migrasi ke React untuk interaktivitas lebih baik).
- **Database**: PostgreSQL untuk menyimpan data pengguna dan pengetahuan pertanian (opsional, jika digunakan).
- **AI/ML**: Model machine learning untuk prediksi panen dan rekomendasi tanaman, diintegrasikan melalui agrisensa-ml (repositori terkait).
- **Deployment**: Render.com untuk hosting API dan dashboard.
- **Library Eksternal**:
  - Chart.js (direncanakan untuk visualisasi tren harga).
  - TensorFlow.js atau Scikit-learn (untuk model AI, jika digunakan).
- **API Eksternal**: Integrasi data harga pasar (misalnya, dari BPS Indonesia, dalam pengembangan).

## 📋 Prasyarat

Untuk menjalankan proyek ini secara lokal, pastikan Anda memiliki:
- Node.js v16+ (atau Python 3.8+, tergantung *tech stack*).
- PostgreSQL (jika digunakan).
- Git untuk kloning repositori.
- Akun Render.com untuk deployment (opsional).

## ⚙️ Instalasi dan Penggunaan

1. **Kloning Repositori**:
   ```bash
   git clone https://github.com/yandri918/agrisensa-api.git
   cd agrisensa-api
   ```

2. **Instal Dependensi**:
   ```bash
   npm install
   ```
   *(Catatan: Jika menggunakan Python, gunakan `pip install -r requirements.txt`.)*

3. **Konfigurasi Lingkungan**:
   - Buat file `.env` di root proyek.
   - Tambahkan variabel seperti:
     ```env
     PORT=3000
     DATABASE_URL=postgres://user:password@localhost:5432/agrisensa
     API_KEY=your_external_api_key
     ```

4. **Jalankan Aplikasi**:
   ```bash
   npm start
   ```
   *(Catatan: Jika menggunakan Python, gunakan `python app.py` atau sesuai framework.)*

5. **Akses Dashboard**:
   - Buka `http://localhost:3000` di browser Anda.
   - Jelajahi modul seperti Pusat Pengetahuan Pertanian atau Kalkulator Pupuk.

## 🧪 Status Proyek

Proyek ini adalah **prototipe** yang dikembangkan sebagai bagian dari portofolio saya. Beberapa modul (misalnya, Analisis Tren Harga, Agrimap AI) masih dalam tahap pengembangan dan menggunakan placeholder untuk data dinamis. Rencana ke depan meliputi:
- Integrasi data harga pasar real-time dari sumber publik.
- Implementasi model AI untuk prediksi panen dan rekomendasi tanaman.
- Peningkatan UI dengan React dan visualisasi interaktif menggunakan Chart.js.
- Penambahan fitur autentikasi untuk personalisasi pengguna.

## 🔍 Tantangan Teknis dan Solusi

- **Tantangan**: Mengintegrasikan data pasar real-time dengan latensi rendah.
  - **Solusi**: Merancang sistem caching menggunakan Redis untuk mengurangi panggilan API eksternal (dalam rencana).
- **Tantangan**: Melatih model AI untuk prediksi panen dengan data lokal yang terbatas.
  - **Solusi**: Menggunakan transfer learning dengan dataset pertanian global dan fine-tuning untuk konteks Indonesia (lihat repositori agrisensa-ml).
- **Tantangan**: Membuat UI yang ramah untuk petani non-teknis.
  - **Solusi**: Menggunakan bahasa sederhana, emoji, dan desain modular untuk aksesibilitas.

## 📈 Cara Berkontribusi

Saya menyambut kontribusi dari komunitas untuk memperkaya proyek ini! Untuk berkontribusi:
1. Fork repositori ini.
2. Buat branch baru: `git checkout -b fitur-anda`.
3. Commit perubahan: `git commit -m "Menambahkan fitur X"`.
4. Push ke branch: `git push origin fitur-anda`.
5. Buat Pull Request di GitHub.

Silakan lihat [CONTRIBUTING.md](CONTRIBUTING.md) untuk panduan lebih lanjut.

## 📬 Kontak

- **Nama**: Yandri (sesuaikan dengan nama Anda).
- **GitHub**: [yandri918](https://github.com/yandri918)
- **Email**: [your-email@example.com](mailto:your-email@example.com)
- **Demo**: [https://agrisensa-api.onrender.com/](https://agrisensa-api.onrender.com/)

## 🙏 Ucapan Terima Kasih

Terima kasih kepada Utel University of Mexico atas pendidikan yang memungkinkan proyek ini, serta komunitas open-source untuk library dan alat yang digunakan. Proyek ini didedikasikan untuk petani Indonesia yang bekerja keras demi ketahanan pangan.

---

**© 2025 Yandri. Dibuat dengan 🌱 untuk pertanian berkelanjutan.**