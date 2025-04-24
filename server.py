from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import base64
import datetime

app = Flask(__name__)

# Thư mục lưu ảnh
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Đường dẫn database SQLite
DATABASE = 'images.db'

# Khởi tạo database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS images
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT NOT NULL,
                      timestamp TEXT NOT NULL)''')
        conn.commit()

init_db()

# Endpoint để nhận và lưu ảnh
@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    image_data = data['image']
    
    # Giải mã base64
    image_bytes = base64.b64decode(image_data.split(',')[1])  # Bỏ phần tiền tố data:image/png;base64
    filename = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Lưu ảnh
    with open(filepath, 'wb') as f:
        f.write(image_bytes)
    
    # Lưu thông tin vào SQLite
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO images (filename, timestamp) VALUES (?, ?)",
                  (filename, datetime.datetime.now().isoformat()))
        conn.commit()
    
    return jsonify({'filename': filename})

# Endpoint để lấy danh sách ảnh
@app.route('/images', methods=['GET'])
def get_images():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT filename, timestamp FROM images ORDER BY timestamp DESC")
        images = [{'filename': row[0], 'timestamp': row[1]} for row in c.fetchall()]
    return jsonify(images)

# Endpoint để phục vụ file ảnh
@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)