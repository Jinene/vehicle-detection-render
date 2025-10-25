import os
import time
from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# Simple statistics
vehicle_count = 0
total_detections = 0
app_start_time = time.time()

@app.route('/')
def home():
    """Simple dashboard without video streaming"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vehicle Detection - Ready for ESP32</title>
        <style>
            body { font-family: Arial; margin: 40px; background: #1e3c72; color: white; }
            .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
            .header { text-align: center; margin-bottom: 30px; }
            .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 30px 0; }
            .stat-card { background: rgba(255,255,255,0.15); padding: 20px; border-radius: 10px; text-align: center; }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #00ff00; }
            .config { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 10px; margin: 20px 0; }
            input[type="text"] { width: 70%; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Vehicle Detection API</h1>
                <p>Ready to connect your ESP32 camera</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="vehicleCount">0</div>
                    <div>Vehicles Detected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalDetections">0</div>
                    <div>Total Detections</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="uptime">0</div>
                    <div>Seconds Uptime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">✅</div>
                    <div>API Status</div>
                </div>
            </div>
            
            <div class="config">
                <h3>🔧 ESP32 Configuration</h3>
                <p>Your ESP32 can now send images to this API endpoint:</p>
                <div style="background: #2c3e50; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <code>POST https://your-app.onrender.com/api/detect</code>
                </div>
                
                <h4>Test the API:</h4>
                <button onclick="testDetection()">Test Vehicle Detection</button>
                <div id="testResult" style="margin-top: 15px;"></div>
            </div>
            
            <div style="margin-top: 30px;">
                <h3>📋 Next Steps:</h3>
                <ol>
                    <li>This basic API is now running successfully</li>
                    <li>Your ESP32 can send POST requests to /api/detect</li>
                    <li>We'll add computer vision features in the next phase</li>
                </ol>
            </div>
        </div>
        
        <script>
            // Update statistics
            function updateStats() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('vehicleCount').textContent = data.vehicle_count;
                        document.getElementById('totalDetections').textContent = data.total_detections;
                        document.getElementById('uptime').textContent = Math.round(data.uptime);
                    });
            }
            
            // Test detection
            function testDetection() {
                const result = document.getElementById('testResult');
                result.innerHTML = 'Testing...';
                
                fetch('/api/detect', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            result.innerHTML = '✅ Test successful! Vehicles detected: ' + data.vehicles_detected;
                        } else {
                            result.innerHTML = '❌ Test failed: ' + data.message;
                        }
                    })
                    .catch(error => {
                        result.innerHTML = '❌ Connection error: ' + error;
                    });
            }
            
            // Update stats every 3 seconds
            setInterval(updateStats, 3000);
            updateStats();
        </script>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    global vehicle_count, total_detections
    return jsonify({
        'status': 'operational',
        'vehicle_count': vehicle_count,
        'total_detections': total_detections,
        'uptime': time.time() - app_start_time,
        'message': 'Basic API running. Ready for ESP32 integration.'
    })

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Detection endpoint for ESP32"""
    global vehicle_count, total_detections
    
    # Simulate vehicle detection
    detected_vehicles = random.randint(1, 5)
    vehicle_count = detected_vehicles
    total_detections += 1
    
    return jsonify({
        'success': True,
        'vehicles_detected': detected_vehicles,
        'message': 'Simulated detection successful',
        'timestamp': time.time(),
        'note': 'Computer vision features will be added in next deployment'
    })

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Basic Vehicle Detection API running on port {port}")
    print("✅ Deployment successful! Ready for ESP32 integration.")
    app.run(host='0.0.0.0', port=port, debug=False)
