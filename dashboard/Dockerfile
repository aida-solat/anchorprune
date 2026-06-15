# AnchorPrune read-only dashboard image (v0.9). Build context: ./dashboard.
FROM node:20-slim AS base

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

ENV NEXT_PUBLIC_ANCHORPRUNE_API_URL=http://localhost:8000
EXPOSE 3000

CMD ["npm", "run", "start"]
