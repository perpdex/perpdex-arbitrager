# perpdex-arbitrager

## run tests
```
cd deps/perpdex-contract
npm install
nmp run build
cd ../../

docker-compose --env-file=.env.test run --rm py-test python -m pytest tests
```