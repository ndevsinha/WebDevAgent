import sys
import os

settings_path = 'math_visualizer/core_backend/core_backend/settings.py'

with open(settings_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip() == "INSTALLED_APPS = [":
        new_lines.append("INSTALLED_APPS = [\n")
        new_lines.append("    'corsheaders',\n")
        new_lines.append("    'api',\n")
    elif line.strip() == "MIDDLEWARE = [":
        new_lines.append("MIDDLEWARE = [\n")
        new_lines.append("    'corsheaders.middleware.CorsMiddleware',\n")
    else:
        new_lines.append(line)

new_content = "".join(new_lines)

if "CORS_ALLOW_ALL_ORIGINS" not in new_content:
    new_content += "\nCORS_ALLOW_ALL_ORIGINS = True\n"

with open(settings_path, 'w') as f:
    f.write(new_content)

print("CORS added successfully.")
