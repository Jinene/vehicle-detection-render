# Vehicle Detection API 🚗

Real-time vehicle detection using YOLOv8 and Flask, deployed on Render.com free tier.

## Features
- Vehicle detection from images
- RESTful API endpoints
- ESP32 camera integration
- Free cloud deployment

## API Endpoints

### GET `/`
Web interface with documentation

### GET `/api/status`
Get system status and statistics

### POST `/api/detect`
Detect vehicles in uploaded image

### GET `/health`
Health check endpoint

## ESP32 Integration

Send POST requests with images to `/api/detect`:

```cpp
// ESP32 example
HTTPClient http;
http.begin("https://your-app.onrender.com/api/detect");
http.addHeader("Content-Type", "image/jpeg");
int httpResponseCode = http.POST(image_data);
