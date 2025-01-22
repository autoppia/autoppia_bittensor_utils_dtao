#!/usr/bin/env python3
import os
import json
import subprocess
import bittensor

from fastapi import FastAPI
from typing import Dict, Any
import uvicorn

# If these imports fail, fix your project structure or PYTHONPATH.
from src.utils.get_my_wallet import get_my_wallet
from src.shared.dtao_helper import DTAOHelper
from src.investing.investment_manager import InvestmentManager

app = FastAPI()

STATE_FILE = "state.json"
DCA_SCRIPT = "main.py"
PM2_APP_NAME = "dca_script"


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
    print("[serve.py] GET /info")
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    subtensor = await bittensor.async_subtensor(network='test')
    wallet = get_my_wallet()
    helper = DTAOHelper(subtensor)

    holdings_info = {}
    for netuid_str, initial_tao in state["initial_alpha"].items():
        netuid = int(netuid_str)
        current_stake = await helper.get_stake(
            hotkey_ss58=wallet.hotkey.ss58_address,
            coldkey_ss58=wallet.coldkeypub.ss58_address,
            netuid=netuid
        )
        current_tao = float(current_stake.tao)
        profit_percent = 0.0
        if initial_tao > 0:
            profit_percent = ((current_tao - initial_tao) / initial_tao) * 100

        holdings_info[netuid_str] = {
            "initial_tao": initial_tao,
            "current_tao": current_tao,
            "profit_percent": profit_percent
        }

    return {
        "strategy_running": state["strategy_running"],
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
