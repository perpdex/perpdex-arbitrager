FROM node:16-alpine3.15
RUN apk update && \
    apk add git curl

WORKDIR /app
COPY package.json /app
COPY yarn.lock /app

RUN yarn install
