FROM node:20-alpine

WORKDIR /app

# Activar Corepack fijando pnpm v9 (compatible con Node 20)
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copiar manifiesto de dependencias
COPY package*.json pnpm-lock.yaml* ./

# Instalar dependencias con pnpm v9
RUN pnpm install

# Copiar el código fuente
COPY . .

EXPOSE 4321

CMD ["pnpm", "run", "dev"]
