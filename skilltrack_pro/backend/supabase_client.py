import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")

# Create Supabase client with service role key for server side admin operations
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def register_user(email: str, password: str, username: str, role: str):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": role,
                    "username": username
                }
            }
        })

        # Check for error in registration
        if response.error:
            error_msg = getattr(response.error, 'message', str(response.error))
            return {'error': error_msg}

        # Access user from response data
        user = getattr(response.data, 'user', None)
        if user is None:
            # Likely email confirmation is enabled: no user data until confirmed
            return {'error': 'Registration failed: no user data returned'}

        user_id = user.id

        # Insert user profile in 'profiles' table
        profile_response = supabase.table('profiles').insert({
            'id': user_id,
            'username': username,
            'role': role,
            'email': email
        }).execute()

        # Check for error on profile insert
        if profile_response.error:
            err_msg = getattr(profile_response.error, 'message', str(profile_response.error))
            return {'error': err_msg}

        return {'message': 'User registered successfully', 'user': user}

    except Exception as e:
        return {'error': str(e)}


def get_all_trainers():
    try:
        # List all users with pagination: adjust page and per_page as needed
        response = supabase.auth.admin.list_users(
            page=1,
            per_page=1000  # max 1000 per page
        )

        if response.error:
            raise Exception(response.error.message)

        # Filter users with user_metadata.role == 'trainer'
        trainers = [
            user for user in response.data['users']
            if user.get('user_metadata', {}).get('role') == 'trainer'
        ]

        return trainers

    except Exception as e:
        print(f"Error fetching trainers from Supabase: {e}")
        return []
