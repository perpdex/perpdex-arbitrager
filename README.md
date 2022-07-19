# perpdex-arbitrager

An arbitrage bot program for perpdex.

Supported chain

- shibuya (astar testnet)

## Setup

### 1. create private key for EVM

### 2. create .env including USER_PRIVATE_KEY as following:

```
USER_PRIVATE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. deposit native token for gas

shibuya faucet: https://docs.astar.network/integration/testnet-faucet

## How to run arbitrager

```bash
docker-compose -f docker-compose-shibuya.yml up

# or run background as daemon
docker-compose -f docker-compose-shibuya.yml up -d
```

## Commands

set collateral balance 1 billion SBY (testnet only)

```bash 
docker-compose -f docker-compose-shibuya.yml run py-shibuya python main.py setCollateralBalance 1000000000
```

see account info

```bash 
docker-compose -f docker-compose-shibuya.yml run py-shibuya python main.py accountInfo
```

see all commands

```bash
docker-compose -f docker-compose-shibuya.yml run py-shibuya python main.py
```

see command help

```bash
docker-compose -f docker-compose-shibuya.yml run py-shibuya python main.py setCollateralBalance --help
```

## run tests
```
# compile deps contract
cd deps/perpdex-contract
npm install
npm run build
cd ../../

# run tests
docker compose run --rm py-test python -m pytest tests
```
* to run the CEX testnet tests, you have to set `XXX_API_KEY` and `XXX_SECRET` envs
* .env will be automatically loaded (see: [pytest-dotenv](https://github.com/theskumar/python-dotenv))
