from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import joblib
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

def calculate_berat_badan_ideal(tinggi_badan):
    berat_badan_ideal = (tinggi_badan - 100) - (10 / 100 * (tinggi_badan - 100))
    return berat_badan_ideal

def calculate_energi(umur, tinggi_badan, aktivitas, gender):
    berat_badan_ideal = calculate_berat_badan_ideal(tinggi_badan)
    if gender == 1:
        energi = (66 + (13.7 * berat_badan_ideal) + (5 * tinggi_badan) - (6.8 * umur)) * aktivitas
    else:
        energi = (655 + (9.6 * berat_badan_ideal) + (1.8 * tinggi_badan) - (4.7 * umur)) * aktivitas
    return energi

def determine_solusi(energi):
    if energi <= 1200:
        return '1100'
    elif 1200 < energi <= 1400:
        return '1300'
    elif 1400 < energi <= 1600:
        return '1500'
    elif 1600 < energi <= 1800:
        return '1700'
    elif 1800 < energi <= 2000:
        return '1900'
    elif 2000 < energi <= 2200:
        return '2100'
    elif 2200 < energi <= 2400:
        return '2300'
    elif energi > 2400:
        return '2500'
    else:
        return 'Belum Diketahui'

def determine_latihan(gds):
    latihan_fisik = ''' Saran Latihan Fisik '''
    if gds <= 100:
        return ''' Harus Konsumsi Karbohidrat \n ''' + latihan_fisik
    elif 100 < gds <= 250:
        return latihan_fisik
    elif 200 < gds <= 300:
        return ''' Tidak boleh Latihan Fisik \n ''' + latihan_fisik



label_mapping = {0: 'Diabetes', 1: 'Normal', 2: 'Prediabetes'}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/prediksi", methods=["GET", "POST"])
def prediksi():
    if request.method == "POST":
        # Get form data
        nama = request.form["nama"]
        umur = int(request.form["umur"])
        berat_badan = int(request.form['bb'])
        tinggi_badan = int(request.form['tb'])
        gula_darah_sewaktu = int(request.form["gds"])
        gula_darah_puasa = int(request.form["gdp"])
        gula_darah_2_jam_pp = int(request.form["gdpp"])
        gender = int(request.form["s1"])
        gejala1 = int(request.form["g1"])
        gejala2 = int(request.form["g2"])
        gejala3 = int(request.form["g3"])
        gejala4 = int(request.form["g4"])
        aktivitas = float(request.form.get('aktivitas', 0.0))

        # Prepare input data for prediction
        input_data = pd.DataFrame({
            'Umur': [umur],
            'Gula Darah Puasa': [gula_darah_puasa],
            'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
            'Gender': [gender],
            'Gejala': [gejala1 and gejala2 and gejala3 and gejala4],
        })

        # Predict disease
        penyakit_prediksi = loaded_model.predict(input_data)
        prediksi = label_mapping.get(penyakit_prediksi[0], 'Belum Diketahui')

        # Calculate energy
        energi = calculate_energi(umur, tinggi_badan, aktivitas, gender)
        
        # Calculate latihan
        latihan = determine_latihan(gula_darah_sewaktu)

        # Database query to fetch solution
        conn = mysql.connection
        cursor = conn.cursor()
        solusi_code = determine_solusi(energi)
        cursor.execute('SELECT id, standar_porsi_makan, saran_menu_makan FROM solusi WHERE energi = %s', (solusi_code,))
        result = cursor.fetchone()
        if result:
            solusi_id = result[0]
            spm = result[1]
            smm = result[2]
        else:
            spm = "Data tidak ditemukan"
            smm = "Data tidak ditemukan"
        cursor.close()

        # Save the data to the database
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO pasien (nama, umur, jenis_kelamin, berat_badan, tinggi_badan, g1, g2, g3, g4, gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp, jenis_aktivitas) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (nama, umur, gender, berat_badan, tinggi_badan, gejala1, gejala2, gejala3, gejala4, gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp, aktivitas))
        mysql.connection.commit()
        pasien_id = cur.lastrowid
        
        cur.execute('''INSERT INTO hasil_prediksi (pasien_id, status_diagnosa, solusi_id) VALUES (%s, %s, %s)''',
                    (pasien_id, prediksi, solusi_id))
        mysql.connection.commit()
        
        cur.close()

        return render_template("prediksi.html", penyakit=prediksi, nama=nama, spm=spm, smm=smm, latihan=latihan)

    return render_template("prediksi.html")

if __name__ == "__main__":
    app.run(debug=True)
