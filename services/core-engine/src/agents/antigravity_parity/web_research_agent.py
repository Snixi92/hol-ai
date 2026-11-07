"""
WebResearchAgent : Agent de recherche approfondie sur le web et extraction de contenu pour HoL AI.
Implémente les capacités search_web et read_url_content d'Antigravity avec DuckDuckGo,
nettoyage HTML par BeautifulSoup, extraction sémantique et synthèse de sources.
"""
import re
import os
import logging
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

logger = logging.getLogger("hol_ai.web_research_agent")


class WebResearchAgent:
    """Agent expert en recherche d'informations en direct et extraction de contenu web."""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    @classmethod
    def search_web(
        cls,
        query: str,
        max_results: int = 5,
        region: str = "fr-fr"
    ) -> Dict[str, Any]:
        """
        Effectue une recherche web en direct et extrait les titres, snippets et URLs.
        """
        if not query or not query.strip():
            return {"status": "error", "error": "Requête de recherche vide", "results": []}

        results = []
        brave_api_key = os.getenv("BRAVE_API_KEY")

        # 1. Tentative via Brave Search API si clé configurée
        if brave_api_key:
            try:
                headers = {"Accept": "application/json", "X-Subscription-Token": brave_api_key}
                params = {"q": query, "count": max_results, "country": "fr"}
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        web_items = data.get("web", {}).get("results", [])
                        for idx, item in enumerate(web_items[:max_results]):
                            results.append({
                                "rank": idx + 1,
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("description", "")
                            })
                        if results:
                            return {
                                "status": "success",
                                "engine": "Brave Search API",
                                "query": query,
                                "total_results": len(results),
                                "results": results,
                                "verbal_reply": f"Recherche Brave pour '{query}' : {len(results)} source(s) trouvée(s)."
                            }
            except Exception as brave_err:
                logger.warning(f"Brave Search indisponible, bascule sur DuckDuckGo : {brave_err}")

        # 2. Recherche DuckDuckGo (100% gratuit & sans clé d'API)
        try:
            with DDGS() as ddgs:
                for idx, r in enumerate(ddgs.text(query, region=region, max_results=max_results)):
                    results.append({
                        "rank": idx + 1,
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })

            return {
                "status": "success",
                "engine": "DuckDuckGo",
                "query": query,
                "total_results": len(results),
                "results": results,
                "verbal_reply": f"Recherche web pour '{query}' : {len(results)} source(s) trouvée(s)."
            }
        except Exception as e:
            logger.warning(f"Erreur recherche DDGS pour '{query}' : {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "results": []
            }

    @classmethod
    def read_url_content(
        cls,
        url: str,
        max_chars: int = 4000
    ) -> Dict[str, Any]:
        """
        Télécharge une page web et extrait le texte lisible nettoyé de scripts, pubs et styles.
        """
        if not url or not url.startswith(("http://", "https://")):
            return {"status": "error", "error": f"URL invalide : {url}", "content": ""}

        try:
            with httpx.Client(headers=cls.DEFAULT_HEADERS, timeout=12.0, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return {
                        "status": "error",
                        "error": f"Statut HTTP {res.status_code}",
                        "url": url,
                        "content": ""
                    }

                html_text = res.text

            # Parsing et nettoyage BeautifulSoup
            soup = BeautifulSoup(html_text, "html.parser")

            # Retirer scripts, styles, iframe, nav, footer
            for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "svg", "button"]):
                tag.extract()

            title = soup.title.string.strip() if soup.title and soup.title.string else url

            # Extraction des paragraphes et titres
            text_blocks = []
            for elem in soup.find_all(["h1", "h2", "h3", "p", "li", "article"]):
                t = elem.get_text(separator=" ", strip=True)
                if t and len(t) > 20:
                    text_blocks.append(t)

            clean_text = "\n\n".join(text_blocks)
            if not clean_text:
                clean_text = soup.get_text(separator=" ", strip=True)

            truncated_text = clean_text[:max_chars]
            word_count = len(truncated_text.split())

            return {
                "status": "success",
                "url": url,
                "title": title,
                "word_count": word_count,
                "content": truncated_text,
                "is_truncated": len(clean_text) > max_chars,
                "verbal_reply": f"Contenu de '{title}' extrait avec succès ({word_count} mots)."
            }
        except Exception as e:
            logger.error(f"Erreur extraction URL {url} : {e}")
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "content": ""
            }
