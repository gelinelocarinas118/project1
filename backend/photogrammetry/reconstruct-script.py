from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import subprocess
import threading
from datetime import datetime
import requests

# Load .env variables
load_dotenv()

app = Flask(__name__)

# Load config from environment
MESHROOM_PATH = os.getenv('MESHROOM_PATH')
UPLOAD_DIR = os.path.abspath(os.getenv('UPLOAD_DIR', '../storage/app/public/uploads'))
OUTPUT_DIR = os.path.abspath(os.getenv('OUTPUT_DIR', '../storage/app/public/outputs'))
CALLBACK_PORT = os.getenv('CALLBACK_PORT', '8000')
MESH_PORT = int(os.getenv('MESH_PORT', '3001'))

@app.route('/upload', methods=['POST'])
def handle_upload_request():
    try:
        data = request.get_json()
        timestamp = data.get('timestamp')
        if not timestamp:
            return jsonify({'error': 'Missing timestamp'}), 400

        upload_path = os.path.join(UPLOAD_DIR, timestamp)
        output_path = os.path.join(OUTPUT_DIR, timestamp)

        if not os.path.exists(upload_path):
            return jsonify({'error': f'Upload directory not found: {upload_path}'}), 404

        os.makedirs(output_path, exist_ok=True)

        # Run reconstruction in background
        threading.Thread(target=reconstruct_3d, args=(upload_path, output_path, timestamp)).start()

        return jsonify({'message': 'Reconstruction started.', 'timestamp': timestamp}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def reconstruct_3d(input_path, output_path, timestamp):
    callback_url = f"http://localhost:{CALLBACK_PORT}/api/photogrammetry/callback"

    try:
        command = [MESHROOM_PATH, "--input", input_path, "--output", output_path]
        subprocess.run(command, check=True)

        model_path = os.path.join(output_path, 'texturedMesh.obj')
        success = os.path.exists(model_path)

        status = 'success' if success else 'model_missing'
        message = 'Model reconstructed.' if success else 'Meshroom ran, but model not found.'

    except subprocess.CalledProcessError as e:
        status = 'error'
        message = f'Meshroom failed: {str(e)}'

    except Exception as e:
        status = 'exception'
        message = f'Unexpected error: {str(e)}'

    # Call back Laravel
    try:
        response = requests.post(callback_url, json={
            'timestamp': timestamp,
            'status': status,
            'message': message
        })
        print(f"[CALLBACK] Laravel notified: {status} — {response.status_code}")
    except Exception as e:
        print(f"[CALLBACK ERROR] Could not notify Laravel: {e}")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=MESH_PORT)
