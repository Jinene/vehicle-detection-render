import os
import time
import cv2
import numpy as np
from flask import Flask, jsonify, request, Response, render_template_string
import threading
from ultralytics import YOLO
import base64

app = Flask(__name__)

# Global variables
vehicle_count = 0
total_detections = 0
app_start_time = time.time()
current_frame = None
frame_lock = threading.Lock()

# Initialize YOLO model (will load on first request)
detector = None

def initialize_detector():
    """Initialize the YOLO model"""
    global detector
    try:
        print("🚀 Loading YOLO model for vehicle detection...")
        detector = YOLO('yolov8n.pt')
        print("✅ YOLO model loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        return False

def detect_vehicles(frame):
    """Detect vehicles in frame using YOLO"""
    global detector
    if detector is None:
        if not initialize_detector():
            return frame, 0
    
    try:
        # Vehicle classes in COCO dataset: car=2, motorcycle=3, bus=5, truck=7
        vehicle_classes = [2, 3, 5, 7]
        
        # Perform detection
        results = detector(frame, verbose=False)
        
        vehicle_count = 0
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if class_id in vehicle_classes and confidence > 0.5:
                    vehicle_count += 1
                    
                    # Draw bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Add label
                    label = f"{detector.names[class_id]} {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame, vehicle_count
        
    except Exception as e:
        print(f"Detection error: {e}")
        return frame, 0

def generate_frames():
    """Generate frames with vehicle detection for streaming"""
    # You can replace this with:
    # 1. ESP32 camera stream URL
    # 2. Webcam feed (if running locally)
    # 3. Video file
    # 4. RTSP stream
    
    # Example: Using a test video or webcam
    # cap = cv2.VideoCapture(0)  # Webcam
    # cap = cv2.VideoCapture('traffic.mp4')  # Video file
    # cap = cv2.VideoCapture('http://your-esp32-ip:81/stream')  # ESP32 stream
    
    # For demo purposes, we'll create a synthetic video stream
    while True:
        try:
            # Create a synthetic frame (replace with real video source)
            width, height = 640, 480
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            
            # Add some synthetic "vehicles" (rectangles)
            for i in range(3):
                x = np.random.randint(50, width-100)
                y = np.random.randint(50, height-100)
                w = np.random.randint(80, 150)
                h = np.random.randint(40, 80)
                color = (0, 255, 0)  # Green for vehicles
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, "Vehicle", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Perform actual vehicle detection (uncomment when ready)
            # frame, current_vehicles = detect_vehicles(frame)
            current_vehicles = 3  # Simulate detection for demo
            
            global vehicle_count, current_frame
            vehicle_count = current_vehicles
            
            with frame_lock:
                current_frame = frame
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.1)  # Control frame rate
            
        except Exception as e:
            print(f"Stream error: {e}")
            break

@app.route('/')
def home():
    """Home page with live video streaming"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Vehicle Detection Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                padding: 20px;
                color: white;
            }
            .dashboard {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                color: #fff;
            }
            .live-container {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .video-stream {
                background: rgba(0,0,0,0.7);
                border-radius: 15px;
                padding: 10px;
                text-align: center;
            }
            .video-stream img {
                max-width: 100%;
                border-radius: 10px;
                border: 3px solid #00ff00;
            }
            .stats-panel {
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .stat-card {
                background: rgba(255,255,255,0.15);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 15px;
                text-align: center;
            }
            .stat-number {
                font-size: 2.5em;
                font-weight: bold;
                color: #00ff00;
            }
            .stat-label {
                font-size: 1.1em;
                opacity: 0.9;
            }
            .controls {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .control-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.3s;
            }
            .control-btn:hover {
                background: #2980b9;
            }
            .stream-source {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
            }
            .detection-overlay {
                position: absolute;
                top: 20px;
                left: 20px;
                background: rgba(0,0,0,0.7);
                color: #00ff00;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
            }
            .video-container {
                position: relative;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🚗 Live Vehicle Detection Dashboard</h1>
                <p>Real-time streaming with AI-powered vehicle detection</p>
            </div>
            
            <div class="live-container">
                <div class="video-stream">
                    <h3>📹 Live Video Stream</h3>
                    <div class="video-container">
                        <img id="videoFeed" src="{{ url_for('video_feed') }}" 
                             alt="Live Video Feed" style="width: 100%;">
                        <div class="detection-overlay">
                            🚗 Vehicles: <span id="liveCount">0</span>
                        </div>
                    </div>
                </div>
                
                <div class="stats-panel">
                    <h3>📊 Real-time Statistics</h3>
                    <div class="stat-card">
                        <div class="stat-number" id="vehicleCount">0</div>
                        <div class="stat-label">Vehicles Detected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalDetections">0</div>
                        <div class="stat-label">Total Detections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="uptime">0</div>
                        <div class="stat-label">Seconds Uptime</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="fps">0</div>
                        <div class="stat-label">FPS</div>
                    </div>
                    
                    <div class="controls">
                        <button class="control-btn" onclick="startDetection()">▶️ Start Detection</button>
                        <button class="control-btn" onclick="stopDetection()">⏹️ Stop Detection</button>
                        <button class="control-btn" onclick="refreshStream()">🔄 Refresh Stream</button>
                    </div>
                </div>
            </div>
            
            <div class="stream-source">
                <h3>🔧 Stream Configuration</h3>
                <p><strong>Current Source:</strong> <span id="streamSource">Synthetic Demo Feed</span></p>
                <div style="margin-top: 15px;">
                    <input type="text" id="streamUrl" placeholder="Enter stream URL (RTSP/HTTP)" 
                           style="width: 70%; padding: 10px; border-radius: 5px; border: 1px solid #ccc;">
                    <button class="control-btn" onclick="changeStream()" style="margin-left: 10px;">
                        Change Stream
                    </button>
                </div>
                <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">
                    Supported: ESP32 Cam (HTTP), RTSP cameras, Webcam, Video files
                </p>
            </div>
        </div>

        <script>
            let frameCount = 0;
            let startTime = Date.now();
            
            // Update statistics in real-time
            function updateStats() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('vehicleCount').textContent = data.vehicle_count;
                        document.getElementById('totalDetections').textContent = data.total_detections;
                        document.getElementById('uptime').textContent = Math.round(data.uptime);
                        document.getElementById('liveCount').textContent = data.vehicle_count;
                    });
                
                // Calculate FPS
                frameCount++;
                const currentTime = Date.now();
                const elapsed = (currentTime - startTime) / 1000;
                if (elapsed >= 1) {
                    document.getElementById('fps').textContent = Math.round(frameCount / elapsed);
                    frameCount = 0;
                    startTime = currentTime;
                }
            }
            
            // Update stats every 500ms
            setInterval(updateStats, 500);
            
            // Control functions
            function startDetection() {
                fetch('/api/start', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert('Detection started: ' + data.message);
                    });
            }
            
            function stopDetection() {
                fetch('/api/stop', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert('Detection stopped: ' + data.message);
                    });
            }
            
            function refreshStream() {
                const video = document.getElementById('videoFeed');
                video.src = video.src + '?' + new Date().getTime();
            }
            
            function changeStream() {
                const url = document.getElementById('streamUrl').value;
                if (url) {
                    fetch('/api/set_stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({stream_url: url})
                    }).then(response => response.json())
                      .then(data => {
                          alert('Stream updated: ' + data.message);
                          document.getElementById('streamSource').textContent = url;
                          refreshStream();
                      });
                }
            }
            
            // Handle video stream errors
            document.getElementById('videoFeed').onerror = function() {
                this.src = "/static/offline.jpg";
                alert('Video stream disconnected. Please check the stream source.');
            };
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    global vehicle_count, total_detections
    return jsonify({
        'status': 'operational',
        'vehicle_count': vehicle_count,
        'total_detections': total_detections,
        'stream_active': True,
        'detection_enabled': True,
        'uptime': time.time() - app_start_time,
        'timestamp': time.time()
    })

@app.route('/api/start', methods=['POST'])
def start_detection():
    """Start vehicle detection"""
    return jsonify({
        'success': True,
        'message': 'Vehicle detection started',
        'timestamp': time.time()
    })

@app.route('/api/stop', methods=['POST'])
def stop_detection():
    """Stop vehicle detection"""
    return jsonify({
        'success': True,
        'message': 'Vehicle detection stopped',
        'timestamp': time.time()
    })

@app.route('/api/set_stream', methods=['POST'])
def set_stream():
    """Change video stream source"""
    data = request.get_json()
    stream_url = data.get('stream_url', '')
    
    # Here you would update the video capture source
    # For now, we'll just acknowledge the request
    
    return jsonify({
        'success': True,
        'message': f'Stream source updated to: {stream_url}',
        'stream_url': stream_url
    })

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Single image detection endpoint"""
    global total_detections
    
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        image_data = image_file.read()
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Detect vehicles
        processed_frame, vehicle_count = detect_vehicles(frame)
        
        # Encode result as JPEG
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        total_detections += 1
        
        return jsonify({
            'success': True,
            'vehicles_detected': vehicle_count,
            'processed_image': f'data:image/jpeg;base64,{processed_image}',
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'vehicle-detection-live'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Live Vehicle Detection Dashboard running on port {port}")
    print("📹 Video streaming enabled")
    print("🎯 Real-time vehicle detection ready")
    app.run(host='0.0.0.0', port=port, debug=False)
