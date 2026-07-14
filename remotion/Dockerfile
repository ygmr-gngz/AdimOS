FROM node:22-bookworm-slim

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

WORKDIR /app
COPY package.json package-lock.json ./

# npm install kullan (npm ci değil) — Railway BuildKit cache'i dosya içeriğine göre kilitlenmişti
# npm install --include=dev garanti typescript kurar
RUN npm install --include=dev

# Sigorta: typescript kurulmadıysa burada anında patlıyor
RUN node_modules/.bin/tsc --version

COPY . .
RUN npm run build

EXPOSE 3001
CMD ["node", "dist/server/index.js"]
