from flask import Flask, render_template, request
import boto3
import pymysql
import os

app = Flask(__name__)

# Konfigurasi S3 & RDS (Ambil dari Environment Variables)
S3_BUCKET = os.environ.get('S3_BUCKET')
s3 = boto3.client('s3')

@app.route('/')
def index():
    return render_template('index.html')

# Tambahkan logika upload S3 dan simpan ke RDS di sini nanti
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)