import cv2
import numpy as np
from flask import Flask, Response, jsonify
import requests
from ultralytics import YOLO
import time
import os

app = Flask(__name__)

# Your Ngrok URL (update this after starting ngrok)
NGROK_STREAM_URL = "https://YOUR_NGROK_ID.ngrok.io/stream"

# Global variables
vehicle_count = 0
total_detections = 0
stream_active = True
ai_model = None

# Initialize AI model
def initialize_ai():
    global ai_model
    try:
        print("🚀 Loading YOLO model on Render...")
        ai_model = YOLO('yolov8n.pt')
        print("✅ AI Model ready on Render!")
    except Exception as e:
        print(f"❌ AI Model failed: {e}")

# Initialize on startup
initialize_ai()

def test_ngrok_connection():
    """Test if ngrok bridge is accessible"""
    try:
        response = requests.get(NGROK_STREAM_URL, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ngrok connection test failed: {e}")
        return False

def generate_cloud_stream():
    """Generate stream from ESP32 via ngrok bridge with AI detection"""
    global vehicle_count, total_detections
    
    print("🌐 Connecting to ESP32 via Ngrok bridge...")
    
    if not test_ngrok_connection():
        yield from generate_offline_stream()
        return
    
    try:
        # Connect to ngrok bridge
        cap = cv2.VideoCapture(NGROK_STREAM_URL)
        
        if not cap.isOpened():
            print("❌ Cannot open ngrok stream")
            yield from generate_offline_stream()
            return
        
        print("✅ Connected to ESP32 via Ngrok!")
        
        frame_count = 0
        while stream_active:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Lost connection to ngrok bridge")
                break
            
            # AI Vehicle Detection on Render
            detected_vehicles = 0
            if ai_model is not None:
                try:
                    results = ai_model(frame, verbose=False, conf=0.5)
                    vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
                    
                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            
                            if class_id in vehicle_classes and confidence > 0.5:
                                detected_vehicles += 1
                                
                                # Draw bounding box
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                
                                # Add AI label
                                label = f"{ai_model.names[class_id]} {confidence:.2f}"
                                cv2.putText(frame, label, (x1, y1-10), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                except Exception as e:
                    print(f"AI detection error: {e}")
            
            vehicle_count = detected_vehicles
            total_detections += detected_vehicles
            frame_count += 1
            
            # Add cloud processing overlay
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"RENDER CLOUD AI - {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Total: {total_detections}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, "Stream: ESP32 → Ngrok → Render Cloud", (10, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Encode and stream
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.1)
        
        cap.release()
        
    except Exception as e:
        print(f"Cloud stream error: {e}")
        yield from generate_offline_stream()

def generate_offline_stream():
    """Offline message when bridge is down"""
    while stream_active:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = [30, 30, 30]
        
        cv2.putText(frame, "CLOUD: ESP32 Bridge Offline", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(frame, "Please check:", (50, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "1. Computer running bridge_server.py", (50, 270), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "2. Ngrok tunnel active", (50, 300), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "3. ESP32 connected to bridge", (50, 330), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(2)

@app.route('/')
def dashboard():
    """Cloud Dashboard with real HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cloud ESP32 Vehicle Detection</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; padding: 20px;
                background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
                color: white;
                min-height: 100vh;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                text-align: center; 
                margin-bottom: 30px;
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .cloud-badge { 
                background: #fdbb2d; 
                color: #000; 
                padding: 5px 15px; 
                border-radius: 20px;
                margin-left: 10px;
            }
            .video-container { 
                text-align: center; 
                background: rgba(0,0,0,0.8);
                padding: 20px;
                border-radius: 15px;
                margin: 20px 0;
            }
            #videoFeed { 
                max-width: 100%; 
                border: 3px solid #00ff00;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            }
            .architecture {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                font-family: monospace;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                backdrop-filter: blur(10px);
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #00ff00;
            }
            .status-online { color: #00ff00; }
            .status-offline { color: #ff0000; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>☁️ Cloud ESP32 Vehicle Detection <span class="cloud-badge">RENDER</span></h1>
                <p>AI processing in cloud, streaming from ESP32 Access Point</p>
            </div>
            
            <div class="architecture">
                <h3>🔗 Architecture: ESP32 → Your Computer → Ngrok → Render Cloud</h3>
                <p>ESP32 WiFi (192.168.4.1) → Bridge → Internet → Cloud AI Processing</p>
            </div>
            
            <div class="video-container">
                <img id="videoFeed" src="/video_feed" alt="Cloud ESP32 Stream">
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
                    <div class="stat-number" id="aiStatus">Active</div>
                    <div>AI Status</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="connection">Checking</div>
                    <div>ESP32 Connection</div>
                </div>
            </div>
            
            <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;">
                <h3>📊 System Information</h3>
                <p><strong>AI Model:</strong> YOLOv8n (Real-time vehicle detection)</p>
                <p><strong>Detection:</strong> Cars, Motorcycles, Buses, Trucks</p>
                <p><strong>Processing:</strong> Render Cloud Server</p>
                <p><strong>Stream Source:</strong> ESP32 Camera via Ngrok</p>
            </div>
        </div>

        <script>
            function updateStats() {
                fetch('/api/status')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('vehicleCount').textContent = data.vehicle_count;
                        document.getElementById('totalDetections').textContent = data.total_detections;
                        document.getElementById('aiStatus').textContent = data.ai_active ? 'Active' : 'Inactive';
                        document.getElementById('aiStatus').className = data.ai_active ? 'status-online' : 'status-offline';
                        document.getElementById('connection').textContent = data.connected ? 'Connected' : 'Offline';
                        document.getElementById('connection').className = data.connected ? 'status-online' : 'status-offline';
                    })
                    .catch(error => {
                        console.log('Error updating stats:', error);
                    });
            }
            
            // Update stats every 2 seconds
            setInterval(updateStats, 2000);
            updateStats();
            
            // Handle stream errors
            document.getElementById('videoFeed').onerror = function() {
                console.log('Video stream error - trying to reconnect...');
                this.src = this.src + '?' + new Date().getTime();
            };
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Cloud video streaming route"""
    global stream_active
    stream_active = True
    return Response(generate_cloud_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    connected = test_ngrok_connection()
    return jsonify({
        'vehicle_count': vehicle_count,
        'total_detections': total_detections,
        'ai_active': ai_model is not None,
        'connected': connected,
        'stream_url': NGROK_STREAM_URL,
        'platform': 'Render Cloud'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'vehicle-detection-cloud'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("☁️ Cloud ESP32 Vehicle Detection Starting...")
    print("🔗 Waiting for Ngrok bridge connection...")
    app.run(host='0.0.0.0', port=port, debug=False)
