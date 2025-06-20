from flask import Flask, send_from_directory, request, jsonify
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
import os

app = Flask(__name__)

stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    try:
        # Receive trace data from frontend as JSON
        data = request.get_json()
        trace = data.get('trace')
        if not trace:
            return jsonify({'error': 'No trace data provided'}), 400

        # Generate heatmap
        plt.figure(figsize=(10, 2))
        plt.imshow([trace], aspect='auto', cmap='viridis')
        plt.colorbar(label='Sweep Counts')
        plt.title('Cache Access Trace')
        plt.xlabel('Time Window')
        plt.ylabel('Trace')

        # Save heatmap to BytesIO and encode as base64
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()

        # Store trace and heatmap
        stored_traces.append(trace)
        heatmap_id = len(stored_heatmaps)
        stored_heatmaps.append({'id': heatmap_id, 'src': f'data:image/png;base64,{img_base64}'})

        # Return heatmap and statistics
        return jsonify({
            'heatmap': f'data:image/png;base64,{img_base64}',
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
        # Clear stored traces and heatmaps
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