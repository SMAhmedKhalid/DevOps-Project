from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration
LLM_API_URL = "http://51.21.223.41:8000"
RATE_LIMIT_REQUESTS = 10  # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

# In-memory storage for rate limiting (use Redis in production)
rate_limit_store = defaultdict(list)
rate_limit_lock = threading.Lock()

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    return EMAIL_REGEX.match(email) is not None

def get_client_identifier(request):
    """Get client identifier (IP or session_id)"""
    # Try to get real IP if behind proxy/load balancer
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip:
        ip = ip.split(',')[0].strip()
    session_id = request.json.get('session_id', '')
    return f"{ip}:{session_id}"

def check_rate_limit(identifier):
    """Check if request is within rate limit"""
    with rate_limit_lock:
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        # Clean old entries
        rate_limit_store[identifier] = [
            timestamp for timestamp in rate_limit_store[identifier]
            if timestamp > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(rate_limit_store[identifier]) >= RATE_LIMIT_REQUESTS:
            return False
        
        # Add current request
        rate_limit_store[identifier].append(current_time)
        return True

def cleanup_rate_limit_store():
    """Periodic cleanup of rate limit store"""
    while True:
        time.sleep(300)  # Run every 5 minutes
        with rate_limit_lock:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(seconds=RATE_LIMIT_WINDOW * 2)
            
            keys_to_delete = []
            for key, timestamps in rate_limit_store.items():
                rate_limit_store[key] = [
                    ts for ts in timestamps if ts > cutoff_time
                ]
                if not rate_limit_store[key]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del rate_limit_store[key]

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_rate_limit_store, daemon=True)
cleanup_thread.start()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancer"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid JSON payload'
            }), 400
        
        # Extract parameters
        session_id = data.get('session_id')
        query = data.get('query')
        email = data.get('email')
        
        # Validate required fields
        if not session_id:
            return jsonify({
                'error': 'session_id is required'
            }), 400
        
        if not query or not isinstance(query, str) or not query.strip():
            return jsonify({
                'error': 'query is required and must be a non-empty string'
            }), 400
        
        if not email:
            return jsonify({
                'error': 'email is required'
            }), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'error': 'Invalid email format'
            }), 400
        
        # Check rate limit
        client_id = get_client_identifier(request)
        if not check_rate_limit(client_id):
            return jsonify({
                'error': 'Rate limit exceeded. Please try again later.',
                'retry_after': RATE_LIMIT_WINDOW
            }), 429
        
        # Prepare payload for LLM API
        llm_payload = {
            'session_id': session_id,
            'query': query.strip(),
            'email': email
        }
        
        # Call LLM API
        try:
            llm_response = requests.post(
                f"{LLM_API_URL}/chat",  # Adjust endpoint as needed
                json=llm_payload,
                timeout=30  # 30 second timeout
            )
            
            # Check if LLM API call was successful
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                
                # Return response to frontend
                return jsonify({
                    'session_id': session_id,
                    'response': llm_data.get('response', ''),
                    'timestamp': datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    'error': 'LLM API error',
                    'details': llm_response.text
                }), 502
                
        except requests.exceptions.Timeout:
            return jsonify({
                'error': 'LLM API request timed out'
            }), 504
        
        except requests.exceptions.ConnectionError:
            return jsonify({
                'error': 'Failed to connect to LLM API'
            }), 503
        
        except Exception as e:
            return jsonify({
                'error': 'Error calling LLM API',
                'details': str(e)
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Optional: Get session information"""
    # Implement session retrieval logic if needed
    return jsonify({
        'session_id': session_id,
        'message': 'Session endpoint - implement as needed'
    }), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        'error': 'Method not allowed'
    }), 405

if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=False)
    
    # For production, use gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
