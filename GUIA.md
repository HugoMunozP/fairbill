# Fairbill: guía para publicar la página gratis

## Cuánto cuesta

| Parte | Servicio | Costo |
|---|---|---|
| La página web | GitHub Pages | Gratis |
| Publicación automática | GitHub Actions | Gratis |
| Base de datos (los recibos que comparte la gente) | Supabase, plan gratis | Gratis |
| Dominio propio (ej. fairbill.com) | Cloudflare o Namecheap | Unos $10–15 al año. Opcional al inicio. |

**¿Por qué Supabase y no solo GitHub?** GitHub Pages solo muestra páginas: no puede **guardar** lo que la gente envía. Para guardar los recibos hace falta una base de datos, y Supabase la da gratis. Su único detalle: si pasan 7 días sin que nadie use la página, el proyecto se pausa. Supabase te avisa por correo antes, y lo reactivas entrando a su panel. Cuando la página tenga visitas, no se pausa.

---

## Qué hay en la carpeta

```
data/            ← LO ÚNICO QUE VAS A EDITAR
  config.json      tu dominio, correo y claves de Supabase
  precios.csv      precios anunciados de cada plan (actualízalo cada mes)
  proveedores.csv  texto de cada proveedor y cuánto suben después de la promo
src/             diseño y textos de la página (plantillas)
tools/build.py   arma la web completa a partir de data/ y src/
public/          la web ya armada (se regenera sola en GitHub)
supabase/        schema.sql y plans.sql para la base de datos
.github/         instrucciones para que GitHub publique solo
```

Para ver la página en tu computadora, abre `public/index.html` (funciona en modo demo).

---

## Paso 1. Subir todo a GitHub · 10 minutos

1. Crea una cuenta en **github.com**.
2. Arriba a la derecha: **+ → New repository**. Nombre: `fairbill`, visibilidad **Public** (GitHub Pages es gratis en repositorios públicos). Dale **Create repository**.
3. En el repositorio vacío, haz clic en **uploading an existing file** y arrastra **todo el contenido** de la carpeta `fairbill`, no la carpeta en sí. Abajo, **Commit changes**.
4. **Ojo con la carpeta `.github`:** como empieza con punto, Mac y Windows a veces la ocultan y no se sube. Revisa si en el repositorio aparece `.github/workflows/deploy.yml`. Si no está:
   - **Add file → Create new file**.
   - En el nombre escribe exactamente `.github/workflows/deploy.yml`.
   - Pega el contenido de ese archivo (ábrelo con el Bloc de notas) y dale **Commit**.

   La forma más fácil de evitar este problema es usar la app **GitHub Desktop**, que sube todo sin fallar.
5. Ve a **Settings → Pages**. En **Source**, elige **GitHub Actions**.
6. Ve a la pestaña **Actions**. Vas a ver "Build and publish Fairbill" corriendo; en 1 o 2 minutos se pone en verde.
7. Tu web queda en `https://TU-USUARIO.github.io/fairbill/`.

**Desde ahora, cada vez que cambies cualquier archivo en GitHub, la web se rearma y se publica sola.**

## Paso 2. Poner tu dirección y tu correo · 2 minutos

En GitHub, abre `data/config.json`, haz clic en el lápiz (✏️) para editar y cambia:

```json
"site_url": "https://TU-USUARIO.github.io/fairbill",
"contact_email": "tucorreo@gmail.com",
```

Dale **Commit changes**. En un par de minutos la web se actualiza. El `site_url` es importante: Google lo usa para el mapa del sitio y para las direcciones oficiales de cada página.

## Paso 3. Crear la base de datos (Supabase) · 10 minutos

1. Entra a **supabase.com** y crea una cuenta gratis, sin tarjeta.
2. Crea un proyecto nuevo: **New project**, de nombre `fairbill`, región **East US**.
3. Ve a **SQL Editor → New query**. Pega todo `supabase/schema.sql` y dale **Run**.
4. Haz otra **New query**, pega `supabase/plans.sql` y dale **Run**.
5. En **Project Settings → API** copia la **Project URL** y la **anon public key**.
6. En GitHub, edita `data/config.json` y pégalas:

```json
"supabase_url": "https://abcd1234.supabase.co",
"supabase_anon_key": "eyJ...",
```

7. Dale **Commit**. Cuando GitHub termine de publicar, la franja rosada de "Demo mode" desaparece: la web ya guarda recibos reales.

> La clave **anon** es pública por diseño: las reglas de la base de datos solo dejan **agregar** recibos y leer resúmenes. **Nunca** pongas la clave `service_role`.

## Paso 4. Que Google te encuentre (incluidos sus resúmenes con IA) · 15 minutos

Google dice que para aparecer en sus funciones con IA (AI Overviews y AI Mode) no hace falta nada especial, solo las buenas prácticas de siempre. Esto ya viene listo en la web:

- **Todo el contenido importante está en el HTML**, sin depender de JavaScript para que Google lo lea: tabla de precios, preguntas frecuentes, páginas por proveedor.
- **Datos estructurados (schema.org)** en todas las páginas: sitio web, organización, la herramienta, el conjunto de datos de precios, preguntas frecuentes, artículos y migas de pan. Así Google entiende qué es cada cosa.
- **8 páginas por proveedor** (Spectrum, Xfinity, AT&T Fiber…). Responden lo que la gente busca, como "¿cuánto sube Spectrum después del primer año?", con datos concretos y fecha de revisión.
- **Una guía**, "How to lower your internet bill", con el guion de llamada.
- **`sitemap.xml`, `robots.txt`**, direcciones oficiales (canonical), imagen para compartir en redes (`og.png`), ícono y página 404.
- **Enlaces internos** entre todas las páginas.

Lo que te toca hacer:

1. Entra a **search.google.com/search-console** y agrega tu sitio (**URL prefix**, con tu `site_url`).
2. Verifícalo. Si usas GitHub Pages sin dominio propio, elige **HTML tag**: Google te da una línea `<meta name="google-site-verification" ...>`. Pégala en `src/index.html` debajo de `<meta charset="utf-8">` y haz commit.
3. En el menú **Sitemaps**, envía `sitemap.xml`.
4. Haz lo mismo en **Bing Webmaster Tools** (bing.com/webmasters). Puedes importar todo desde Search Console con un clic, y Bing alimenta a otros buscadores con IA.

Lo que más te va a ayudar a que una IA te cite es tener **datos propios que nadie más tiene**: los recibos reales de la gente. Mientras más reportes juntes, más vale tu web como fuente.

## Paso 5. Tu dominio propio (opcional, recomendado antes de AdSense)

1. Compra el dominio en **Cloudflare Registrar** o **Namecheap**. Antes, revisa en Google y en uspto.gov que no sea una marca registrada.
2. En GitHub crea el archivo `data/CNAME` con una sola línea: tu dominio, por ejemplo `www.fairbill.com`.
3. En GitHub, **Settings → Pages → Custom domain**: escribe tu dominio y sigue las instrucciones de DNS que te muestra (registros CNAME y A en tu proveedor de dominio). Luego activa **Enforce HTTPS**.
4. Cambia `site_url` en `data/config.json` por tu dominio nuevo.
5. En Search Console agrega el dominio nuevo y vuelve a enviar el sitemap.

## Paso 6. AdSense (cuando ya tengas visitas)

1. Postula en **adsense.google.com**, idealmente con tu dominio propio.
2. Google te da un código: pégalo en `src/index.html` dentro de `<head>`.
3. Reemplaza `<div class="ad" id="ad-top">Advertisement</div>` en `src/index.html` por el bloque de anuncio que te dé AdSense.
4. Crea el archivo `data/ads.txt` con la línea que te da Google. La web lo publica sola en la raíz, que es donde Google lo busca.

## Tu rutina

**Cada semana, revisar fotos de recibos (15 minutos).** Al final de `supabase/schema.sql` están las consultas listas. Para cada foto:

1. Ábrela en Supabase → **Storage → bills** y comprueba que el precio coincida.
2. Si coincide, marca el reporte como verificado; si no, márcalo como no contado.
3. En los dos casos, **borra la foto**. Esto es lo que promete la página.

**Cada mes, actualizar precios (20 minutos).**

1. Revisa los precios en la web de cada proveedor.
2. Edita `data/precios.csv` en GitHub con el lápiz y cambia la fecha `prices_checked` en `data/config.json`. La web, la tabla y las 8 páginas de proveedores se actualizan solas.
3. Si un precio cambió mucho o agregaste un plan nuevo, actualiza también la base de datos. Tienes dos formas: corre `python tools/build.py` en tu computadora y pega el `supabase/plans.sql` que se genera en el SQL Editor de Supabase, o pídeme que te lo genere. (Los planes que la base de datos aún no conoce igual se cuentan, siempre que el precio esté entre $10 y $400.)

**Conseguir los primeros reportes.** Empieza con una ciudad, por ejemplo Austin, y publica en su subreddit y en grupos de inquilinos, con un gancho concreto: *"Spectrum anuncia $40 pero en Austin la gente paga $X"*. Lee las reglas de cada grupo sobre autopromoción.

## Cosas que conviene saber

- El límite de un reporte por dispositivo usa un identificador guardado en el navegador. Alguien que borre sus datos de navegación puede volver a reportar. La mediana, el mínimo de 5 reportes y las fotos verificadas compensan eso.
- La lectura automática del precio desde la foto no está incluida; por ahora lo verificas tú a mano.
- Los nombres de los proveedores se usan para comparar precios, como hacen otros sitios comparadores, pero no uses sus logos. No soy abogado: si el proyecto crece, consulta con uno sobre los términos y la privacidad.
