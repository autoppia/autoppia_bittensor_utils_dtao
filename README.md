# DTAO Helper Scripts

Investment management tools for Bittensor testnet, featuring market-cap weighted and DCA strategies.

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

### 1. TAO16 (`tao16.py`)
Market cap-weighted investment in top 16 subnets (S&P 500 analogy).

```bash
python -m scripts.tao16 --total 1.0 --increment 0.1 --network test
```

### 2. TAO64 (`tao64.py`)
DCA investment across specified subnets.

```bash
python -m scripts.tao64 --netuids 1 2 3 --total 1.0 --increment 0.1
```

Options:
- Empty `--netuids`: Auto-selects all available subnets
- Specific `--netuids`: Targets only listed subnets

### 3. DCA Sell (`dca_sell.py`)
Percentage-based position reduction.

```bash
python -m scripts.dca_sell --netuids 1 2 --percentages 0.5 0.3 --reduction 5.0
```

### 4. Stake Root Dividends (Beta)
Auto-reinvests validator dividends.

```bash
python -m scripts.stake_root_dividends_for_validator --validator_hotkey HOTKEY
```

## License
From Autoppia Team with ❤️