#!/usr/bin/env python3
import os
import json
import subprocess
import bittensor

from fastapi import FastAPI
from typing import Dict, Any
import uvicorn

from src.utils.get_my_wallet import get_my_wallet
from src.shared.dtao_helper import DTAOHelper

app = FastAPI()

STATE_FILE = "data/state.json"
DCA_SCRIPT = "main.py"
PM2_APP_NAME = "data/dca_script"


@app.on_event("startup")
async def on_startup():
    print("[serve.py] on_startup event triggered.")
    if not os.path.exists(STATE_FILE):
        print(f"[serve.py] {STATE_FILE} not found. Creating default file.")
        initial_data = {
            "initial_alpha": {},
            "strategy_running": False
        }
        with open(STATE_FILE, "w") as f:
            json.dump(initial_data, f)
    else:
        print(f"[serve.py] Found existing {STATE_FILE}.")


@app.get("/info")
async def get_info() -> Dict[str, Any]:
    """
    Returns current stake and profit info for each netuid 
    where the user has stake (directly retrieved from get_stake_info_for_coldkey).
    Automatically updates state.json with newly discovered netuids.
    """
    print("[serve.py] GET /info")

    # Ensure state.json exists
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"initial_alpha": {}, "strategy_running": False}, f)

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    # Prepare subtensor and wallet
    subtensor = await bittensor.async_subtensor(network='test')
    wallet = get_my_wallet()

    # 1) Get all StakeInfo for this coldkey
    stake_info_list = await subtensor.get_stake_info_for_coldkey(
        coldkey_ss58=wallet.coldkeypub.ss58_address
    )
    # stake_info_list: list[StakeInfo]
    # Each StakeInfo has: hotkey_ss58, coldkey_ss58, netuid, stake, locked, emission, drain, is_registered

    # 2) Sum stake by netuid (the user might have multiple hotkeys for one netuid)
    from collections import defaultdict
    netuid_stakes = defaultdict(float)

    for stake_info in stake_info_list:
        netuid = stake_info.netuid
        # stake_info.stake is a bittensor.Balance, convert to float
        netuid_stakes[netuid] += float(stake_info.stake.tao)

    # 3) Merge newly discovered netuids into state["initial_alpha"]
    for netuid, current_tao in netuid_stakes.items():
        netuid_str = str(netuid)
        if netuid_str not in state["initial_alpha"]:
            print(f"[serve.py] Discovered netuid={netuid} with stake={current_tao}, not in state.json.")
            # Decide how to treat the initial stake:
            # Option A: set to 0 => only track new additions as profit
            # Option B: set to current_tao => treat existing stake as initial reference
            state["initial_alpha"][netuid_str] = 0.0

    # 4) Build holdings_info for all netuids in state["initial_alpha"]
    holdings_info = {}
    for netuid_str, initial_tao in state["initial_alpha"].items():
        netuid = int(netuid_str)
        # Get the user's total stake for this netuid (0 if no stake in netuid_stakes)
        current_tao = netuid_stakes.get(netuid, 0.0)

        profit_percent = 0.0
        if initial_tao > 0:
            profit_percent = ((current_tao - initial_tao) / initial_tao) * 100

        holdings_info[netuid_str] = {
            "initial_tao": initial_tao,
            "current_tao": current_tao,
            "profit_percent": profit_percent
        }

    # 5) Persist any updates to state.json
    with open(STATE_FILE, "w") as f:
        updated_state = {
            "initial_alpha": state["initial_alpha"],
            "strategy_running": state.get("strategy_running", False)
        }
        json.dump(updated_state, f, indent=2)

    return {
        "strategy_running": state.get("strategy_running", False),
        "holdings": holdings_info
    }


@app.post("/dca")
async def start_dca():
    print("[serve.py] POST /dca called")
    subprocess.run(["pm2", "start", DCA_SCRIPT, "--name", PM2_APP_NAME])
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    state["strategy_running"] = True
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    return {"message": "DCA strategy started via PM2."}


@app.post("/stop")
async def stop_dca():
    print("[serve.py] POST /stop called")
    subprocess.run(["pm2", "stop", PM2_APP_NAME])
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    state["strategy_running"] = False
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    return {"message": "DCA strategy stopped via PM2."}

if __name__ == "__main__":
    print("[serve.py] Starting Uvicorn on 0.0.0.0:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
