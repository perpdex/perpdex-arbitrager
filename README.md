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

* shibuya faucet: https://docs.astar.network/integration/testnet-faucet
* zksync2 testnet: 
  * get ETH Goerli from below urls
    - https://goerli-faucet.mudit.blog/
    - https://faucets.chain.link/goerli
    - https://goerli-faucet.slock.it/
  * deposit ETH Goerli to zksync2 here: https://portal.zksync.io/bridge

## How to run arbitrager
```bash
git submodule update --init --recursive

# set collateral balance 1 billion SBY (testnet only)
docker-compose -f docker-compose-shibuya.yml run py-shibuya python main.py setCollateralBalance 1000000000

# run arbitrager(shibuya)
docker-compose -f docker-compose-shibuya.yml up

# run arbitrager(zksync2 testnet)
docker-compose -f docker-compose-zksync2-testnet.yml up

# or run in the background as daemon
docker-compose -f docker-compose-shibuya.yml up -d
docker-compose -f docker-compose-zksync2-testnet.yml up -d
```

## Commands

**note**: you can use below commands with replacing shibuya to network-name

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
