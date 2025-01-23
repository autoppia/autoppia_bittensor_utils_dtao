import requests
import time


def test_serve(base_url="http://127.0.0.1:8000", netuid=1, wait_timeout=60):
    """
    Tests whether DCA invests a small amount of TAO into netuid=1,
    ensuring final holdings > initial.
    Assumes serve.py is already running, and the DCA script invests 
    into netuid=1 when POST /dca is called.
    """

    # 1) Wait for the server to be up
    print("[test.py] Waiting 3 seconds to ensure server is running...")
    time.sleep(3)

    # 2) Read initial info
    print("[test.py] Getting /info to capture initial stake.")
    r = requests.get(f"{base_url}/info")
    if r.status_code != 200:
        print("[test.py] ERROR: /info returned", r.status_code, r.text)
        return

    data = r.json()
    # The info endpoint returns something like:
    # {
    #   "strategy_running": False,
    #   "holdings": {
    #       "1": {"initial_tao": 10.0, "current_tao": 10.0, "profit_percent": 0.0},
    #       ...
    #   }
    # }
    holdings = data.get("holdings", {})
    netuid_str = str(netuid)
    if netuid_str not in holdings:
        print(f"[test.py] ERROR: netuid={netuid} not found in /info holdings. Check state.json setup.")
        return

    initial_tao = holdings[netuid_str]["current_tao"]
    print(f"[test.py] Initial stake for netuid={netuid}: {initial_tao} TAO")

    # 3) Start DCA
    print("[test.py] Calling /dca to start the strategy.")
    r = requests.post(f"{base_url}/dca")
    if r.status_code != 200:
        print("[test.py] ERROR: /dca returned", r.status_code, r.text)
        return
    print("[test.py] /dca response:", r.json())

    # 4) Poll /info until stake increases or timeout
    print(f"[test.py] Waiting up to {wait_timeout} seconds for stake to increase...")
    start_time = time.time()
    final_tao = initial_tao
    while time.time() - start_time < wait_timeout:
        time.sleep(5)  # poll every 5s
        r = requests.get(f"{base_url}/info")
        if r.status_code != 200:
            print("[test.py] WARNING: /info returned", r.status_code, r.text)
            continue

        data = r.json()
        holdings = data.get("holdings", {})
        if netuid_str not in holdings:
            continue

        final_tao = holdings[netuid_str]["current_tao"]
        print(f"[test.py] polled /info => netuid={netuid}, current_tao={final_tao}")

        if final_tao > initial_tao:
            print("[test.py] Detected an increase in stake. DCA presumably succeeded.")
            break

    # 5) Validate final stake is indeed higher
    if final_tao <= initial_tao:
        print("[test.py] ERROR: final stake did not exceed initial stake. DCA may not have completed.")
    else:
        print(f"[test.py] SUCCESS: final stake {final_tao} > initial stake {initial_tao}")
        # 6) We can compute or retrieve an investment return from profit_percent:
        profit_percent = holdings[netuid_str].get("profit_percent", 0.0)
        print(f"[test.py] Profit Percentage (from /info) = {profit_percent:.2f}%")

    # 7) Stop DCA
    print("[test.py] Stopping strategy via /stop...")
    r = requests.post(f"{base_url}/stop")
    print("[test.py] /stop response:", r.status_code, r.json())


if __name__ == "__main__":
    # For example, if your DCA invests in netuid=1, call:
    test_serve(base_url="http://127.0.0.1:8000", netuid=1, wait_timeout=60)
