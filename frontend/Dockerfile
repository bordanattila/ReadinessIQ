FROM node:22-slim

WORKDIR /app

# Install dependencies (build context must be repo root: docker build -f frontend/Dockerfile .)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and Vite entry/config
COPY frontend/index.html .
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.node.json .
COPY frontend/tsconfig.app.json .

ENV NODE_ENV=development

EXPOSE 5173

# --host 0.0.0.0 so the dev server is reachable outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
