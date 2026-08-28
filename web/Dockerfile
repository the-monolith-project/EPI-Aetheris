FROM node:22-alpine

WORKDIR /app

# Activar Corepack fijando pnpm v9 (compatible con Node 22, requerido por Astro 6+)
RUN corepack enable && corepack prepare pnpm@9 --activate

# Copiar manifiesto de dependencias
COPY package*.json pnpm-lock.yaml* ./

# Instalar dependencias con pnpm v9
RUN pnpm install

# Copiar el código fuente
COPY . .

EXPOSE 4321

# El PID guardado por Astro en .astro/dev.json puede sobrevivir al contenedor
# porque /app se monta desde el host. Docker ya controla la instancia del
# servicio, así que se omite ese lock para evitar falsos positivos al reiniciar.
CMD ["pnpm", "exec", "astro", "dev", "--host", "0.0.0.0", "--ignore-lock"]
