from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import subprocess
import threading
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Config from .env
MESHROOM_PATH = os.getenv('MESHROOM_PATH')
BASE_UPLOAD_FOLDER = os.path.abspath(os.getenv('UPLOAD_DIR', '../storage/app/public/uploads'))
BASE_OUTPUT_FOLDER = os.path.abspath(os.getenv('OUTPUT_DIR', './outputs'))

@app.route('/upload', methods=['POST'])
def handle_upload_request():
    try:
        data = request.get_json()
        timestamp = data.get('timestamp')
        if not timestamp:
            return jsonify({'error': 'Missing timestamp.'}), 400

        upload_dir = os.path.join(BASE_UPLOAD_FOLDER, timestamp)
        output_dir = os.path.join(BASE_OUTPUT_FOLDER, timestamp)

        if not os.path.exists(upload_dir):
            return jsonify({'error': f"Upload directory not found: {upload_dir}"}), 404

        os.makedirs(output_dir, exist_ok=True)

        threading.Thread(target=reconstruct_3d, args=(upload_dir, output_dir, timestamp)).start()

        return jsonify({'message': 'Reconstruction started.', 'timestamp': timestamp}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def reconstruct_3d(upload_dir, output_dir, timestamp):
    
   laravel_port = os.getenv("CALLBACK_PORT", "8000")
   callback_url = f"http://localhost:{laravel_port}/api/photogrammetry/callback"


    try:
        command = [MESHROOM_PATH, "--input", upload_dir, "--output", output_dir]
        subprocess.run(command, check=True)

        model_path = os.path.join(output_dir, 'texturedMesh.obj')
        success = os.path.exists(model_path)

        status = 'success' if success else 'model_missing'
        message = 'Model reconstructed' if success else 'Meshroom finished, but model not found'

    except subprocess.CalledProcessError as e:
        status = 'error'
        message = f'Meshroom failed: {str(e)}'

    except Exception as e:
        status = 'exception'
        message = f'Unexpected error: {str(e)}'

    # 🔁 Send result back to Laravel
    try:
        requests.post(callback_url, json={
            'timestamp': timestamp,
            'status': status,
            'message': message
        })
        print(f"Callback to Laravel sent with status: {status}")
    except Exception as e:
        print(f"Failed to notify Laravel: {e}")

if __name__ == "__main__":
    port = int(os.getenv('MESH_PORT', 8000))
    app.run(host="0.0.0.0", port=port)
