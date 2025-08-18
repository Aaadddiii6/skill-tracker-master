from supabase import create_client
import os
from dotenv import load_dotenv

# Load .env from the same folder as this script
load_dotenv()

# Read values
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Debug print to confirm they’re loaded
print("✅ SUPABASE_URL:", SUPABASE_URL)
print("✅ Service Role Key (partial):", SUPABASE_SERVICE_ROLE_KEY[:6] + "...")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. Check your .env file.")

# Create Supabase client with service role key
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Replace with **real** UUIDs from Supabase dashboard
users = [
    {"id": "97f9cbcf-7cf5-41d4-9e55-05e78806e27d", "role": "admin", "email_verified": True},
    {"id": "70d7acd9-f127-4485-9dab-6c204bad3134", "role": "trainer", "email_verified": True},
    {"id": "04cbfe37-ab4c-447d-a653-d6f9d7499621", "role": "observer", "email_verified": True}
]

# Loop and update roles
for user in users:
    print(f"🔄 Updating {user['id']} to role '{user['role']}'")
    resp = supabase.auth.admin.update_user_by_id(
        user["id"],
        {
            "user_metadata": {
                "role": user["role"],
                "email_verified": user["email_verified"]
            }
        }
    )
    print("   ➡ Response:", resp)

print("🎯 Done! Roles updated successfully.")
