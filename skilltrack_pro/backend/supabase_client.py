from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def register_user(email: str, password: str, username: str, role: str):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"role": role, "username": username}}
        })

        # Check for error property safely
        error = getattr(response, 'error', None)
        if error is not None:
            error_msg = getattr(error, 'message', str(error))
            return {'error': error_msg}

        # Check if data and user exist
        data = getattr(response, 'data', None)
        if not data or 'user' not in data:
            return {'error': 'Registration failed: no user data returned'}

        user = data['user']
        user_id = user['id']

        profile_response = supabase.table('profiles').insert({
            'id': user_id,
            'username': username,
            'role': role,
            'email': email
        }).execute()

        if profile_response.error:
            err_msg = getattr(profile_response.error, 'message', str(profile_response.error))
            return {'error': err_msg}

        return {'message': 'User registered successfully', 'user': user}

    except Exception as e:
        return {'error': str(e)}
