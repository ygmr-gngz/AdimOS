FROM node:20-bookworm-slim

# Chromium + gerekli sistem kütüphaneleri
RUN apt-get update && apt-get install -y \
  chromium \
  fonts-noto-color-emoji \
  fonts-liberation \
  ffmpeg \
  --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV BROWSER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

EXPOSE 3001
CMD ["sh", "-c", "echo 'Container CMD basliyor...' && node --version && ls node_modules/.bin/tsx && node_modules/.bin/tsx src/server/index.ts 2>&1 || echo 'TSX CRASH exit:'$?"]
