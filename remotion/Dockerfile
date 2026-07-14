FROM node:22-bookworm-slim

# Lambda'ya geçildiği için Chromium artık gerekmez.
# Sadece küçük yardımcı araçlar yeterli.
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

# Derleme tamamlandı — dev bağımlılıklarını temizle (image boyutu küçülür)
RUN npm prune --omit=dev

EXPOSE 3001
CMD ["node", "dist/server/index.js"]
