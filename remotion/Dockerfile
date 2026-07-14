FROM node:22-bookworm-slim

# @remotion/renderer peer dep Chromium indir — Lambda'ya geçildi, atla
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV REMOTION_SKIP_CHROMIUM_INSTALL=1

RUN apt-get update && apt-get install -y \
  --no-install-recommends \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# TypeScript server kodunu derle
RUN npx tsc -p tsconfig.server.json

# Dev bağımlılıklarını temizle (image boyutu küçülür)
RUN npm prune --omit=dev

EXPOSE 3001
CMD ["node", "dist/server/index.js"]
