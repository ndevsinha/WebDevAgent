import sys

with open('math_visualizer/core_backend/core_backend/settings.py', 'r') as f:
    text = f.read()

has_cors = 'corsheaders' in text
has_allow = 'CORS_ALLOW_ALL_ORIGINS' in text

print(f"CORS added: {has_cors}")
print(f"ALLOW all: {has_allow}")
