from flask import Flask, render_template, request, redirect, url_for
import boto3
import pymysql
import os

app = Flask(__name__)

# Konfigurasi S3 (Ambil dari Environment Variables GitHub Secrets)
S3_BUCKET = os.environ.get('S3_BUCKET')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Konfigurasi RDS
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME', 'db_uts_cloud')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Tidak ada file yang dipilih"
    
    file = request.files['file']
    
    if file.filename == '':
        return "Nama file kosong"

    try:
        # 1. Upload ke S3
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={'ACL': 'public-read'} # Agar file bisa dilihat publik
        )
        
        # 2. Simpan info ke RDS (Contoh log transaksi)
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        with connection.cursor() as cursor:
            sql = "INSERT INTO uploads (filename) VALUES (%s)"
            cursor.execute(sql, (file.filename,))
        connection.commit()
        connection.close()

        return f"File {file.filename} Berhasil Diupload ke S3 dan tercatat di RDS!"
    
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)