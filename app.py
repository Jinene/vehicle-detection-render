import os
import time
from flask import Flask, jsonify, request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
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
        <title>Vehicle Detection API</title>
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
            .header p {
                font-size: 1.2em;
                opacity: 0.9;
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
                transition: transform 0.2s;
            }
            .endpoint-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
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
            .status-badge {
                display: inline-block;
                padding: 5px 15px;
                background: #27ae60;
                color: white;
                border-radius: 20px;
                font-weight: bold;
                margin-left: 10px;
            }
            .warning {
                background: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Vehicle Detection API</h1>
                <p>Powered by Flask & Deployed on Render.com Free Tier</p>
            </div>
            
            <div class="content">
                <div class="card">
                    <h2>System Status: <span class="status-badge">🟢 OPERATIONAL</span></h2>
                    <p>This service provides vehicle detection API endpoints.</p>
                </div>

                <div class="warning">
                    <strong>Note:</strong> Basic API is running. Computer vision features will be added after successful deployment.
                </div>
                
                <div class="card">
                    <h3>📊 Current Statistics</h3>
                    <div id="stats">
                        <p>📈 Vehicles Detected: <strong>0</strong></p>
                        <p>🔄 Total Detections: <strong>0</strong></p>
                        <p>🤖 Model Status: <strong>Basic API Ready</strong></p>
                        <p>⏰ Uptime: <strong id="uptime">0</strong> seconds</p>
                        <p>🌐 Platform: <strong>render-free</strong></p>
                    </div>
                </div>
                
                <h3>🔗 API Endpoints</h3>
                <div class="endpoints">
                    <div class="endpoint-card">
                        <span class="method get">GET</span>
                        <h4>System Status</h4>
                        <div class="url">/api/status</div>
                        <p>Check system status and current vehicle count</p>
                    </div>
                    
                    <div class="endpoint-card">
                        <span class="method post">POST</span>
                        <h4>Detect Vehicles</h4>
                        <div class="url">/api/detect</div>
                        <p>Upload an image for vehicle detection</p>
                        <p><strong>Body:</strong> form-data with 'image' file</p>
                    </div>
                    
                    <div class="endpoint-card">
                        <span class="method get">GET</span>
                        <h4>Health Check</h4>
                        <div class="url">/health</div>
                        <p>Simple health check endpoint</p>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🛠️ How to Use</h3>
                    <p><strong>For ESP32 Integration:</strong></p>
                    <ol>
                        <li>Capture image with ESP32 camera</li>
                        <li>Send POST request to <code>/api/detect</code> with image data</li>
                        <li>Receive JSON response with vehicle count</li>
                    </ol>
                    
                    <p><strong>Example cURL:</strong></p>
                    <div class="url">
                        curl -X POST -F "image=@car.jpg" https://your-app.onrender.com/api/detect
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Update uptime
            function updateUptime() {
                const startTime = Date.now() / 1000;
                setInterval(() => {
                    const uptime = Math.round((Date.now() / 1000) - startTime);
                    document.getElementById('uptime').textContent = uptime;
                }, 1000);
            }
            updateUptime();
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
        'detector_ready': False,
        'model': 'basic-api',
        'platform': 'render-free',
        'uptime': time.time() - app_start_time,
        'timestamp': time.time(),
        'message': 'Basic API running. Computer vision features pending installation.'
    })

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Main detection endpoint - SIMULATED for now"""
    global vehicle_count, total_detections
    
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided. Send as form-data with "image" field.'
            }), 400
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image selected'
            }), 400
        
        # Read image data (but don't process yet)
        image_data = image_file.read()
        
        if len(image_data) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty image file'
            }), 400
        
        # Simulate detection for now
        # In a real scenario, this would use YOLO/OpenCV
        simulated_vehicles = 2  # Simulate finding 2 vehicles
        
        vehicle_count = simulated_vehicles
        total_detections += 1
        
        return jsonify({
            'success': True,
            'vehicles_detected': simulated_vehicles,
            'message': 'SIMULATED DETECTION - Computer vision libraries not yet installed',
            'timestamp': time.time(),
            'processing_time': 'simulated',
            'note': 'Install OpenCV and Ultralytics after successful deployment'
        })
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'vehicle-detection-basic',
        'timestamp': time.time(),
        'message': 'Basic API is running successfully'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting Basic Vehicle Detection API on port {port}...")
    logger.info("📝 Note: Computer vision features will be added after successful deployment")
    app.run(host='0.0.0.0', port=port, debug=False)
