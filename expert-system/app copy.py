from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from sklearn.ensemble import RandomForestClassifier
import joblib
import pandas as pd


app = Flask(__name__)
loaded_model = joblib.load('model/model-rf.pkl')

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
    if gender == 0:  # Laki-laki
        energi = (66 + (13.7 * berat_badan_ideal) + (5 * tinggi_badan) - (6.8 * umur))
        faktor_aktivitas = {
            'sangat ringan': 1.30,
            'ringan': 1.65,
            'sedang': 1.76,
            'berat': 2.10
        }
    elif gender == 1:  # Perempuan
        energi = (655 + (9.6 * berat_badan_ideal) + (1.8 * tinggi_badan) - (4.7 * umur))
        faktor_aktivitas = {
            'sangat ringan': 1.30,  
            'ringan': 1.55,        
            'sedang': 1.70,        
            'berat': 2.00          
        }
    else:
        raise ValueError("Gender tidak valid. Gunakan 'L' untuk laki-laki atau 'P' untuk perempuan.")
    

    # Menghitung total kebutuhan energi
    energi_harian = energi * faktor_aktivitas[aktivitas]
    return energi_harian

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

def determine_guldar(gds, gdp, gd2pp):
    messages = []
    gds_high = gds > 199
    gdp_high = gdp > 125
    gd2pp_high = gd2pp > 199


    if gds_high:
        messages.append("Gula Darah Sewaktu melebihi batas normal. Segera lakukan pemeriksaan pada dokter!")
    if gdp_high:
        messages.append("Gula Darah Puasa melebihi batas normal. Segera lakukan pemeriksaan pada dokter!")
    if gd2pp_high:
        messages.append("Gula Darah 2 PP melebihi batas normal. Segera lakukan pemeriksaan pada dokter!")
    
    if gds_high and gdp_high and gd2pp_high: 
        return "Your blood sugar is over the normal limit. Please check with your doctor immediately!"
    elif gds_high or gdp_high or gd2pp_high:
        return "Your blood sugar is over the normal limit. Please check with your doctor immediately!"
    else:
        return "Gula darah anda normal."


    
def determine_gejala(g1,g2,g3,g4):
    if g1 or g2 or g3 or g4 == 1:
        return redirect(url_for('test1'))
    else :
        status = "Anda tidak memiliki gejala diabetes! "
        return redirect(url_for('home', status=status))
    

label_mapping = {0: 'Tidak Memiliki Diabetes', 1: 'Diabetes'}

@app.route("/")
def home():
    status = request.args.get('status')
    return render_template('index.html', status=status)

@app.route("/test", methods=["GET", "POST"])
def test(): 
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
        aktivitas = request.form['aktivitas']

        # Prepare input data for prediction
        input_data = pd.DataFrame({
            'Umur': [umur],
            'Gula darah Sewaktu': [gula_darah_sewaktu],
            'Gula Darah Puasa': [gula_darah_puasa],
            'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
            'Jenis Kelamin': [gender],
        })

        # Predict disease
        penyakit_prediksi = loaded_model.predict(input_data)
        prediksi = label_mapping.get(penyakit_prediksi[0], 'Belum Diketahui')

        # Calculate energy
        energi = calculate_energi(umur, tinggi_badan, aktivitas, gender)
        pesan_energi = "Untuk menjaga gula darah tetap normal, sesuaikan porsi makan dengan kebutuhan energi!"
        
        # Calculate latihan
        guldar = determine_guldar(gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp)

        # Database query to fetch solution
        conn = mysql.connection
        cursor = conn.cursor()
        solusi_code = determine_solusi(energi)
        cursor.execute('SELECT id, standar_porsi_makan, saran_menu_makan FROM solusi WHERE energi = %s', (solusi_code,))
        result = cursor.fetchone()
        solusi_id = result[0]
        spm = result[1]
        smm = result[2]
        cursor.close()

        # Save the data to the database
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO pasien (nama, umur, jenis_kelamin, berat_badan, tinggi_badan, gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp, jenis_aktivitas) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (nama, umur, gender, berat_badan, tinggi_badan, gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp, aktivitas))
        mysql.connection.commit()
        pasien_id = cur.lastrowid
        
        cur.execute('''INSERT INTO hasil_prediksi (pasien_id, status_diagnosa, solusi_id) VALUES (%s, %s, %s)''',
                    (pasien_id, prediksi, solusi_id))
        mysql.connection.commit()
        
        cur.close()
        
        energi = int(energi)
        
        return render_template("test.html", penyakit=prediksi, nama=nama, spm=spm, smm=smm, guldar=guldar, energi=energi)

    return render_template("test.html")

@app.route("/test-1", methods=["GET", "POST"])
def test1():
    if request.method == "POST":
        try:
            # Get form data
            umur = int(request.form["umur"])
            berat_badan = int(request.form['bb'])
            tinggi_badan = int(request.form['tb'])
            gula_darah_sewaktu = int(request.form["gds"])
            gula_darah_puasa = int(request.form["gdp"])
            gula_darah_2_jam_pp = int(request.form["gdpp"])
            gender = int(request.form["s1"])
            aktivitas = request.form['aktivitas']

            # Prepare input data for prediction
            input_data = pd.DataFrame({
                'Umur': [umur],
                'Gula darah Sewaktu': [gula_darah_sewaktu],
                'Gula Darah Puasa': [gula_darah_puasa],
                'Gula Darah 2 Jam PP': [gula_darah_2_jam_pp],
                'Jenis Kelamin': [gender],
            })

            # Predict disease
            penyakit_prediksi = loaded_model.predict(input_data)
            prediksi = label_mapping.get(penyakit_prediksi[0], 'Belum Diketahui')

            # Calculate energy
            energi = calculate_energi(umur, tinggi_badan, aktivitas, gender)
            pesan_energi = "Untuk menjaga gula darah tetap normal, sesuaikan porsi makan dengan kebutuhan energi!"
            
            # Calculate latihan
            guldar = determine_guldar(gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp)

            # Database query to fetch solution
            conn = mysql.connection
            cursor = conn.cursor()
            solusi_code = determine_solusi(energi)
            cursor.execute('SELECT id, standar_porsi_makan, saran_menu_makan FROM solusi WHERE energi = %s', (solusi_code,))
            result = cursor.fetchone()
            
            if result:
                solusi_id, spm, smm = result
            else:
                raise ValueError("No solution found for the given energy value.")

            # Get the latest pasien id
            cursor.execute('SELECT MAX(id) FROM pasien')
            pasien_id = cursor.fetchone()[0]
            
            # Update pasien information
            cursor.execute('''
                UPDATE pasien 
                SET umur=%s, jenis_kelamin=%s, berat_badan=%s, tinggi_badan=%s, gula_darah_sewaktu=%s, 
                    gula_darah_puasa=%s, gula_darah_2_jam_pp=%s, jenis_aktivitas=%s 
                WHERE id=%s
            ''', (umur, gender, berat_badan, tinggi_badan, gula_darah_sewaktu, gula_darah_puasa, gula_darah_2_jam_pp, aktivitas, pasien_id))
            
            # Insert hasil_prediksi
            cursor.execute('''
                INSERT INTO hasil_prediksi (pasien_id, status_diagnosa, solusi_id) 
                VALUES (%s, %s, %s)
            ''', (pasien_id, prediksi, solusi_id))

            # Commit the transaction
            conn.commit()

            # Get pasien name
            cursor.execute('SELECT nama FROM pasien WHERE id = %s', (pasien_id,))
            nama = cursor.fetchone()[0]

        except Exception as e:
            conn.rollback()
            return str(e), 500
        finally:
            cursor.close()

            energi = int(energi)
            
        return render_template("test-1.html", penyakit=prediksi, nama=nama, spm=spm, smm=smm, guldar=guldar, energi=energi)

    return render_template("test-1.html")

@app.route("/prediksi", methods=["GET", "POST"])
def prediksi():
    if request.method == "POST":
        # Get form data
        nama = request.form["nama"]
        gejala1 = int(request.form["g1"])
        gejala2 = int(request.form["g2"])
        gejala3 = int(request.form["g3"])
        gejala4 = int(request.form["g4"])

        # Save the data to the database
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO pasien (nama, g1, g2, g3, g4) VALUES (%s, %s, %s, %s, %s)''',
                    (nama, gejala1, gejala2, gejala3, gejala4))
        mysql.connection.commit()
        cur.close()
        
        return determine_gejala(gejala1,gejala2,gejala3,gejala4)

    return render_template("prediksi.html")

if __name__ == "__main__":
    app.run(debug=True)
