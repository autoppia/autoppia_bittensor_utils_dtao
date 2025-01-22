# DTAO Helper Scripts

A collection of scripts for managing DTAO investments in Bittensor testnet.

## Quick Setup

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
pip install python-dotenv colorama tabulate
```

3. Set up your wallet password in `.env` (see `.env.template`)

## Available Scripts

### 1. `dca.py`
Gradually stakes TAO into multiple subnets using dollar-cost averaging.
```bash
python dca.py  # Stakes 0.1 TAO in small increments of 0.005
```

### 2. `dca_sell.py`
Gradually sells alpha holdings from multiple subnets.
```bash
python dca_sell.py  # Sells specified percentages of alpha in small increments
```

### 3. `stake_root_dividends.py`
Automatically reinvests root subnet dividends across multiple subnets.
```bash
python stake_root_dividends.py  # Monitors and stakes dividends based on preset percentages
```

## License
MIT License