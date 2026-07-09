# Buyer Radar (prototipo)

Detecta señales de compra reales en Hacker News (y próximamente Reddit): mensajes
donde alguien pide una alternativa/herramienta para un problema concreto. Filtra
el ruido (anuncios de producto propio, blogs, debates) con IA y manda un digest
solo con los leads reales.

## Estado actual

- `prototype.py`: busca en Hacker News combinando frases de intención de compra
  ("alternative to", "looking for a tool", etc.) con temas/nichos. **Probado y
  funciona** (validado vía fetch directo, ver nota de sandbox abajo).
- `classify.py`: filtro de IA que distingue LEAD vs RUIDO. La lógica está
  validada a mano contra 6 ejemplos reales (`GOLDEN_SET`), pero **todavía no se
  ha ejecutado contra la API real** porque hace falta una `ANTHROPIC_API_KEY`.
- `main.py`: orquestador que junta todo y genera el digest final.
- `.github/workflows/radar.yml`: hace que esto se ejecute solo, cada 6 horas,
  gratis, en GitHub Actions — sin servidor, sin que nadie lo lance a mano.

## Nota sobre el entorno de desarrollo (sandbox)

Este entorno de trabajo (donde se construyó el prototipo) tiene una red
restringida: bloquea las peticiones directas a `hn.algolia.com` y a
`reddit.com` vía `requests`. Por eso no se pudo ejecutar `main.py` de punta a
punta aquí dentro. Esto **no es un problema del código** — en GitHub Actions
(donde va a correr de verdad) no existe esa restricción, y ya se comprobó por
otra vía que Hacker News responde bien y con datos reales.

## Lo que falta para que corra de verdad, y quién lo hace

1. **Cuenta de GitHub** (si no tienes) y crear un repositorio con este código.
   — lo haces tú, es gratis.
2. **API key de Anthropic** (para el filtro de IA) — te la puedo ayudar a
   sacar cuando lleguemos a ese paso, tiene un coste muy bajo por uso (céntimos
   por cada mensaje clasificado).
3. **Cuenta gratuita de Reddit para developers** (para leer Reddit vía su API
   oficial, en vez de scraping) — 5 minutos, te guío paso a paso cuando toque.
4. **(Opcional) Cuenta de Resend** (gratis hasta cierto volumen) si quieres que
   el digest llegue por email en vez de solo guardarse en un archivo.
5. Añadir esas keys como "Secrets" en la configuración del repositorio de
   GitHub — te lo explico paso a paso cuando lleguemos ahí.

Ninguno de estos pasos hay que hacerlo ya — se hacen uno a uno, cuando toque,
igual que hemos ido haciendo hasta ahora.
