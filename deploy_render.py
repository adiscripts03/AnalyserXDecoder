import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

def deploy(api_key: str = None):
    root_dir = Path(__file__).resolve().parent
    env_file = root_dir / ".env"
    env_dict = {}

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_dict[k.strip()] = v.strip().strip("\"'")

    token = api_key or os.getenv("RENDER_API_KEY") or env_dict.get("RENDER_API_KEY")
    if not token:
        print("❌ Error: RENDER_API_KEY not found in environment or .env file.")
        return False
    owner_id = "tea-db2ije59fdbs739hsbf0"

    env_vars = [
        {"key": "PYTHON_VERSION", "value": "3.12.0"},
        {"key": "LLM_PROVIDER", "value": "gemini"},
    ]

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k not in ["RENDER_API_KEY"]:
                        env_vars.append({"key": k, "value": v})

    payload = {
        "type": "web_service",
        "name": "analyser-x-decoder",
        "ownerId": owner_id,
        "repo": "https://github.com/adiscripts03/AnalyserXDecoder",
        "branch": "main",
        "autoDeployTrigger": "commit",
        "serviceDetails": {
            "runtime": "python",
            "plan": "free",
            "region": "oregon",
            "healthCheckPath": "/health",
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python main.py",
            },
        },
        "envVars": env_vars,
    }

    req = urllib.request.Request(
        "https://api.render.com/v1/services",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("🚀 Service created and deployment initiated successfully!")
            service = data.get("service", {})
            print(f"Service Name: {service.get('name')}")
            print(f"Service ID:   {service.get('id')}")
            print(f"Service URL:  {service.get('serviceDetails', {}).get('url')}")
            deploy_info = data.get("deploy", {})
            print(f"Deploy ID:    {deploy_info.get('id')}")
            print(f"Deploy Status:{deploy_info.get('status')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Render API returned HTTP {e.code}:")
        print(error_body)
        return False

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else None
    deploy(key)
