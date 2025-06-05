import aiohttp
from aiolimiter import AsyncLimiter
import asyncio
import json
from typing import Optional
class PubtatorClient:
    def __init__(self) -> None:
        self.base_url = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/"
        self._limiter = AsyncLimiter(3, 1)

    async def _rate_limited_request(self, url, session, json=True, **kwargs):
        async with self._limiter:
            async with session.get(url, **kwargs) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"API error: {resp.status} - {text}")
                return await resp.json() if json else await resp.text()
            
    async def find_entity(self, query:str, bioconcept:Optional[str]=None, limit:Optional[int]=10):
        """
        Query PubTator3 for identifiers given a free text bioconcept query,
        optionally filtering by concept type and limiting results.
        """

        url = self.base_url + f"entity/autocomplete/?query={query}"
        if bioconcept:
            url+= f'&concept={bioconcept}'
        if limit:
            url += f'&limit={limit}'

        # Use aiohttp for async HTTP requests
        async with aiohttp.ClientSession() as session:
            resp = await self._rate_limited_request(url, session, json=True)
            return json.dumps(resp)
    
                
    async def search_pubtator(self, query: str, relation: Optional[str] = "ANY", limit: Optional[int] = 10):
        """
        Query PubTator3 for relevant search results given a query.

        The query can be free text, entity ID (e.g., @CHEMICAL_remdesivir), or
        relations specifications (e.g., relations:ANY|@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms).

        Args:

            query (str): PubTator search query.
            relation(Optional[str]): relation of the two entities
            limit (Optional[int]): Maximum number of results (default 10, max 50).

        Returns:
            str: JSON string response from PubTator3 API.
        """
        # Ensure limit is respected (API max 50)
        safe_limit = min(50, limit if limit is not None else 10)
        if relation == "ANY" or relation == None:
            url = self.base_url + f"search/?text={query}&limit={safe_limit}"
        else:
            url = self.base_url + f"search/?text=relations:{relation}|{query}&limit={safe_limit}"

        async with aiohttp.ClientSession() as session:
            resp = await self._rate_limited_request(url, session, json=True)
            # Get basic article data for each article in the results
            # Collect PMIDs from the search results
            pmids = [str(art.get("pmid")) for art in resp.get('results', []) if art.get("pmid")]

            # Fetch abstracts using get_paper_text
            abstracts_map = {}
            if pmids:
                paper_text_resp = await self.get_paper_text(pmids=pmids, format="biocjson", full=False)
                # paper_text_resp is expected to be a dict with 'documents' key
                for doc in paper_text_resp['PubTator3']:
                    pmid = doc['pmid']
                    for passage in doc.get("passages", []):
                    # Try to get the abstract from passages
                        abstract = None
                        if passage.get("infons", {}).get("type") == "abstract":
                            abstract = passage.get("text")
                            break
                    abstracts_map[pmid] = abstract

            articles = []
            for art in resp.get('results', []):
                pmid = art.get("pmid")
                article = {
                    "pmid": pmid,
                    "title": art.get("title"),
                    "abstract": abstracts_map.get(pmid),
                    "journal": art.get("journal"),
                    "authors": art.get("authors", [])
                }
                articles.append(article)
            return json.dumps({
                "articles": articles,
                "facets": resp.get("facets", {}),
                "page_size": resp.get("page_size"),
                "current": resp.get("current"),
                "count": resp.get("count"),
                "total_pages": resp.get("total_pages")
            })
    

    async def get_paper_text(
        self,
        pmids: Optional[list[str]] = None,
        pmcids: Optional[list[str]] = None,
        format: str = "biocjson",
        full: Optional[bool] = True
    ):
        """
        get the abstract or full text a set of publications in a specified format.

        Args:
            pmids (Optional[list[str]]): List of PubMed IDs.
            pmcids (Optional[list[str]]): List of PubMed Central IDs.
            format (str): One of 'pubtator', 'biocxml', or 'biocjson'.
            full (Optional[bool]): For pmid export, set to True to request full text (biocxml or biocjson only).

        Returns:
            str: Raw response text in the requested format.
        """
        ALLOWED_FORMATS = ["pubtator", "biocxml", "biocjson"]
        if format not in ALLOWED_FORMATS:
            raise ValueError(f"Invalid format: {format}. Must be one of {ALLOWED_FORMATS}")

        if pmids and pmcids:
            raise ValueError("Only one of pmids or pmcids should be supplied.")

        if not pmids and not pmcids:
            raise ValueError("Either pmids or pmcids must be provided.")

        if pmids:
            pmid_str = ",".join(pmids)
            url = f"{self.base_url}publications/export/{format}?pmids={pmid_str}"
            if full is not None and format in ("biocxml", "biocjson"):
                if full:
                    url += f"&full=true"
        else:
            pmcid_str = ",".join(pmcids)
            url = f"{self.base_url}publications/pmc_export/{format}?pmcids={pmcid_str}"

        async with aiohttp.ClientSession() as session:
            resp = await self._rate_limited_request(url, session, json=True)

            return resp


    async def find_related_entities(
        self,
        entity_id: str,
        relation_type: str = None,
        entity_type: str = None
    ):
        """
        Query related entities (of a specific entity type) in a specific relation type.

        Args:
            entity_id (str): The entity ID (e.g., @CHEMICAL_remdesivir).
            relation_type (str, optional): The relation type, one of: treat, cause, cotreat,
                convert, compare, interact, associate, positive_correlate, negative_correlate,
                prevent, inhibit, stimulate, drug_interact.
            entity_type (str, optional): The type of related entities to retrieve. One of: gene, disease, chemical, variant.

        Returns:
            dict: The response from the PubTator3 API.
        """
        # Validate entity_type
        VALID_ENTITY_TYPES = {'gene', 'disease', 'chemical', 'variant'}
        VALID_RELATION_TYPES = {
            'treat', 'cause', 'cotreat', 'convert', 'compare', 'interact', 'associate',
            'positive_correlate', 'negative_correlate', 'prevent', 'inhibit', 'stimulate', 'drug_interact'
        }

        if relation_type:
            if relation_type not in VALID_RELATION_TYPES:
                raise ValueError(f"Invalid relation_type: {relation_type}. Must be one of {VALID_RELATION_TYPES}")
        else:
            relation_type = ''
        if entity_type:
            if entity_type not in VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}")

        url = f"{self.base_url}relations?e1={entity_id}&type={relation_type}&e2={entity_type}"
        async with aiohttp.ClientSession() as session:
            resp = await self._rate_limited_request(url, session, json=True)
            return json.dumps(resp)