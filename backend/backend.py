from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os # Tambahkan import os
from dotenv import load_dotenv # Tambahkan import load_dotenv

load_dotenv() # Panggil fungsi ini untuk memuat file .env

# Inisialisasi aplikasi Flask
app = Flask(__name__)
# Definisikan domain frontend mana saja yang diizinkan
origins = [
    os.getenv('FRONTEND_URL', 'http://localhost:5173'), 
]

CORS(app, origins=origins)


@app.route("/api/upload", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang dikirim"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400
    
    if file:
        try:
            # LANGKAH 1: Definisikan "kamus" jawaban skala Likert yang umum.
            # Kita menggunakan set untuk pencarian yang lebih cepat.
            SKALA_LIKERT_UMUM = {
                'sangat tidak setuju', 'tidak setuju', 'netral', 'setuju', 'sangat setuju',
                'sangat tidak memuaskan', 'tidak memuaskan', 'cukup', 'memuaskan', 'sangat memuaskan',
                'tidak pernah', 'jarang', 'kadang-kadang', 'sering', 'selalu',
                'sangat buruk', 'buruk', 'biasa saja', 'baik', 'sangat baik',
                '1', '2', '3', '4', '5' # Sertakan juga jika skala sudah dalam bentuk angka
            }

            nilai_likert = {
                'sangat tidak setuju': 1, 'tidak setuju': 2, 'netral': 3, 'setuju': 4, 'sangat setuju': 5,
                'sangat tidak memuaskan': 1, 'tidak memuaskan': 2, 'cukup': 3, 'memuaskan': 4, 'sangat memuaskan': 5,
                'tidak pernah': 1, 'jarang': 2, 'kadang-kadang': 3, 'sering': 4, 'selalu': 5,
                'sangat buruk': 1, 'buruk': 2, 'biasa saja': 3, 'baik': 4, 'sangat baik': 5,
            }

            df = pd.read_csv(file)
            
            # LANGKAH 2: Deteksi kolom Likert secara otomatis
            kolom_likert_terdeteksi = []
            AMBANG_BATAS_LIKERT = 0.8  # Artinya 80% jawaban unik di kolom harus cocok

            for kolom in df.columns:
                # Abaikan kolom yang sudah pasti numerik tapi bukan skala 1-5
                if pd.api.types.is_numeric_dtype(df[kolom]) and df[kolom].nunique() > 5:
                    continue

                # Ambil jawaban unik, bersihkan (lowercase, hapus spasi), dan buang nilai kosong
                jawaban_unik = df[kolom].dropna().unique()
                
                # Jika tidak ada jawaban unik, lewati kolom ini
                if len(jawaban_unik) == 0:
                    continue

                jawaban_bersih = {str(j).lower().strip() for j in jawaban_unik}
                
                # Hitung berapa banyak jawaban bersih yang ada di "kamus" kita
                jumlah_cocok = sum(1 for j in jawaban_bersih if j in SKALA_LIKERT_UMUM)
                
                persentase_cocok = jumlah_cocok / len(jawaban_bersih)
                
                # Jika persentase cocok melebihi ambang batas, anggap ini kolom Likert
                if persentase_cocok >= AMBANG_BATAS_LIKERT:
                    kolom_likert_terdeteksi.append(kolom)

            # Jika tidak ada kolom Likert yang terdeteksi, kirim pesan error
            if not kolom_likert_terdeteksi:
                return jsonify({"error": "Tidak ada kolom dengan format skala Likert yang terdeteksi di dalam file Anda."}), 400

            # LANGKAH 3: Lanjutkan analisis HANYA pada kolom yang terdeteksi
            df_analisis = df[kolom_likert_terdeteksi].copy()

            kolom_pendek = [f'Q{i+1}' for i in range(len(kolom_likert_terdeteksi))]
            pemetaan_kolom = dict(zip(kolom_pendek, kolom_likert_terdeteksi))

            df_analisis.columns = kolom_pendek

            # Konversi jawaban teks ke angka
            for kolom in df_analisis.columns:
                # Ubah isi kolom menjadi string, lowercase, dan strip
                df_analisis[kolom] = df_analisis[kolom].astype(str).str.lower().str.strip()
            
            df_analisis.replace(nilai_likert, inplace=True)

            # Ubah semua kolom menjadi numerik, paksa nilai yang tidak bisa diubah menjadi NaN (Not a Number)
            for kolom in df_analisis.columns:
                 df_analisis[kolom] = pd.to_numeric(df_analisis[kolom], errors='coerce')

            # Hapus baris yang mengandung NaN setelah konversi agar tidak mengganggu perhitungan
            df_analisis.dropna(inplace=True)

            # Jika setelah dibersihkan tidak ada data tersisa
            if df_analisis.empty:
                return jsonify({"error": "Data valid tidak ditemukan setelah pembersihan. Pastikan jawaban di kolom Likert sesuai format."}), 400

            # Lakukan analisis deskriptif
            jumlah_baris, jumlah_kolom_asli = df.shape
            statistik = df_analisis.describe().to_dict()
            matriks_korelasi = df_analisis.corr(method='spearman').to_dict()

            plt.figure(figsize=(10, 8))

            sns.heatmap(pd.DataFrame(matriks_korelasi), annot=True, cmap='coolwarm', fmt='.2f')

            plt.title('Heatmap Korelasi', fontsize = '16')
            # plt.subplots_adjust(left=0.3, bottom=0.4)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

            plt.close()

            # Membangun respon JSON
            hasil_analisis = {
                "nama_file": file.filename,
                "jumlah_baris": jumlah_baris,
                "jumlah_kolom": jumlah_kolom_asli,
                "statistik": statistik,
                "korelasi": matriks_korelasi,
                "kolom_dianalisis": kolom_likert_terdeteksi, # Info tambahan untuk frontend
                "heatmap_base64" : image_base64,
                'pemetaan_kolom' : pemetaan_kolom
            }
            
            return jsonify(hasil_analisis), 200

        except Exception as e:
            print(f"!!! TERJADI ERROR TAK TERDUGA: {e}") 
            return jsonify({"error": f"Terjadi kesalahan internal saat memproses file: {str(e)}"}), 500
        
@app.route("/api/test", methods=["GET"])
def get_test():
    return jsonify({" message: Test Get Berdhasil "})
# Jalankan server saat skrip dieksekusi
if __name__ == "__main__":
    app.run(debug=True, port=5001)