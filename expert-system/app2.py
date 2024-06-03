from flask import Flask, render_template, request
import joblib
import pickle
import pandas as pd

app = Flask(__name__)

# with open('model/model-dum2.pkl', 'rb') as f:
#     loaded_model = pickle.load(f)
# with open('model/model-dum5.pkl', 'rb') as f:
#     loaded_model = pickle.load(f)
loaded_model = joblib.load('model/model-dum6.pkl')

# training_features = ['Umur', 'Berat Badan', 'Tinggi Badan', 'Gula Darah Puasa', 'Gula Darah 2 Jam PP', 'Gender', 'Gejala']
def calculate_energi(umur, berat_badan, tinggi_badan, aktivitas, gender):
    if gender == 1:  # Laki-laki
        energi = (66 + (13.7 * berat_badan) + (5 * tinggi_badan) - (6.8 * umur)) * aktivitas
    else:  # Perempuan
        energi = (655 + (9.6 * berat_badan) + (1.8 * tinggi_badan) - (4.7 * umur)) * aktivitas

    return energi


def determine_solusi(energi):
    if energi <= 1200:
        return 'E01'
    elif 1200 < energi <= 1400:
        return 'E02'
    elif 1400 < energi <= 1600:
        return 'E03'
    elif 1600 < energi <= 1800:
        return 'E04'
    elif 1800 < energi <= 2000:
        return 'E05'
    elif 2000 < energi <= 2200:
        return 'E06'
    elif 2200 < energi <= 2400:
        return 'E07'
    elif energi > 2400:
        return 'E08'
    else:
        return 'Belum Diketahui'

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        umur = int(request.form["umur"])
        berat_badan = int(request.form['berat_badan'])
        tinggi_badan = int(request.form['tinggi_badan'])
        gula_darah_puasa = int(request.form["gula_darah_puasa"])
        gula_darah_2_jam_pp = int(request.form["gula_darah_2_jam_pp"])
        gender = int(request.form["gender"])
        gejala = int(request.form["gejala"])
        try:
            aktivitas = float(request.form['aktivitas'])
        except KeyError:
            # Lakukan penanganan jika 'aktivitas' tidak ditemukan dalam request.form
            aktivitas = 0.0  # Atau nilai default yang sesuai
        except TypeError:
            # Lakukan penanganan jika 'aktivitas' memiliki nilai None
            aktivitas = 0.0  # Atau nilai default yang sesuai


        # print("Feature Names during Training:", training_features)
        # Membuat DataFrame sesuai dengan input pengguna
        # input_data = pd.DataFrame({
        #     'Umur': [umur],
        #     'Berat Badan': [berat_badan],
        #     'Tinggi Badan': [tinggi_badan],
        #     'Aktivitas': [aktivitas],
        #     'Gula Darah Puasa': [gula_darah_puasa],
        #     'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
        #     'Gender': [gender],
        #     'Gejala': [gejala],
        # })
        # Pastikan nama kolom dan urutan kolom sama dengan saat melatih model
        input_data = pd.DataFrame({
            'Umur': [umur],
            # 'Berat Badan': [berat_badan],
            # 'Tinggi Badan': [tinggi_badan],
            'Gula Darah Puasa': [gula_darah_puasa],
            'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
            'Gender': [gender],
            'Gejala': [gejala],
        })

        # input_data = input_data[training_features]
        # Prediksi penyakit menggunakan model Random Forest
        penyakit_prediksi = loaded_model.predict(input_data)
        # prediksi = loaded_model.classes_[penyakit_prediksi]
        
        # Tentukan solusi berdasarkan energi (gunakan nilai dummy 1500 untuk saat ini)
        energi = calculate_energi(umur, berat_badan, tinggi_badan, aktivitas, gender)

        solusi = determine_solusi(energi)

        return render_template("index.html", penyakit=penyakit_prediksi, solusi=solusi)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)