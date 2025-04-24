import aiohttp
import json
from typing import Optional
class PubtatorClient:
    def __init__(self) -> None:
        self.base_url = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/"
    
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
            async with session.get(url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"PubTator3 API error: {resp.status} - {text}")
                data = await resp.json()
                return json.dumps(data)
    
                
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
            async with session.get(url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"PubTator3 API error: {resp.status} - {text}")
                data = await resp.json()
                return json.dumps(data)
    

    async def get_paper_text(
        self,
        pmids: Optional[list[str]] = None,
        pmcids: Optional[list[str]] = None,
        format: str = "biocjson",
        full: Optional[bool] = None
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
            async with session.get(url) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"PubTator3 API export error: {resp.status} - {text}")
                # For pubtator (plain text), return as text, for others, may be JSON or XML
                if format == "biocjson":
                    data =  await resp.json()
                else:
                    data = await resp.text()
                    raise ValueError("others format are not supported now.")

                return data
    # INSERT_YOUR_CODE
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

        params = {'e1': entity_id}
        if relation_type:
            if relation_type not in VALID_RELATION_TYPES:
                raise ValueError(f"Invalid relation_type: {relation_type}. Must be one of {VALID_RELATION_TYPES}")
            params['type'] = relation_type
        if entity_type:
            if entity_type not in VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}")
            params['e2'] = entity_type

        url = f"{self.base_url}relations"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"PubTator3 API relation error: {resp.status} - {text}")
                return await json.dumps(resp.json())