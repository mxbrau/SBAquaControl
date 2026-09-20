Import("env")
from pathlib import Path

secrets_file = Path(env.subst("$PROJECT_DIR")) / "secrets.ini"

if not secrets_file.exists():
    print(">>> secrets.ini not found — OTA_PASSWORD will be undefined")

else:
    with open(secrets_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";") or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # For the C++ side: -DOTA_PASSWORD=\"value\"
            env.Append(BUILD_FLAGS=[f'-D{key}=\\"{value}\\"'])

            # For the OTA upload side: --auth=value
            if key == "OTA_PASSWORD":
                env.Append(UPLOAD_FLAGS=[f"--auth={value}"])
