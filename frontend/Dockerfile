# syntax=docker/dockerfile:1.7
FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 AS build

WORKDIR /workspace/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY frontend/ ./
COPY data/seeds /workspace/data/seeds
RUN chown -R node:node /workspace

USER node
ARG VITE_API_BASE_URL
ARG VITE_USE_MOCK=false
RUN test -n "$VITE_API_BASE_URL" \
    && test "$VITE_USE_MOCK" = "false" \
    && npm run build

FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 AS runtime

ENV NODE_ENV=production \
    PORT=3000
WORKDIR /app
COPY --from=build --chown=node:node /workspace/frontend/dist /app/dist
COPY --chown=node:node frontend/docker-server.mjs /app/docker-server.mjs

USER node
EXPOSE 3000
CMD ["node", "/app/docker-server.mjs"]
