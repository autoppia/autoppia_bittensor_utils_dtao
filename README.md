# DTAO Helper Scripts

Advanced investment management tools for Bittensor testnet, featuring market cap-weighted and DCA strategies.

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
pip install -r requirements.txt
```

3. Set wallet password in `.env` (see `.env.template`)

## Investment Scripts

### 1. TAO64 - S&P 500 Style Investment Strategy
Dollar-cost averaging into the top 64 subnets weighted by market capitalization, mirroring the S&P 500's investment approach. Configurable to any number of top subnets (e.g., TAO16 for top 16).

```bash
# Example for top 64 subnets
python -m scripts.tao_n --total 1.0 --increment 0.1 --network test --n 64

# Example for top 16 subnets
python -m scripts.tao_n --total 1.0 --increment 0.1 --network test --n 16
```

Options:
- `--n`: Number of top subnets to target (default: 16)
- `--total`: Total TAO to invest
- `--increment`: DCA increment size
- `--network`: Choose 'test' or 'main' network

### 2. DCA Investment (`dca.py`)
Dollar-cost averaging investment across specified subnets.

```bash
# Specific subnets
python -m scripts.dca --netuids 1 2 3 --total 1.0 --increment 0.1

# All available subnets
python -m scripts.dca --total 1.0 --increment 0.1
```

Options:
- Empty `--netuids`: Auto-selects all available subnets
- Specific `--netuids`: Targets only listed subnets
- `--total`: Total amount to stake
- `--increment`: DCA increment size

### 3. DCA Sell (`dca_sell.py`)
Percentage-based position reduction across subnets.

```bash
python -m scripts.dca_sell --netuids 1 2 --percentages 0.5 0.3 --reduction 10
```

Options:
- `--netuids`: Target subnet IDs
- `--percentages`: Reduction percentage per subnet
- `--reduction`: Total reduction amount

### 4. Stake Root Dividends (`stake_root_dividends.py`)
Automatically reinvests validator dividends.

```bash
python -m scripts.stake_root_dividends --validator_hotkey HOTKEY
```

## Features

- Market cap-weighted investment strategies
- Configurable subnet targeting (N top subnets)
- Dollar-cost averaging (DCA) implementation
- Position reduction management
- Dividend reinvestment automation
- Support for both testnet and mainnet
- Detailed balance tracking and reporting
- Color-coded console output

## License
From Autoppia Team with ❤️