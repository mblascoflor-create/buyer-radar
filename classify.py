# -*- coding: utf-8 -*-
"""
Capa de filtrado con IA: distingue una senal de compra real (alguien pidiendo
una herramienta/alternativa) de ruido (anuncios de producto propio, blogs,
discusiones meta, etc.).

Requiere una ANTHROPIC_API_KEY valida en variable de entorno para ejecutarse
de verdad. Este script NO se ha ejecutado contra la API todavia (no hay key
en este entorno) -- la clasificacion de ejemplo mas abajo la hice yo mismo
(Claude) leyendo los 20 resultados reales uno a uno, a mano, como referencia
para validar que el prompt tiene sentido antes de automatizarlo.
"""
import os
import json

try:
    import anthropic
except ImportError:
    anthropic = None

CLASSIFY_PROMPT = """Eres un filtro que distingue, dentro de un foro online (Hacker News, Reddit, etc.), si un mensaje es:

- LEAD: alguien pidiendo genuinamente una recomendacion, alternativa o herramienta para resolver un problema real que tiene ahora mismo. Es una oportunidad de venta real.
- RUIDO: cualquier otra cosa -- un fundador anunciando su propio producto ("Show HN: mi herramienta..."), un blog/ebook, una discusion meta sobre el mercado, un comentario tecnico que solo menciona la palabra de pasada, etc.

Responde SOLO con JSON: {{"is_lead": true/false, "reason": "una frase corta explicando por que"}}

Mensaje a clasificar:
\"\"\"{text}\"\"\"
"""


def classify_signal(text: str, model: str = "claude-3-5-haiku-20241022") -> dict:
    """Clasifica un texto como LEAD o RUIDO usando la API de Claude.
    Requiere ANTHROPIC_API_KEY en el entorno."""
    if anthropic is None:
        raise RuntimeError("Falta instalar el paquete 'anthropic' (pip install anthropic)")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el entorno")

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=150,
        messages=[{"role": "user", "content": CLASSIFY_PROMPT.format(text=text)}],
    )
    raw = msg.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"is_lead": False, "reason": f"[no parseable] {raw}"}


# --- Set de validacion manual (hecho a mano por Claude sobre resultados reales) ---
# Esto sirve para comprobar, cuando haya API key, que el clasificador automatico
# coincide con este criterio de referencia.
GOLDEN_SET = [
    {"text": "N8n.io - Workflow automation alternative to Zapier (story submission)", "expected_is_lead": False, "reason": "Enlace a la propia web de n8n, no es una pregunta de nadie"},
    {"text": "Show HN: Automatisch - Open source workflow automation, an alternative to Zapier", "expected_is_lead": False, "reason": "Fundador anunciando su propio producto"},
    {"text": "Ask HN: What are some cheap/self-hosted alternatives to Zapier? I'm looking for only some basic integrations", "expected_is_lead": True, "reason": "Pregunta directa y real pidiendo recomendacion, con contexto de necesidad concreta"},
    {"text": "Show HN: Aivaro - Open-source AI alternative to Zapier (founder describing why he built it)", "expected_is_lead": False, "reason": "Es el fundador narrando el origen de su propio producto, no un comprador"},
    {"text": "Ask HN: Why the Deluge of Zapier Alternatives? (discusion sobre por que hay tantas alternativas)", "expected_is_lead": False, "reason": "Discusion meta sobre el mercado, no una necesidad de compra"},
    {"text": "Some Alternatives to Zapier (enlace a pregunta antigua de Quora)", "expected_is_lead": False, "reason": "Contenido agregado/reenlazado, no una persona pidiendo ayuda ahora"},
]


def run_golden_set_check():
    print("Nota: esto imprime el criterio de referencia (hecho a mano), no una llamada real a la API.\n")
    for item in GOLDEN_SET:
        print(f"- {'LEAD' if item['expected_is_lead'] else 'RUIDO':6} | {item['text'][:80]}")
        print(f"          motivo: {item['reason']}\n")


if __name__ == "__main__":
    run_golden_set_check()
