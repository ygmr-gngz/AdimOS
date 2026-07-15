FROM node:22-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    chromium \
    fonts-noto-color-emoji \
    fonts-liberation \
    ffmpeg \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV BROWSER_EXECUTABLE_PATH=/usr/bin/chromium

# Root Directory=remotion → build context remotion/ dizini, yollar context-göreli
COPY package.json package-lock.json ./
RUN npm install --include=dev

# Sigorta: typescript kurulmadıysa burada net hata verir (sahte paket indirme yok)
RUN ./node_modules/.bin/tsc --version

COPY . .
RUN npm run build

EXPOSE 3001
CMD ["npm", "start"]
