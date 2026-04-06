import os
import subprocess
import sys

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

if not os.path.exists(ENV_FILE):
    print("ERROR: .env file not found.")
    print("Create a file named .env in your my-web-app folder with this content:")
    print("")
    print("  ANTHROPIC_API_KEY=sk-ant-your-key-here")
    print("  SECRET_TOKEN=choose-a-secret-word")
    print("")
    sys.exit(1)

# Load .env into environment
with open(ENV_FILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
            print(f"Loaded: {key.strip()}")

print("")
print("Starting server...")
os.execv(sys.executable, [sys.executable, 'server.py'])
