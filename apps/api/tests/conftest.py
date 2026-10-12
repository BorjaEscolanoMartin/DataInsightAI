import os

# Settings require SUPABASE_URL; tests must not depend on a developer's .env.
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
