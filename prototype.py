# -*- coding: utf-8 -*-
"""
Prototipo: motor de deteccion de "senales de compra" en Hacker News y Reddit.
Busca mensajes donde alguien pide una alternativa/herramienta/recomendacion.
"""
import requests
import json
from datetime import datetime, timezone

INTENT_PHRASES = [
    "alternative to",
    "looking for a tool",
    "any tool that can",
    "recommend a tool for",
    "what do you use for",
    "looking for software",
    "recommend an app for",
]

# Para la demo, buscamos senales genericas de "quiero una herramienta que haga X"
# En produccion esto se filtra por nicho especifico (el cliente elige palabras clave).
DEMO_TOPICS = ["automation", "saas", "crm"]

HEADERS = {"User-Agent": "buyer-radar-prototype/0.1 (research demo)"}


def search_hn(query, hits_per_page=5):
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": query, "tags": "comment,story", "hitsPerPage": hits_per_page}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = []
    for hit in data.get("hits", []):
        text = hit.get("comment_text") or hit.get("story_text") or hit.get("title") or ""
        if not text:
            continue
        results.append({
            "source": "HackerNews",
            "text": text[:220].replace("\n", " "),
            "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "date": hit.get("created_at"),
            "query": query,
        })
    return results


def search_reddit(query, limit=5):
    url = "https://www.reddit.com/search.json"
    params = {"q": query, "sort": "new", "limit": limit}
    r = requests.get(url, params=params, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return [{"source": "Reddit", "text": f"[error {r.status_code} al consultar Reddit]", "url": "", "date": "", "query": query}]
    data = r.json()
    results = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        title = d.get("title", "")
        results.append({
            "source": "Reddit",
            "text": title[:220],
            "url": f"https://reddit.com{d.get('permalink', '')}",
            "date": datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc).isoformat() if d.get("created_utc") else "",
            "query": query,
        })
    return results


def build_queries():
    queries = []
    for phrase in INTENT_PHRASES:
        for topic in DEMO_TOPICS:
            queries.append(f'"{phrase}" {topic}')
    return queries


def main():
    all_results = []
    queries = build_queries()
    print(f"Probando {len(queries)} combinaciones de busqueda (frase de intencion + tema)...\n")

    for q in queries[:6]:  # limitamos la demo a 6 combinaciones para no saturar las APIs
        try:
            hn = search_hn(q, hits_per_page=3)
            all_results.extend(hn)
        except Exception as e:
            print(f"[HN error] {q}: {e}")
        try:
            rd = search_reddit(q, limit=3)
            all_results.extend(rd)
        except Exception as e:
            print(f"[Reddit error] {q}: {e}")

    # dedupe por url
    seen = set()
    deduped = []
    for r in all_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)

    print(f"Resultados unicos encontrados: {len(deduped)}\n")
    for r in deduped:
        print(f"[{r['source']}] (busqueda: {r['query']})")
        print(f"  {r['text']}")
        print(f"  {r['url']}")
        print()

    with open("resultados_demo.json", "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
