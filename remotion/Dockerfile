FROM node:20-bookworm-slim

# Chromium sistem bağımlılıkları — @remotion/renderer peer dep gerektiriyor
# (Lambda Bridge Chromium kullanmıyor; ama kurulum sırasında postinstall gerekiyor)
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
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# TypeScript server kodunu derle
RUN npm run build

EXPOSE 3001
CMD ["node", "dist/server/index.js"]
