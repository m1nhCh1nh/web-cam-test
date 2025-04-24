from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import base64
import datetime
import logging

app = Flask(__name__)
CORS(app)  # Cho phép tất cả nguồn gốc để tránh lỗi CORS

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình thư mục và database
UPLOAD_FOLDER = 'uploads'
DATABASE = 'images.db'

# Tạo thư mục uploads nếu chưa tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Khởi tạo database
def init_db():
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS images
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             filename TEXT NOT NULL,
                             timestamp TEXT NOT NULL)''')
            conn.commit()
            logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

init_db()

# Endpoint để nhận và lưu ảnh
@app.route('/upload', methods=['POST'])
def upload_image():
    logger.info("Received POST /upload request")
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            logger.warning("Invalid request: Missing image data")
            return jsonify({'error': 'Missing image data'}), 400

        image_data = data['image']
        if not image_data.startswith('data:image/png;base64,'):
            logger.warning("Invalid image format")
            return jsonify({'error': 'Invalid image format'}), 400

        # Giải mã base64
        image_bytes = base64.b64decode(image_data.split(',')[1])
        filename = f"image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Lưu ảnh
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        logger.info(f"Image saved: {filename}")

        # Lưu thông tin vào SQLite
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO images (filename, timestamp) VALUES (?, ?)",
                          (filename, datetime.datetime.now().isoformat()))
            conn.commit()
            logger.info(f"Image metadata saved to database: {filename}")

        return jsonify({'filename': filename}), 200
    except base64.binascii.Error:
        logger.error("Invalid base64 data")
        return jsonify({'error': 'Invalid base64 data'}), 400
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500

# Endpoint để lấy danh sách ảnh
@app.route('/images', methods=['GET'])
def get_images():
    logger.info("Received GET /images request")
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename, timestamp FROM images ORDER BY timestamp DESC")
            images = [{'filename': row[0], 'timestamp': row[1]} for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(images)} images from database")
        return jsonify(images), 200
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error'}), 500

# Endpoint để phục vụ file ảnh
@app.route('/images/<filename>', methods=['GET'])
def serve_image(filename):
    logger.info(f"Serving image: {filename}")
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        logger.warning(f"Image not found: {filename}")
        return jsonify({'error': 'Image not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)