#!/usr/bin/env python3
"""
Sync local SD card files to ESP8266 via HTTP upload endpoint
Usage: python sync_sd_card.py <esp_ip> [--exclude pattern1,pattern2,...]
Example: python sync_sd_card.py 192.168.103.8
"""

import os
import sys
import requests
from pathlib import Path


def sync_sd_card(esp_ip, exclude_patterns=None):
    """Sync all files from extras/SDCard/ to ESP8266"""

    sd_card_dir = Path("extras/SDCard")

    if not sd_card_dir.exists():
        print(f"Error: {sd_card_dir} directory not found")
        sys.exit(1)

    exclude_patterns = exclude_patterns or []
    base_url = f"http://{esp_ip}/upload"

    # Collect all files recursively
    files_to_upload = []
    for file_path in sd_card_dir.rglob("*"):
        if file_path.is_file():
            # Calculate relative path from sd_card_dir
            rel_path = file_path.relative_to(sd_card_dir)

            # Check exclusions
            skip = False
            for pattern in exclude_patterns:
                if pattern.lower() in str(rel_path).lower():
                    skip = True
                    break

            if not skip:
                files_to_upload.append((file_path, str(rel_path).replace("\\", "/")))

    if not files_to_upload:
        print("No files to upload")
        return

    print(f"Found {len(files_to_upload)} files to upload to {esp_ip}")
    print("-" * 60)

    successful = 0
    failed = 0

    for local_path, remote_path in sorted(files_to_upload):
        try:
            with open(local_path, "rb") as f:
                files = {"file": f}
                data = {"path": remote_path}

                response = requests.post(base_url, files=files, data=data, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        print(f"✓ {remote_path}")
                        successful += 1
                    else:
                        print(
                            f"✗ {remote_path}: {result.get('error', 'Unknown error')}"
                        )
                        failed += 1
                else:
                    print(f"✗ {remote_path}: HTTP {response.status_code}")
                    failed += 1

        except Exception as e:
            print(f"✗ {remote_path}: {str(e)}")
            failed += 1

    print("-" * 60)
    print(f"Sync complete: {successful} uploaded, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python sync_sd_card.py <esp_ip> [--exclude pattern1,pattern2,...]"
        )
        print("Example: python sync_sd_card.py 192.168.103.8")
        sys.exit(1)

    esp_ip = sys.argv[1]
    exclude = []

    if len(sys.argv) > 2 and sys.argv[2] == "--exclude":
        exclude = sys.argv[3].split(",")

    sync_sd_card(esp_ip, exclude)
