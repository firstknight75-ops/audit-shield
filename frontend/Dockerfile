# Multi-stage build: Vite static build → nginx serving with security headers.
FROM oven/bun:1 AS builder

WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production=false

COPY . .
RUN bun run build

# ── Runtime: nginx with hardened security headers ──────────────
FROM nginx:1.27-alpine AS runtime

# Replace default config with our hardened one
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers — enforced at the edge (defense in depth alongside app headers)
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), camera=(), microphone=()" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    # CSP — allow same-origin assets only
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';" always;

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets aggressively
    location ~* \.(js|css|woff2?|png|jpg|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Hide nginx version
    server_tokens off;
}
EOF

# Static assets from build
COPY --from=builder /app/dist /usr/share/nginx/html

# Non-root runtime
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx
USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -q --spider http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
