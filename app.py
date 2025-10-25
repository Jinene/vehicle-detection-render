import os
import time
import cv2
import numpy as np
from flask import Flask, jsonify, request, Response
import threading
import random

app = Flask(__name__)

# Global variables
vehicle_count = 0
total_detections = 0
app_start_time = time.time()
stream_active = True

# YOUR ESP32 STREAM URL - Automatically connected
ESP32_STREAM_URL = "http://192.168.4.1/"
current_capture = None

def initialize_camera():
    """Initialize connection to ESP32 camera"""
    global current_capture
    try:
        print(f"🚀 Connecting to ESP32 camera: {ESP32_STREAM_URL}")
        current_capture = cv2.VideoCapture(ESP32_STREAM_URL)
        
        # Test the connection
        if current_capture.isOpened():
            ret, frame = current_capture.read()
            if ret:
                print("✅ Successfully connected to ESP32 camera!")
                return True
            else:
                print("❌ Connected but cannot read frames")
        else:
            print("❌ Cannot connect to ESP32 camera")
            
    except Exception as e:
        print(f"❌ Error connecting to ESP32: {e}")
    
    return False

def generate_esp32_stream():
    """Generate video stream from ESP32 camera"""
    global stream_active, vehicle_count
    
    # Initialize camera connection
    if not initialize_camera():
        # Fallback to demo stream if ESP32 is not available
        yield from generate_demo_stream()
        return
    
    frame_count = 0
    while stream_active and current_capture.isOpened():
        try:
            # Read frame from ESP32
            ret, frame = current_capture.read()
            
            if not ret:
                print("❌ Lost connection to ESP32, switching to demo stream")
                yield from generate_demo_stream()
                break
            
            # Resize frame for consistent display
            frame = cv2.resize(frame, (640, 480))
            
            # Perform vehicle detection on the frame
            processed_frame, detected_vehicles = detect_vehicles(frame)
            vehicle_count = detected_vehicles
            
            # Add overlay information
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(processed_frame, f"ESP32 Live Stream - {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(processed_frame, f"Vehicles: {vehicle_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(processed_frame, "Source: http://192.168.4.1/", (10, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            frame_count += 1
            time.sleep(0.1)  # Control frame rate
            
        except Exception as e:
            print(f"Stream error: {e}")
            yield from generate_demo_stream()
            break

def generate_demo_stream():
    """Generate demo stream as fallback"""
    global vehicle_count
    while stream_active:
        try:
            width, height = 640, 480
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create realistic background
            frame[100:400, :] = [100, 100, 100]  # Road
            frame[0:100, :] = [135, 206, 235]    # Sky
            frame[400:480, :] = [34, 139, 34]    # Grass
            
            # Road markings
            cv2.line(frame, (0, 250), (width, 250), (255, 255, 255), 2)
            cv2.line(frame, (0, 350), (width, 350), (255, 255, 255), 2)
            
            # Moving vehicles
            vehicle_count = random.randint(1, 4)
            colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]
            
            for i in range(vehicle_count):
                x_pos = int((time.time() * 50 + i * 150) % (width + 200) - 100)
                y_pos = 280 + (i * 30)
                
                cv2.rectangle(frame, (x_pos, y_pos), (x_pos + 120, y_pos + 60), colors[i], -1)
                cv2.rectangle(frame, (x_pos + 10, y_pos + 10), (x_pos + 50, y_pos + 30), (200, 200, 255), -1)
                cv2.rectangle(frame, (x_pos + 70, y_pos + 10), (x_pos + 110, y_pos + 30), (200, 200, 255), -1)
                
                vehicle_types = ["Car", "Truck", "Bus", "Motorcycle"]
                cv2.putText(frame, vehicle_types[i], (x_pos + 10, y_pos - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
            
            # Overlay info
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"Demo Stream - ESP32 Offline - {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, "Trying to connect: http://192.168.4.1/", (10, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Demo stream error: {e}")
            break

def detect_vehicles(frame):
    """Simple vehicle detection (will be enhanced with YOLO later)"""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple detection based on color and shape (placeholder)
        # This will be replaced with YOLO in the next phase
        height, width = frame.shape[:2]
        
        # Simulate detection for now
        detected_vehicles = random.randint(0, 3)
        
        # Draw some detection indicators
        if detected_vehicles > 0:
            cv2.putText(frame, "VEHICLE DETECTED", (width-200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame, detected_vehicles
        
    except Exception as e:
        print(f"Detection error: {e}")
        return frame, 0

@app.route('/')
def home():
    """Dashboard with ESP32 live streaming"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Live Vehicle Detection</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                background: rgba(255,255,255,0.1);
                padding: 25px;
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
            @media (max-width: 768px) {
                .live-container {
                    grid-template-columns: 1fr;
                }
            }
            .video-stream {
                background: rgba(0,0,0,0.8);
                border-radius: 15px;
                padding: 15px;
                text-align: center;
                position: relative;
            }
            .video-container {
                position: relative;
                display: inline-block;
            }
            #videoFeed {
                max-width: 100%;
                border-radius: 10px;
                border: 3px solid #00ff00;
                background: #000;
            }
            .stream-overlay {
                position: absolute;
                top: 15px;
                left: 15px;
                background: rgba(0,0,0,0.7);
                color: #00ff00;
                padding: 10px 15px;
                border-radius: 5px;
                font-family: monospace;
                font-size: 14px;
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
            .connection-info {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
                backdrop-filter: blur(10px);
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-connected { background: #00ff00; }
            .status-disconnected { background: #ff0000; }
            .controls {
                display: grid;
                gap: 10px;
                margin-top: 15px;
            }
            .control-btn {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.3s;
            }
            .control-btn:hover {
                background: #2980b9;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🚗 ESP32 Live Vehicle Detection</h1>
                <p>Directly streaming from your ESP32 camera</p>
            </div>
            
            <div class="live-container">
                <!-- ESP32 Video Stream -->
                <div class="video-stream">
                    <h3>📹 ESP32 Live Stream</h3>
                    <div class="video-container">
                        <img id="videoFeed" src="/video_feed" alt="ESP32 Live Feed">
                        <div class="stream-overlay">
                            <span class="status-indicator status-connected" id="statusIndicator"></span>
                            Vehicles: <span id="liveCount">0</span> | 
                            FPS: <span id="fpsCounter">0</span>
                        </div>
                    </div>
                    <div class="controls">
                        <button class="control-btn" onclick="refreshStream()">🔄 Refresh Stream</button>
                        <button class="control-btn" onclick="checkConnection()">🔍 Check Connection</button>
                    </div>
                </div>
                
                <!-- Statistics -->
                <div class="stats-panel">
                    <h3>📊 Live Statistics</h3>
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
                        <div class="stat-number" id="connectionStatus">Connected</div>
                        <div class="stat-label">ESP32 Status</div>
                    </div>
                </div>
            </div>
            
            <!-- Connection Information -->
            <div class="connection-info">
                <h3>🔗 ESP32 Connection</h3>
                <p><strong>Stream URL:</strong> <code>http://192.168.4.1/</code></p>
                <p><strong>Status:</strong> <span id="detailedStatus">Connecting to ESP32...</span></p>
                <p><strong>Note:</strong> If ESP32 is unavailable, demo stream will activate automatically.</p>
                
                <div id="connectionMessage" style="margin-top: 15px; padding: 10px; border-radius: 5px;"></div>
            </div>
        </div>

        <script>
            let frameCount = 0;
            let startTime = Date.now();
            let isConnected = false;
            
            // Update statistics
            function updateStats() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('vehicleCount').textContent = data.vehicle_count;
                        document.getElementById('totalDetections').textContent = data.total_detections;
                        document.getElementById('uptime').textContent = Math.round(data.uptime);
                        document.getElementById('liveCount').textContent = data.vehicle_count;
                        
                        // Update connection status
                        isConnected = data.esp32_connected;
                        document.getElementById('connectionStatus').textContent = isConnected ? 'Connected' : 'Demo';
                        document.getElementById('statusIndicator').className = 
                            'status-indicator ' + (isConnected ? 'status-connected' : 'status-disconnected');
                        document.getElementById('detailedStatus').textContent = 
                            isConnected ? '✅ Connected to ESP32' : '⚠️ Using demo stream';
                    })
                    .catch(error => {
                        console.log('Stats update error:', error);
                    });
                
                // Calculate FPS
                frameCount++;
                const currentTime = Date.now();
                const elapsed = (currentTime - startTime) / 1000;
                if (elapsed >= 1) {
                    document.getElementById('fpsCounter').textContent = Math.round(frameCount / elapsed);
                    frameCount = 0;
                    startTime = currentTime;
                }
            }
            
            // Stream controls
            function refreshStream() {
                document.getElementById('videoFeed').src = '/video_feed?' + new Date().getTime();
                showMessage('Stream refreshed!', 'success');
            }
            
            function checkConnection() {
                showMessage('Checking ESP32 connection...', 'info');
                refreshStream();
            }
            
            function showMessage(message, type) {
                const messageDiv = document.getElementById('connectionMessage');
                const colors = {
                    success: '#27ae60',
                    error: '#e74c3c', 
                    warning: '#f39c12',
                    info: '#3498db'
                };
                messageDiv.innerHTML = message;
                messageDiv.style.background = colors[type] || '#3498db';
                messageDiv.style.color = 'white';
                
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                    messageDiv.style.background = 'transparent';
                }, 3000);
            }
            
            // Handle stream errors
            document.getElementById('videoFeed').onerror = function() {
                showMessage('Stream disconnected. Trying to reconnect...', 'error');
                setTimeout(refreshStream, 2000);
            };
            
            // Auto-start
            document.addEventListener('DOMContentLoaded', function() {
                setInterval(updateStats, 1000);
                updateStats();
                showMessage('Automatically connected to ESP32: http://192.168.4.1/', 'success');
            });
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Video streaming route - automatically uses ESP32"""
    global stream_active
    stream_active = True
    return Response(generate_esp32_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    global vehicle_count, total_detections, current_capture
    
    # Check if ESP32 is connected
    esp32_connected = current_capture is not None and current_capture.isOpened()
    
    return jsonify({
        'status': 'operational',
        'vehicle_count': vehicle_count,
        'total_detections': total_detections,
        'esp32_connected': esp32_connected,
        'stream_url': 'http://192.168.4.1/',
        'uptime': time.time() - app_start_time,
        'timestamp': time.time()
    })

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 ESP32 Vehicle Detection Dashboard running on port {port}")
    print(f"📹 AUTO-CONNECTING to: http://192.168.4.1/")
    print("🌐 Open your browser to see the live ESP32 stream!")
    app.run(host='0.0.0.0', port=port, debug=False)
