from flask import Flask, send_from_directory, request, jsonify
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
import torch
from train import ComplexFingerprintClassifier
from train import FingerprintClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

app = Flask(__name__)
stored_traces = []
stored_heatmaps = []

# Define the websites
WEBSITES = [
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

# Initialize and load the complex model
model = ComplexFingerprintClassifier(input_size=1000, hidden_size=128, num_classes=3)
model.load_state_dict(torch.load('saved_models/complex_fingerprint_classifier.pth', 
                               map_location=torch.device('cpu'), 
                               weights_only=True))
model.eval()

# Load the scaler used during training
SCALER_PATH = 'saved_models/scaler.pkl'
if os.path.exists(SCALER_PATH):
    scaler = joblib.load(SCALER_PATH)
else:
    raise FileNotFoundError(f"Scaler file not found at {SCALER_PATH}. Please ensure the scaler used during training is saved here.")

@app.route('/')
def index():
    return send_from_directory('static', 'prediction_index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    try:
        data = request.get_json()
        trace = data.get('trace')
        if not trace:
            return jsonify({'error': 'No trace data provided'}), 400

        # Pad or truncate trace to 1000 elements
        if len(trace) < 1000:
            trace = trace + [0] * (1000 - len(trace))
        else:
            trace = trace[:1000]

        # Convert to numpy array and reshape for scaling
        trace_array = np.array(trace).reshape(1, -1)
        
        # Normalize the trace using the same scaler used during training
        normalized_trace = scaler.transform(trace_array)
        
        # Convert to tensor
        trace_tensor = torch.tensor(normalized_trace, dtype=torch.float32)

        # Make prediction
        with torch.no_grad():
            outputs = model(trace_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            predicted_website = WEBSITES[predicted.item()]
            confidence_percent = confidence.item() * 100

        # Generate heatmap (using original trace for visualization)
        plt.figure(figsize=(10, 2))
        plt.imshow([trace], aspect='auto', cmap='viridis')
        plt.colorbar(label='Sweep Counts')
        plt.title('Cache Access Trace')
        plt.xlabel('Time Window')
        plt.ylabel('Trace')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

        # Store trace and heatmap
        stored_traces.append(trace)
        heatmap_id = len(stored_heatmaps)
        stored_heatmaps.append({'id': heatmap_id, 'src': f'data:image/png;base64,{img_base64}'})

        return jsonify({
            'heatmap': f'data:image/png;base64,{img_base64}',
            'prediction': {
                'website': predicted_website,
                'confidence': confidence_percent
            },
            'stats': {
                'mean': np.mean(trace),
                'std': np.std(trace),
                'length': len(trace)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_results', methods=['POST'])
def clear_results():
    try:
        stored_traces.clear()
        stored_heatmaps.clear()
        return jsonify({'message': 'Results cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_results', methods=['GET'])
def get_results():
    try:
        return jsonify({
            'traces': stored_traces,
            'heatmaps': stored_heatmaps
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)