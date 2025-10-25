import cv2
import numpy as np
from flask import Flask, Response, jsonify, request
import threading
import time
import os
from ultralytics import YOLO

app = Flask(__name__)

class VehicleDetectionSystem:
    def __init__(self):
        print("🚀 Initializing Vehicle Detection System...")
        # Use the smallest model for free tier compatibility
        self.model = YOLO('yolov8n.pt')
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        self.vehicle_count = 0
        self.total_detections = 0
        print("✅ System initialized successfully!")
    
    def detect_vehicles(self, image_data):
        """Detect vehicles in image data"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return 0, "Invalid image data"
            
            # Perform detection
            results = self.model(image, verbose=False)
            
            vehicle_count = 0
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    if class_id in self.vehicle_classes and confidence > 0.5:
                        vehicle_count += 1
            
            self.vehicle_count = vehicle_count
            self.total_detections += 1
            
            return vehicle_count, "Success"
            
        except Exception as e:
            return 0, f"Error: {str(e)}"

# Initialize the detection system
detector = VehicleDetectionSystem()

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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 Vehicle Detection API</h1>
                <p>Powered by YOLOv8 & Deployed on Render.com Free Tier</p>
            </div>
            
            <div class="content">
                <div class="card">
                    <h2>System Status: <span class="status-badge">🟢 OPERATIONAL</span></h2>
                    <p>This service provides real-time vehicle detection using computer vision and deep learning.</p>
                </div>
                
                <div class="card">
                    <h3>📊 Current Statistics</h3>
                    <div id="stats">
                        <p>🔄 Loading statistics...</p>
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
            // Update statistics
            async function updateStats() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    document.getElementById('stats').innerHTML = `
                        <p>📈 Vehicles Detected: <strong>${data.vehicle_count}</strong></p>
                        <p>🔄 Total Detections: <strong>${data.total_detections}</strong></p>
                        <p>🤖 Model: <strong>${data.model}</strong></p>
                        <p>⏰ Uptime: <strong>${Math.round(data.uptime)} seconds</strong></p>
                        <p>🌐 Platform: <strong>${data.platform}</strong></p>
                    `;
                } catch (error) {
                    console.error('Error fetching stats:', error);
                }
            }
            
            // Update stats immediately and every 10 seconds
            updateStats();
            setInterval(updateStats, 10000);
        </script>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'vehicle_count': detector.vehicle_count,
        'total_detections': detector.total_detections,
        'model': 'yolov8n',
        'platform': 'render-free',
        'uptime': time.time() - app.start_time,
        'timestamp': time.time()
    })

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Main detection endpoint"""
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
        
        # Read image data
        image_data = image_file.read()
        
        if len(image_data) == 0:
            return jsonify({
                'success': False,
                'error': 'Empty image file'
            }), 400
        
        # Perform detection
        vehicle_count, message = detector.detect_vehicles(image_data)
        
        return jsonify({
            'success': True,
            'vehicles_detected': vehicle_count,
            'message': message,
            'timestamp': time.time(),
            'processing_time': 'realtime'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'vehicle-detection',
        'timestamp': time.time()
    })

# Initialize app start time
app.start_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Vehicle Detection API on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
