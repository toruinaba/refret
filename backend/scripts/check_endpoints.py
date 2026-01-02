
import requests
import json

BASE_URL = "http://localhost:8000"

def check_endpoints():
    print("Checking /lessons...")
    try:
        r = requests.get(f"{BASE_URL}/api/lessons")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Items: {len(data.get('items', []))}")
        else:
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

    print("\nChecking /licks...")
    try:
        r = requests.get(f"{BASE_URL}/api/licks")
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Items: {len(data.get('items', []))}")
        else:
            print(r.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_endpoints()
