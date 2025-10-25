import os
import time
from flask import Flask, jsonify, request

app = Flask(__name__)

# Simple in-memory storage
vehicle_count = 0
total_detections = 0
app_start_time = time.time()

@app.route('/')
def home():
    """Home page with information"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vehicle Detection API - READY</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .content {
                padding: 40px;
            }
            .card {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 20px;
                border-left: 5px solid #3498db;
            }
            .success {
                background: #d4edda;
                border-left: 5px solid #28a745;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .endpoints {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .endpoint-card {
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 10px;
                padding: 20px;
            }
            .method {
                display: inline-block;
                padding: 5px 12px;
                background: #3498db;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.9em;
            }
            .method.get { background: #27ae60; }
            .method.post { background: #e67e22; }
            .url {
                background: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                margin: 10px 0;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Vehicle Detection API</h1>
                <p>Successfully Deployed on Render.com Free Tier! 🎉</p>
            </div>
            
            <div class="content">
                <div class="success">
                    <h2>✅ Deployment Successful!</h2>
                    <p>Your Flask API is now live and running. The basic infrastructure is ready.</p>
                </div>
                
                <div class="card">
                    <h3>📊 Current Statistics</h3>
                    <p>Vehicles Detected: <strong>0</strong></p>
                    <p>Total API Calls: <strong id="totalCalls">0</strong></p>
                    <p>Uptime: <strong id="uptime">0</strong> seconds</p>
                </div>
                
                <h3>🔗 API Endpoints (Working)</h3>
                <div class="endpoints">
                    <div class="endpoint-card">
                        <span class="method get">GET</span>
                        <h4>System Status</h4>
                        <div class="url">/api/status</div>
                        <p>Check system status</p>
                    </div>
                    
                    <div class="endpoint-card">
                        <span class="method post">POST</span>
                        <h4>Simulate Detection</h4>
                        <div class="url">/api/detect</div>
                        <p>Test the detection endpoint</p>
                    </div>
                    
                    <div class="endpoint-card">
                        <span class="method get">GET</span>
                        <h4>Health Check</h4>
                        <div class="url">/health</div>
                        <p>Verify API is running</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🛠️ Next Steps</h3>
                    <ol>
                        <li><strong>Test your API</strong> - Use the endpoints above</li>
                        <li><strong>Add computer vision</strong> - Once basic API works, we'll add OpenCV and YOLO</li>
                        <li><strong>Connect ESP32</strong> - Your ESP32 can now send requests to this API</li>
                    </ol>
                    
                    <p><strong>Your API URL:</strong></p>
                    <div class="url" id="apiUrl">https://your-app.onrender.com</div>
                </div>
            </div>
        </div>
        
        <script>
            // Update dynamic content
            function updateDynamicContent() {
                // Update uptime
                const startTime = Math.floor(Date.now() / 1000);
                setInterval(() => {
                    const currentTime = Math.floor(Date.now() / 1000);
                    document.getElementById('uptime').textContent = currentTime - startTime;
                }, 1000);
                
                // Update API URL
                document.getElementById('apiUrl').textContent = window.location.origin;
                
                // Update stats periodically
                setInterval(() => {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('totalCalls').textContent = data.total_detections;
                        });
                }, 3000);
            }
            
            updateDynamicContent();
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
        'message': 'Basic API running successfully. Ready to add computer vision.',
        'uptime': time.time() - app_start_time,
        'timestamp': time.time()
    })

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Simulated detection endpoint"""
    global vehicle_count, total_detections
    
    total_detections += 1
    
    # Simulate vehicle detection
    vehicle_count = 2  # Simulate finding 2 vehicles
    
    return jsonify({
        'success': True,
        'vehicles_detected': vehicle_count,
        'message': 'SIMULATED: API is working! Add OpenCV and YOLO for real detection.',
        'timestamp': time.time(),
        'note': 'This is a simulation. Install computer vision libraries next.'
    })

@app.route('/api/detect', methods=['GET'])
def api_detect_get():
    """GET method for testing"""
    return jsonify({
        'message': 'Send POST request with image data for vehicle detection simulation',
        'example_curl': 'curl -X POST -F "image=@test.jpg" YOUR-APP-URL/api/detect'
    })

@app.route('/health')
def health_check():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'vehicle-detection-basic',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Basic Vehicle Detection API running on port {port}")
    print("✅ Deployment successful! Ready to add computer vision features.")
    app.run(host='0.0.0.0', port=port, debug=False)
