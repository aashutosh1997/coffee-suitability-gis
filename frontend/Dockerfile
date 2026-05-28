# TerraBean web — Phase 0 walking skeleton.
# Runs the Vite dev server so VITE_API_BASE is read at runtime and the map renders
# without a static-build/env-baking step. A static nginx build replaces this in Phase 4.
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
