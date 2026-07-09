# -*- coding: utf-8 -*-
"""
Orquestador principal de Buyer Radar.

Flujo:
1. Busca en Hacker News (y, cuando este configurado, Reddit via API oficial)
   mensajes que combinen una frase de intencion de compra con un tema/nicho.
2. Filtra cada resultado con IA (clasifica LEAD vs RUIDO).
3. Genera un digest (email/consola) solo con los LEADs.

Pensado para ejecutarse solo, en un cron (GitHub Actions gratis), sin
intervencion manual. Configuracion por variables de entorno:

  ANTHROPIC_API_KEY   -> necesaria para el filtrado con IA (si falta, se
                         incluyen todos los resultados sin filtrar y se avisa)
  TOPICS              -> lista de temas separados por coma (por defecto: demo)
  RESEND_API_KEY      -> opcional, para enviar el digest por email real
  DIGEST_TO_EMAIL     -> email de destino del digest
"""
import os
import json
from prototype import build_queries, search_hn, INTENT_PHRASES
from classify import classify_signal

TOPICS_ENV = os.environ.get("TOPICS", "automation,saas,crm")
TOPICS = [t.strip() for t in TOPICS_ENV.split(",") if t.strip()]


def build_queries_for_topics(topics):
    queries = []
    for phrase in INTENT_PHRASES:
        for topic in topics:
            queries.append(f"{phrase} {topic}")
    return queries


def gather_raw_signals(max_queries=10, hits_per_query=5):
    queries = build_queries_for_topics(TOPICS)
    all_results = []
    for q in queries[:max_queries]:
        try:
            hits = search_hn(q, hits_per_page=hits_per_query)
            all_results.extend(hits)
        except Exception as e:
            print(f"[aviso] fallo buscando '{q}': {e}")
    # dedupe por url
    seen = set()
    deduped = []
    for r in all_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    return deduped


def filter_leads(raw_signals):
    has_api_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not has_api_key:
        print("[aviso] No hay ANTHROPIC_API_KEY configurada: se listan TODOS los "
              "resultados sin filtrar. Configura la key para activar el filtro de IA.")
        return [{**r, "is_lead": None, "reason": "sin clasificar (falta API key)"} for r in raw_signals]

    leads = []
    for r in raw_signals:
        try:
            result = classify_signal(r["text"])
            r["is_lead"] = result.get("is_lead", False)
            r["reason"] = result.get("reason", "")
            if r["is_lead"]:
                leads.append(r)
        except Exception as e:
            print(f"[aviso] fallo clasificando: {e}")
    return leads


def format_digest(leads):
    if not leads:
        return "Sin leads nuevos en esta pasada."
    lines = [f"BUYER RADAR - {len(leads)} señal(es) de compra detectada(s)\n"]
    for l in leads:
        lines.append(f"- [{l['source']}] {l['text']}")
        lines.append(f"  {l['url']}")
        if l.get("reason"):
            lines.append(f"  motivo: {l['reason']}")
        lines.append("")
    return "\n".join(lines)


def send_digest_email(digest_text):
    resend_key = os.environ.get("RESEND_API_KEY")
    to_email = os.environ.get("DIGEST_TO_EMAIL")
    if not resend_key or not to_email:
        print("[aviso] Envio de email no configurado (falta RESEND_API_KEY o DIGEST_TO_EMAIL).")
        return False
    import requests
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {resend_key}"},
        json={
            "from": "Buyer Radar <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "Buyer Radar - nuevas señales de compra",
            "text": digest_text,
        },
        timeout=15,
    )
    return r.status_code < 300


def main():
    print(f"Temas configurados: {TOPICS}\n")
    raw = gather_raw_signals()
    print(f"Resultados en bruto: {len(raw)}")
    leads = filter_leads(raw)
    print(f"Leads tras filtrar: {len(leads)}\n")

    digest = format_digest(leads)
    print(digest)

    with open("digest_ultima_ejecucion.txt", "w", encoding="utf-8") as f:
        f.write(digest)

    sent = send_digest_email(digest)
    if sent:
        print("Digest enviado por email.")


if __name__ == "__main__":
    main()
