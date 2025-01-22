# DTAO Helper Scripts

A collection of scripts for managing DTAO investments in Bittensor testnet.

## Quick Setup to try DTAO

1. Clone and install Bittensor (rao branch):
```bash
git clone https://github.com/opentensor/bittensor.git
cd bittensor
python3.11 -m venv venv
source venv/bin/activate
git fetch origin rao
git checkout rao
python3 -m pip install -e .
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your wallet password in `.env` (see `.env.template`) and follow instructions

## Available Scripts

### 1. `dca.py`
Gradually stakes TAO into multiple subnets using dollar-cost averaging.
```bash
python -m scripts.dca  # Stakes 0.1 TAO in small increments of 0.005
```

### 2. `dca_sell.py`
Gradually sells alpha holdings from multiple subnets given an array of percentages of alpha targets to sell. 50% will sell 50% of alpha in steps of 'dca_subnet_reduction'. 

```bash
python -m scripts.dca_sell  # Sells specified percentages of alpha in small increments given a weights array. This is not DCA, tao dividends are spent as they come. Better Slipage managment will be added. 
```

### 3. `stake_root_dividends.py`
Automatically reinvests root subnet dividends across multiple subnets.
```bash
python -m scripts.stake_root_dividends  # Monitors and stakes dividends based on preset percentages
```

## License
MIT License