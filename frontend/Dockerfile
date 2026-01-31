FROM node:24.13.0

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy dependency files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Expose Vite's default port
EXPOSE 3000

# Run dev server with host flag to allow external access
CMD ["pnpm", "dev", "--host"]