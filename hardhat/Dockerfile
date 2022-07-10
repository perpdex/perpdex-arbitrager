FROM node:16-alpine3.15
RUN apk update && \
    apk add git curl

WORKDIR /app
COPY package.json /app

RUN yarn install
