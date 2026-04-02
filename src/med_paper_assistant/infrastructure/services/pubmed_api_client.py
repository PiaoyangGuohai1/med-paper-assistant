"""
HTTP Client for MCP-to-MCP communication.

This module provides a client for mdpaper to communicate directly
with pubmed-search MCP via HTTP API, bypassing the Agent.

Author: u9401066@gap.kmu.edu.tw
"""

import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import httpx
import requests
import structlog

logger = structlog.get_logger()

# Default configuration
DEFAULT_PUBMED_API_URL = "http://127.0.0.1:8765"


class PubMedAPIClient:
    """
    HTTP client for communicating with pubmed-search MCP's HTTP API.

    This enables MCP-to-MCP direct communication for verified data:
    - mdpaper only receives PMID from Agent
    - mdpaper fetches verified metadata directly from pubmed-search
    - Prevents Agent from modifying/hallucinating bibliographic data
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize the API client.

        Args:
            base_url: pubmed-search API URL (default from env or localhost:8765)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.environ.get("PUBMED_MCP_API_URL", DEFAULT_PUBMED_API_URL)
        self.timeout = timeout
        logger.info(f"PubMedAPIClient initialized with URL: {self.base_url}")

    def get_cached_article(
        self, pmid: str, fetch_if_missing: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get article metadata from pubmed-search cache.

        This is the primary method for MCP-to-MCP data retrieval.

        Args:
            pmid: PubMed ID
            fetch_if_missing: If True, pubmed-search will fetch from NCBI if not cached

        Returns:
            Article metadata dict with verified=True, or None if not found
        """
        try:
            url = f"{self.base_url}/api/cached_article/{pmid}"
            params = {"fetch_if_missing": str(fetch_if_missing).lower()}

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("verified"):
                        logger.info(f"[MCP-to-MCP] Retrieved verified article PMID:{pmid}")
                        return data.get("data")
                    else:
                        logger.warning(f"[MCP-to-MCP] Article not marked as verified: {pmid}")
                        return data.get("data")

                elif response.status_code == 404:
                    logger.warning(f"[MCP-to-MCP] Article not found: PMID:{pmid}")
                    return None

                else:
                    logger.error(f"[MCP-to-MCP] HTTP error {response.status_code}: {response.text}")
                    return None

        except httpx.ConnectError:
            logger.error(
                f"[MCP-to-MCP] Cannot connect to pubmed-search API at {self.base_url}. "
                f"Is pubmed-search MCP running?"
            )
            return None
        except Exception as e:
            logger.error(f"[MCP-to-MCP] Error fetching article: {e}")
            return None

    def get_multiple_articles(
        self, pmids: List[str], fetch_if_missing: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple articles from pubmed-search cache.

        Args:
            pmids: List of PubMed IDs
            fetch_if_missing: If True, fetch missing articles from NCBI

        Returns:
            Dict mapping PMID to article metadata
        """
        try:
            url = f"{self.base_url}/api/cached_articles"
            params = {"pmids": ",".join(pmids), "fetch_if_missing": str(fetch_if_missing).lower()}

            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    found = data.get("found", {})
                    missing = data.get("missing", [])

                    if missing:
                        logger.warning(f"[MCP-to-MCP] Missing articles: {missing}")

                    logger.info(f"[MCP-to-MCP] Retrieved {len(found)}/{len(pmids)} articles")
                    return found
                else:
                    logger.error(f"[MCP-to-MCP] HTTP error {response.status_code}")
                    return {}

        except httpx.ConnectError:
            logger.error("[MCP-to-MCP] Cannot connect to pubmed-search API")
            return {}
        except Exception as e:
            logger.error(f"[MCP-to-MCP] Error: {e}")
            return {}

    def check_health(self) -> bool:
        """
        Check if pubmed-search API is available.

        Returns:
            True if API is healthy
        """
        try:
            url = f"{self.base_url}/health"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception:
            logger.debug("PubMed API health check failed", exc_info=True)
            return False

    def get_session_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get pubmed-search session summary.

        Returns:
            Session summary dict or None
        """
        try:
            url = f"{self.base_url}/api/session/summary"
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            logger.debug("Failed to get session summary", exc_info=True)
            return None

    def fetch_from_ncbi_direct(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch article metadata directly from NCBI E-utilities via requests.

        Fallback when the pubmed-search HTTP API is unavailable.
        Uses requests library which handles proxy + SSL correctly
        (unlike urllib/Biopython which may fail through certain proxies).

        Args:
            pmid: PubMed ID

        Returns:
            Article metadata dict, or None if not found
        """
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        }
        email = os.environ.get("ENTREZ_EMAIL", os.environ.get("PUBMED_EMAIL", ""))
        api_key = os.environ.get("NCBI_API_KEY", "")
        if email:
            params["email"] = email
        if api_key:
            params["api_key"] = api_key

        try:
            resp = requests.get(efetch_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"[NCBI-direct] Failed to fetch PMID:{pmid}: {e}")
            return None

        try:
            root = ET.fromstring(resp.text)
            article_el = root.find(".//PubmedArticle")
            if article_el is None:
                logger.warning(f"[NCBI-direct] No PubmedArticle found for PMID:{pmid}")
                return None

            medline = article_el.find("MedlineCitation")
            art = medline.find("Article")

            # Title
            title_el = art.find("ArticleTitle")
            title = title_el.text.rstrip(".") if title_el is not None and title_el.text else ""

            # Journal
            journal_el = art.find("Journal/Title")
            journal = journal_el.text if journal_el is not None else ""
            journal_abbrev_el = art.find("Journal/ISOAbbreviation")
            journal_abbrev = journal_abbrev_el.text if journal_abbrev_el is not None else ""

            # Year
            year_el = art.find("Journal/JournalIssue/PubDate/Year")
            year = year_el.text if year_el is not None else ""
            if not year:
                medline_year = art.find("Journal/JournalIssue/PubDate/MedlineDate")
                if medline_year is not None and medline_year.text:
                    year = medline_year.text[:4]

            # Volume / Issue / Pages
            vol_el = art.find("Journal/JournalIssue/Volume")
            volume = vol_el.text if vol_el is not None else ""
            iss_el = art.find("Journal/JournalIssue/Issue")
            issue = iss_el.text if iss_el is not None else ""
            pages_el = art.find("Pagination/MedlinePgn")
            pages = pages_el.text if pages_el is not None else ""

            # DOI
            doi = ""
            for eid in art.findall("ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = eid.text or ""
                    break

            # Authors
            authors = []
            authors_full = []
            for author_el in art.findall("AuthorList/Author"):
                last = author_el.find("LastName")
                initials_el = author_el.find("Initials")
                if last is not None and last.text:
                    ln = last.text
                    ini = initials_el.text if initials_el is not None else ""
                    authors.append(f"{ln} {ini}".strip())
                    authors_full.append({"last_name": ln, "initials": ini})

            # Abstract
            abstract_parts = []
            for abs_text in art.findall("Abstract/AbstractText"):
                label = abs_text.get("Label", "")
                text = "".join(abs_text.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

            # PMC ID
            pmc_id = ""
            for art_id in article_el.findall("PubmedData/ArticleIdList/ArticleId"):
                if art_id.get("IdType") == "pmc":
                    pmc_id = art_id.text or ""
                    break

            result = {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "authors_full": authors_full,
                "journal": journal,
                "journal_abbrev": journal_abbrev,
                "year": year,
                "volume": volume,
                "issue": issue,
                "pages": pages,
                "doi": doi,
                "abstract": abstract,
                "pmc_id": pmc_id,
                "_data_source": "ncbi_efetch_direct",
                "_verified": True,
            }

            logger.info(f"[NCBI-direct] Successfully fetched PMID:{pmid}: {title[:60]}")
            return result

        except Exception as e:
            logger.error(f"[NCBI-direct] Failed to parse XML for PMID:{pmid}: {e}")
            return None


# Singleton instance for convenience
_client: Optional[PubMedAPIClient] = None


def get_pubmed_api_client(
    base_url: Optional[str] = None, force_new: bool = False
) -> PubMedAPIClient:
    """
    Get or create the PubMed API client singleton.

    Args:
        base_url: Optional custom API URL
        force_new: If True, create a new instance

    Returns:
        PubMedAPIClient instance
    """
    global _client

    if _client is None or force_new:
        _client = PubMedAPIClient(base_url=base_url)

    return _client
