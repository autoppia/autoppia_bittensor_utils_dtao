# DTAO Helper Scripts

A collection of scripts for managing DTAO investments in Bittensor testnet, featuring automated investment strategies inspired by traditional finance.

## Overview

This toolkit provides various investment strategies for the Bittensor network:
- Dollar-cost averaging (DCA) for stake management
- Automated selling with percentage-based targets
- S&P 500-inspired weighted investment in top subnets (TAO16)
- Dividend reinvestment for validators

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

3. Configure wallet password in `.env` (template available in `.env.template`)

## Investment Scripts

### 1. TAO16 Strategy (`tao16.py`)
Implements a market cap-weighted investment strategy across top 16 subnets, similar to S&P 500 index investing.

```bash
python -m scripts.tao16 [--total-stake AMOUNT] [--increment AMOUNT]
```

Arguments:
- `--total-stake`: Total TAO to invest (default: 1.0)
- `--increment`: DCA increment size (default: 0.1)

### 2. Dollar-Cost Averaging (`dca.py`)
Gradually stakes TAO across multiple subnets.

```bash
python -m scripts.dca --netuids NETUID [NETUID ...] --increment AMOUNT --total-stake AMOUNT
```

Arguments:
- `--netuids`: Target subnet IDs
- `--increment`: DCA increment size
- `--total-stake`: Total investment amount

### 3. DCA Sell (`dca_sell.py`)
Gradually reduces positions in specified subnets.

```bash
python -m scripts.dca_sell --netuids NETUID [NETUID ...] --percentages PERCENT [PERCENT ...] --reduction AMOUNT
```

Arguments:
- `--netuids`: Target subnet IDs
- `--percentages`: Selling targets per subnet (0.5 = 50%)
- `--reduction`: Alpha reduction per iteration (default: 5.0)

### 4. Dividend Reinvestment (`stake_root_dividends.py`)
Automatically reinvests validator root subnet dividends (Beta).

```bash
python -m scripts.stake_root_dividends_for_validator --validator_hotkey HOTKEY
```

## License

From Autoppia Team with ❤️