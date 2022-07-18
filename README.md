# perpdex-arbitrager

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
