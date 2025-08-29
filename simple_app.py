"""
Simple test app for Azure App Service
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Pre-Walkthrough Report Generator API",
        "status": "running",
        "version": "1.0.0"
    })

@app.route('/test')
def test():
    return jsonify({
        "message": "API is working!",
        "timestamp": "2025-07-07T17:50:00Z"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "pre-walkthrough-report-generator"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 