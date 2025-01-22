import requests
import time


def test_serve(base_url="http://127.0.0.1:8000"):
    print("[test.py] Waiting a couple seconds to ensure server is up...")
    time.sleep(2)

    try:
        # 1) /info
        print("[test.py] Calling GET /info...")
        r = requests.get(f"{base_url}/info")
        print("GET /info =>", r.status_code, r.json())

        # 2) /dca
        print("[test.py] Calling POST /dca...")
        r = requests.post(f"{base_url}/dca")
        print("POST /dca =>", r.status_code, r.json())

        # Wait a bit for PM2 process to respond
        time.sleep(2)

        # 3) /info again
        print("[test.py] Calling GET /info again...")
        r = requests.get(f"{base_url}/info")
        print("GET /info =>", r.status_code, r.json())

        # 4) /stop
        print("[test.py] Calling POST /stop...")
        r = requests.post(f"{base_url}/stop")
        print("POST /stop =>", r.status_code, r.json())

        # 5) final /info
        print("[test.py] Final GET /info check...")
        r = requests.get(f"{base_url}/info")
        print("GET /info =>", r.status_code, r.json())

    except Exception as e:
        print("[test.py] Error:", e)


if __name__ == "__main__":
    test_serve()
