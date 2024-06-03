from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import joblib
import pickle
import pandas as pd

app = Flask(__name__)
loaded_model = joblib.load('model/model-dum6.pkl')

# Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'prediksi_diabetes'

# Initialize MySQL
mysql = MySQL(app)


def calculate_berat_badan_ideal(tinggi_badan, gender):
    if gender == 1: #cowo
        berat_badan_ideal = (tinggi_badan - 100) - (10 / 100 * (tinggi_badan - 100))
    else:
        berat_badan_ideal = (tinggi_badan - 100) - (15 / 100 * (tinggi_badan - 100))
    
    return berat_badan_ideal

def calculate_energi(umur, berat_badan, tinggi_badan, aktivitas, gender):
    berat_badan_ideal = calculate_berat_badan_ideal(tinggi_badan, gender)

    if gender == 1:
        energi = (66 + (13.7 * berat_badan_ideal) + (5 * tinggi_badan) - (6.8 * umur)) * aktivitas
    else:
        energi = (655 + (9.6 * berat_badan_ideal) + (1.8 * tinggi_badan) - (4.7 * umur)) * aktivitas

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
label_mapping = {0: 'Diabetes', 1: 'Normal', 2: 'Prediabetes'}



@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/")
def home():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM pasien''')
    results = cur.fetchall()
    return render_template("index.html", results=results)


@app.route("/prediksi", methods=["GET", "POST"])
def prediksi():
    if request.method == "POST":
        umur = int(request.form["umur"])
        berat_badan = int(request.form['berat_badan'])
        tinggi_badan = int(request.form['tinggi_badan'])
        gula_darah_puasa = int(request.form["gula_darah_puasa"])
        gula_darah_2_jam_pp = int(request.form["gula_darah_2_jam_pp"])
        gender = int(request.form["gender"])
        gejala = int(request.form["gejala"])
        aktivitas = float(request.form.get('aktivitas', 0.0))

        input_data = pd.DataFrame({
            'Umur': [umur],
            # 'Berat Badan': [berat_badan],
            # 'Tinggi Badan': [tinggi_badan],
            'Gula Darah Puasa': [gula_darah_puasa],
            'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
            'Gender': [gender],
            'Gejala': [gejala],
        })

      
        penyakit_prediksi = loaded_model.predict(input_data)
        prediksi = label_mapping.get(penyakit_prediksi[0], 'Belum Diketahui')
        # print("Predicted Disease:", prediksi)
        energi = calculate_energi(umur, berat_badan, tinggi_badan, aktivitas, gender)

        solusi = determine_solusi(energi)
        # print("Determined Solusi:", solusi)
        return render_template("prediksi.html", penyakit=prediksi, solusi=solusi)

    return render_template("prediksi.html")


if __name__ == "__main__":
    app.run(debug=True)
