FROM node:16 as builder

RUN \
    git clone -b audit-20220612-3 --depth 1 --recursive \
      https://github.com/perpdex/perpdex-contract.git perpdex-contract \
    && cd perpdex-contract \
    && npm install \
    && npm run build \
    && rm -rf node_modules

FROM python:3.8.12

COPY --from=builder /perpdex-contract /app/deps/perpdex-contract

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
