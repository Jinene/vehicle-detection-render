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
stream_active = False
current_stream_url = ""

def generate_demo_stream():
    """Generate a demo video stream with synthetic vehicles"""
    while stream_active:
        try:
            # Create a synthetic frame (640x480)
            width, height = 640, 480
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Create a realistic-looking background (road-like)
            frame[100:400, :] = [100, 100, 100]  # Road color
            frame[0:100, :] = [135, 206, 235]    # Sky color
            frame[400:480, :] = [34, 139, 34]    # Grass color
            
            # Add road markings
            cv2.line(frame, (0, 250), (width, 250), (255, 255, 255), 2)
            cv2.line(frame, (0, 350), (width, 350), (255, 255, 255), 2)
            
            # Add moving vehicles (they'll move across the screen)
            global vehicle_count
            vehicle_count = random.randint(1, 4)
            
            # Draw vehicles as colored rectangles
            colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]  # Red, Green, Blue, Yellow
            
            for i in range(vehicle_count):
                # Make vehicles move
                x_pos = int((time.time() * 50 + i * 150) % (width + 200) - 100)
                y_pos = 280 + (i * 30)
                
                # Draw vehicle body
                cv2.rectangle(frame, (x_pos, y_pos), (x_pos + 120, y_pos + 60), colors[i], -1)
                
                # Draw vehicle windows
                cv2.rectangle(frame, (x_pos + 10, y_pos + 10), (x_pos + 50, y_pos + 30), (200, 200, 255), -1)
                cv2.rectangle(frame, (x_pos + 70, y_pos + 10), (x_pos + 110, y_pos + 30), (200, 200, 255), -1)
                
                # Add vehicle label
                vehicle_types = ["Car", "Truck", "Bus", "Motorcycle"]
                cv2.putText(frame, vehicle_types[i], (x_pos + 10, y_pos - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
            
            # Add timestamp and info
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, f"Live Stream - {timestamp}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "DEMO STREAM - Add your ESP32 URL below", (10, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control frame rate (10 FPS)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Stream error: {e}")
            break

@app.route('/')
def home():
    """Dashboard with live video streaming"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Vehicle Detection Dashboard</title>
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
            .controls {
                display: grid;
                gap: 10px;
                margin-top: 20px;
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
            .control-btn.start { background: #27ae60; }
            .control-btn.start:hover { background: #219a52; }
            .control-btn.stop { background: #e74c3c; }
            .control-btn.stop:hover { background: #c0392b; }
            .stream-config {
                background: rgba(255,255,255,0.1);
                padding: 25px;
                border-radius: 15px;
                margin-top: 20px;
                backdrop-filter: blur(10px);
            }
            .input-group {
                display: flex;
                gap: 10px;
                margin: 15px 0;
            }
            input[type="text"] {
                flex: 1;
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-size: 1em;
            }
            .examples {
                background: rgba(255,255,255,0.05);
                padding: 15px;
                border-radius: 8px;
                margin-top: 15px;
            }
            .examples h4 {
                margin-bottom: 10px;
                color: #3498db;
            }
            .examples ul {
                list-style: none;
                padding-left: 0;
            }
            .examples li {
                padding: 5px 0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-live { background: #00ff00; }
            .status-offline { background: #ff0000; }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="header">
                <h1>🚗 Live Vehicle Detection Dashboard</h1>
                <p>Real-time video streaming with vehicle detection</p>
            </div>
            
            <div class="live-container">
                <!-- Video Stream Section -->
                <div class="video-stream">
                    <h3>📹 Live Video Stream</h3>
                    <div class="video-container">
                        <img id="videoFeed" src="/video_feed" alt="Live Video Feed">
                        <div class="stream-overlay">
                            <span class="status-indicator status-live"></span>
                            Vehicles: <span id="liveCount">0</span> | 
                            FPS: <span id="fpsCounter">0</span>
                        </div>
                    </div>
                    <div class="controls" style="margin-top: 15px;">
                        <button class="control-btn start" onclick="startStream()">▶️ Start Stream</button>
                        <button class="control-btn stop" onclick="stopStream()">⏹️ Stop Stream</button>
                        <button class="control-btn" onclick="refreshStream()">🔄 Refresh Stream</button>
                    </div>
                </div>
                
                <!-- Statistics Panel -->
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
                        <div class="stat-number" id="streamStatus">Live</div>
                        <div class="stat-label">Stream Status</div>
                    </div>
                </div>
            </div>
            
            <!-- Stream Configuration -->
            <div class="stream-config">
                <h3>🔧 Stream Configuration</h3>
                <p>Current Stream: <strong id="currentStream">Demo Stream (Synthetic)</strong></p>
                
                <div class="input-group">
                    <input type="text" id="streamUrl" 
                           placeholder="Enter ESP32 stream URL: http://192.168.1.100:81/stream">
                    <button class="control-btn" onclick="changeStream()">Change Stream</button>
                </div>
                
                <div class="examples">
                    <h4>📹 Example Stream URLs:</h4>
                    <ul>
                        <li><strong>ESP32 Camera:</strong> http://192.168.1.100:81/stream</li>
                        <li><strong>RTSP Camera:</strong> rtsp://username:password@ip:port/stream</li>
                        <li><strong>Webcam:</strong> 0 (local testing only)</li>
                        <li><strong>Video File:</strong> traffic.mp4</li>
                    </ul>
                </div>
                
                <div id="streamMessage" style="margin-top: 15px; padding: 10px; border-radius: 5px;"></div>
            </div>
        </div>

        <script>
            let frameCount = 0;
            let startTime = Date.now();
            let streamActive = true;
            
            // Update statistics in real-time
            function updateStats() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('vehicleCount').textContent = data.vehicle_count;
                        document.getElementById('totalDetections').textContent = data.total_detections;
                        document.getElementById('uptime').textContent = Math.round(data.uptime);
                        document.getElementById('liveCount').textContent = data.vehicle_count;
                        document.getElementById('streamStatus').textContent = streamActive ? 'Live' : 'Stopped';
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
            
            // Stream control functions
            function startStream() {
                streamActive = true;
                document.getElementById('videoFeed').src = '/video_feed?' + new Date().getTime();
                showMessage('Stream started successfully!', 'success');
            }
            
            function stopStream() {
                streamActive = false;
                document.getElementById('videoFeed').src = '';
                showMessage('Stream stopped.', 'warning');
            }
            
            function refreshStream() {
                document.getElementById('videoFeed').src = '/video_feed?' + new Date().getTime();
                showMessage('Stream refreshed!', 'success');
            }
            
            function changeStream() {
                const url = document.getElementById('streamUrl').value;
                if (url) {
                    fetch('/api/set_stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({stream_url: url})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            document.getElementById('currentStream').textContent = url;
                            showMessage('Stream URL updated! Refresh the stream.', 'success');
                        } else {
                            showMessage('Error: ' + data.message, 'error');
                        }
                    })
                    .catch(error => {
                        showMessage('Connection error: ' + error, 'error');
                    });
                } else {
                    showMessage('Please enter a stream URL', 'error');
                }
            }
            
            function showMessage(message, type) {
                const messageDiv = document.getElementById('streamMessage');
                const colors = {
                    success: '#27ae60',
                    error: '#e74c3c', 
                    warning: '#f39c12'
                };
                messageDiv.innerHTML = message;
                messageDiv.style.background = colors[type] || '#3498db';
                messageDiv.style.color = 'white';
                
                setTimeout(() => {
                    messageDiv.innerHTML = '';
                    messageDiv.style.background = 'transparent';
                }, 5000);
            }
            
            // Handle video stream errors
            document.getElementById('videoFeed').onerror = function() {
                showMessage('Video stream disconnected. Please check the stream source.', 'error');
            };
            
            // Auto-start stream and update stats
            document.addEventListener('DOMContentLoaded', function() {
                startStream();
                setInterval(updateStats, 1000);
                updateStats();
            });
        </script>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    global stream_active
    stream_active = True
    return Response(generate_demo_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    global vehicle_count, total_detections, stream_active
    return jsonify({
        'status': 'operational',
        'vehicle_count': vehicle_count,
        'total_detections': total_detections,
        'stream_active': stream_active,
        'uptime': time.time() - app_start_time,
        'timestamp': time.time()
    })

@app.route('/api/start', methods=['POST'])
def start_stream():
    """Start video stream"""
    global stream_active
    stream_active = True
    return jsonify({
        'success': True,
        'message': 'Video stream started',
        'timestamp': time.time()
    })

@app.route('/api/stop', methods=['POST'])
def stop_stream():
    """Stop video stream"""
    global stream_active
    stream_active = False
    return jsonify({
        'success': True,
        'message': 'Video stream stopped',
        'timestamp': time.time()
    })

@app.route('/api/set_stream', methods=['POST'])
def set_stream():
    """Change video stream source"""
    data = request.get_json()
    stream_url = data.get('stream_url', '')
    
    # In a real implementation, you would update the video capture source here
    # For now, we'll just acknowledge the request
    
    return jsonify({
        'success': True,
        'message': f'Stream source updated to: {stream_url}',
        'stream_url': stream_url
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
        'timestamp': time.time()
    })

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Live Vehicle Detection Dashboard running on port {port}")
    print("📹 Video streaming ENABLED")
    print("🌐 Open your browser to see the live stream!")
    app.run(host='0.0.0.0', port=port, debug=False)
