// Los tipos generados por Astro (.astro/types.d.ts, que referencia
// astro/client) los levanta ahora el `include` de tsconfig.json, así que
// aquí solo queda el tipado manual de las variables PUBLIC_* del proyecto
// -- Astro no genera un tipo para PUBLIC_API_URL sin un esquema astro:env.
interface ImportMetaEnv {
  readonly PUBLIC_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
