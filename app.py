from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase_client import supabase
import jwt

app = Flask(__name__)
CORS(app) # Mobile app se request allow karne ke liye

# --- Middleware: Verify User Token ---
def verify_token(token):
    try:
        # Supabase JWT verify karne ka simple tarika
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub') # Returns User ID
    except Exception as e:
        return None

# --- 1. Health Check API ---
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "Super App Backend is running!"}), 200

# --- 2. Sync Profile (Signup ke baad call hoga) ---
@app.route('/api/auth/sync-profile', methods=['POST'])
def sync_profile():
    data = request.json
    user_id = data.get('user_id')
    full_name = data.get('full_name')
    phone = data.get('phone')

    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    # Profile insert karein
    try:
        supabase.table('profiles').upsert({
            "id": user_id,
            "full_name": full_name,
            "phone": phone,
            "role": "customer"
        }).execute()
        
        # Wallet create karein naye user ke liye
        supabase.table('wallets').upsert({
            "user_id": user_id,
            "balance": 0.00
        }).execute()

        return jsonify({"message": "Profile and Wallet created!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 3. Add Address API ---
@app.route('/api/addresses', methods=['POST'])
def add_address():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = verify_token(token.replace("Bearer ", ""))
    if not user_id:
        return jsonify({"error": "Invalid Token"}), 401

    data = request.json
    
    try:
        response = supabase.table('addresses').insert({
            "user_id": user_id,
            "label": data.get('label'),
            "address_line": data.get('address_line'),
            "city": data.get('city'),
            "pincode": data.get('pincode'),
            "is_default": data.get('is_default', False)
        }).execute()
        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 4. Get My Wallet API ---
@app.route('/api/wallet', methods=['GET'])
def get_wallet():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = verify_token(token.replace("Bearer ", ""))
    if not user_id:
        return jsonify({"error": "Invalid Token"}), 401

    try:
        response = supabase.table('wallets').select('*').eq('user_id', user_id).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
