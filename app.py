from flask import Flask, render_template, request, jsonify
import boto3
import pymysql
import os

app = Flask(__name__)

S3_BUCKET = os.environ.get('S3_BUCKET')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'ap-southeast-1')

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER', 'admin')
DB_PASS = os.environ.get('DB_PASS')
DB_NAME = os.environ.get('DB_NAME', 'db_uts_cloud')

def get_db():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER,
        password=DB_PASS, database=DB_NAME
    )

def upload_to_s3(file, folder):
    """Upload file ke S3, return public URL atau None jika gagal."""
    if not file or file.filename == '':
        return None
    key = f"{folder}/{file.filename}"
    s3.upload_fileobj(
        file, S3_BUCKET, key,
        ExtraArgs={'ACL': 'public-read'}
    )
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

@app.route('/')
def index():
    return render_template('index.html')

# ✅ Route sesuai yang dipanggil frontend
@app.route('/api/pengajuan/', methods=['POST'])
def pengajuan():
    try:
        jenis_surat  = request.form.get('jenis_surat', '')
        nama_lengkap = request.form.get('nama_lengkap', '')

        # Ambil semua kemungkinan field file dari frontend
        foto_ktp     = request.files.get('foto_ktp')
        foto_bukti_1 = request.files.get('foto_bukti_1')
        foto_bukti_2 = request.files.get('foto_bukti_2')

        # Upload ke S3
        foto_ktp_url     = upload_to_s3(foto_ktp,     f'pengajuan/{jenis_surat}')
        foto_bukti_1_url = upload_to_s3(foto_bukti_1, 'pengaduan/bukti')
        foto_bukti_2_url = upload_to_s3(foto_bukti_2, 'pengaduan/bukti')

        # Simpan ke RDS
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO uploads
                   (jenis_surat, nama_lengkap, foto_ktp_url,
                    foto_bukti_1_url, foto_bukti_2_url)
                   VALUES (%s, %s, %s, %s, %s)""",
                (jenis_surat, nama_lengkap,
                 foto_ktp_url, foto_bukti_1_url, foto_bukti_2_url)
            )
        conn.commit()
        conn.close()

        # ✅ Return JSON agar frontend bisa membaca URL file
        return jsonify({
            'status': 'success',
            'foto_ktp_url':     foto_ktp_url,
            'foto_bukti_1_url': foto_bukti_1_url,
            'foto_bukti_2_url': foto_bukti_2_url,
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ✅ Endpoint health check untuk banner AWS di dashboard
@app.route('/api/health/')
def health():
    rds_ok  = False
    rds_lat = 0
    s3_ok   = False

    import time
    try:
        t = time.time()
        conn = get_db()
        conn.close()
        rds_ok  = True
        rds_lat = round((time.time() - t) * 1000)
    except:
        pass

    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        s3_ok = True
    except:
        pass

    return jsonify({
        'rds': {'connected': rds_ok, 'latency_ms': rds_lat,
                'engine': 'MySQL', 'host': DB_HOST},
        's3':  {'connected': s3_ok, 'bucket': S3_BUCKET,
                'region': AWS_REGION},
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)