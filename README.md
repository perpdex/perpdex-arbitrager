# perpdex-arbitrager

## run tests
```
# compile deps contract
cd deps/perpdex-contract
npm install
npm run build
cd ../../

# run tests
docker-compose --env-file=.env.test run --rm py-test python -m pytest tests
```
