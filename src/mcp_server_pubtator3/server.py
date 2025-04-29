import asyncio
import json
import logging
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server
from .pubtator_client import PubtatorClient

app = Server("mcp-server-pubtator3")
pubtator_client = PubtatorClient()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server-pubtator3")
@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    """List available prompts for interacting with Pubtator."""
    return [
        types.Prompt(
            name = "relation_prover",
            description="Prove whether two the two biology ontologies have the certain relations",
            arguments=[
                types.PromptArgument(
                    name="entity1",
                    description="The first biology ontology",
                    required=True
                ),
                types.PromptArgument(
                    name="entity2",
                    description="The second biology ontology",
                    required=True
                ),
                types.PromptArgument(
                    name="relation",
                    description="The relation between the two entities",
                    required=True
                ),
            ] 
        )
    ]
@app.get_prompt()
async def get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    if name != "relation_prover":
        raise ValueError(f"Prompt not found: {name}")

    if name == "relation_prover":
        entity1 = arguments.get("entity1") if arguments else ""
        entity2 = arguments.get("entity2") if arguments else ""
        relation = arguments.get("relation") if arguments else ""
        return types.GetPromptResult(
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""You are a specialized AI Agent focused on biomedical literature analysis from pubmed. Your task is to evaluate and validate whether a biological relationship between two entities can be semantically supported by scientific literature.

Step-by-step process:

1. Extract the minimal keyword (MeSH Term) from the pair provided to search scientific literature—do not use the relationship itself as the keyword.
3. Begin by reviewing abstracts only:
   - If an abstract contains a direct or semantically implied connection between the two entities, then proceed to review the full text to confirm and strengthen the evidence.
   - If no abstract shows any semantic link, halt the search and report that no credible evidence exists.
4. If the minimal keywords yield no results, refine your query by subtracting elements from the original keyword set—removing non-essential words using close synonyms or semantically equivalent phrases without adding any new terms (e.g., using the gene name or function name without additional descriptors).
5. Apply semantic reasoning to evaluate whether the intended relationship exists, even if the wording does not exactly match.

For any paper that supports the relationship:
- Report the **title and PMID**.
- Extract a **exact sentence** from the abstract or full text that supports the connection.


you must obey the following response format strictly:

# Search Strategy and Reasoning
"Insert your keyword query logic and how you reasoned through the abstract/full text here"

# literature evidence
## "Insert title and PMID here"
"Insert the exact sentence from the abstract or full text that semantically supports the connection between the two biological entities here"

Answer: <True/False> 

Prove whether there is literature evidence for the pair:
'{entity1}' and '{entity2}' with relation '{relation}'. "
"""
                    )
                )
            ]
        )

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools for interacting with Pubtator."""
    return [
        types.Tool(
            name="find_entity",
            description="""Find the identifier(s) for a specific bioconcept using a free text query.

Use this tool to look up identifiers for biomedical concepts, such as diseases or genes. Optionally, you can restrict by concept type and limit the number of results.

- The `query` parameter is required and should be the free text of the concept you want to look up (e.g. "breast cancer", "BRCA1").
- The `concept` parameter is optional and can be used to restrict results to either 'disease','gene', 'chemical' or 'varient'.
- The `limit` parameter is optional and restricts how many identifier results are returned (default is 10, max 50).

Examples:
- Find entity for "diabetes":
  query = "diabetes"
- Find gene entity for "BRCA1":
  query = "BRCA1", concept = "gene"
- Find up to 5 disease entities for "cancer":
  query = "cancer", concept = "disease", limit = 5
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free text for the bioconcept to look up (e.g. 'breast cancer', 'BRCA1')"
                    },
                    "bioconcept": {
                        "type": "string",
                        "description": "Type of bioconcept to restrict to. Choose from 'disease','gene','chemical' or 'variant'. (optional)",
                        "enum": ["disease", "gene", 'chemical', 'variant']
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of identifiers to return (default: 10, max: 50). (optional)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),

        types.Tool(
            name="search_pubtator",
            description="""User can query through this API for retrieving the relevant search results returned by PubTator3 given a query in these forms:
- Free text (e.g., "cancer therapy")
- Entity ID via “Find Entity ID” (e.g., @CHEMICAL_remdesivir)
- Relations between two entities (e.g., @CHEMICAL_Doxorubicin|@DISEASE_Neoplasms)
- Relations between an entity and entities of a specific type (e.g., @CHEMICAL_Doxorubicin|DISEASE)

Users can also limit the number of results via the 'limit' parameter (optional).
Examples:
- Search by keyword:
  query = "cancer therapy"
- Search by entity ID:
  query = "@GENE_BRCA1"
- Search by relation between two entities:
  query = "@CHEMICAL_Doxorubicin|@DISEASE_Neoplasms"
- Search by relation between entity and entity type:
  query = "@CHEMICAL_Doxorubicin|DISEASE"
This returns relevant PubTator3 search results for your query.
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query string to search PubTator3 (use free text, entity ID)."
                    },
                    # "relation": {
                    #     "type": "string",
                    #     "description": "Relation type to filter search by. Choose from: 'treat', 'cause', 'cotreat', 'convert', 'compare', 'interact', 'associate', 'positive_correlate', 'negative_correlate', 'prevent', 'inhibit', 'stimulate', 'drug_interact'. (optional)",
                    #     "enum": [
                    #         "treat",
                    #         "cause",
                    #         "cotreat",
                    #         "convert",
                    #         "compare",
                    #         "interact",
                    #         "associate",
                    #         "positive_correlate",
                    #         "negative_correlate",
                    #         "prevent",
                    #         "inhibit",
                    #         "stimulate",
                    #         "drug_interact",
                    #         "ANY"
                    #     ],
                    #     "default": "ANY"
                    # },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 10, max: 50). (optional)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_paper_text",
            description="""Retrieve  text of one or more articles from Pubtator Central using either PMID(s) or PMCID(s).

Full texts are available in BioC XML or BioC JSON formats.
If a requested paper is not available in full text, the system responds with a message explaining why (e.g., not in PMC, access restricted).
Input parameters:
- pmids: A string or list of PubMed IDs. Use this to retrieve by PMID.
- pmcids: A string or list of PubMed Central IDs. Use this to retrieve by PMCID.
- format: Output format; one of "biocxml" or "biocjson" (default: "biocjson").
- full: [PMID only] Set to true to request the full text (default: true for pmid queries).
Returns:
- The full text(s) in the selected format, or
- A message if full text is not available.
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "pmids": {
                        "type": ["string", "array"],
                        "items": {"type": "string"},
                        "description": "PubMed ID or list of IDs (PMID)."
                    },
                    "pmcids": {
                        "type": ["string", "array"],
                        "items": {"type": "string"},
                        "description": "PubMed Central ID or list of IDs (PMCID)."
                    },
                    "format": {
                        "type": "string",
                        "enum": ["biocxml", "biocjson"],
                        "description": "Export format: 'biocxml' or 'biocjson'. Default is 'biocjson'.",
                        "default": "biocjson"
                    },
                    "full": {
                        "type": "boolean",
                        "description": "(For PMID queries) Whether to request full text articles. Default is true.",
                        "default": True
                    }
                },
            }
        ),
    types.Tool(
        name="find_related_entities",
        description="""
Passing a specific entityId (via “Find Entity ID”) to e1, relation_type to type (optional), and entity_type to e2 (optional) to query related entities (of a specific entity type) in a specific relation type.

Entity types include: gene, disease, chemical, and variant.
Available relation types: treat, cause, cotreat, convert, compare, interact, associate, positive_correlate, negative_correlate, prevent, inhibit, stimulate, drug_interact.

Example:
https://www.ncbi.nlm.nih.gov/research/pubtator3-api/relations?e1=entityId&type=relation_type(OPTIONAL)&e2=entity_type(OPTIONAL)
""",
        inputSchema={
            "type": "object",
            "properties": {
                "e1": {
                    "type": "string",
                    "description": "Entity ID to start from. Obtainable via 'Find Entity ID'."
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "treat", "cause", "cotreat", "convert", "compare", "interact",
                        "associate", "positive_correlate", "negative_correlate", "prevent",
                        "inhibit", "stimulate", "drug_interact"
                    ],
                    "description": "Relation type to filter for. Optional."
                },
                "e2": {
                    "type": "string",
                    "enum": ["gene", "disease", "chemical", "variant"],
                    "description": "Entity type of related entities to query for. Optional."
                }
            },
            "required": ["e1"]
        }
    )
    ]

@app.call_tool()
async def fetch_tool(name:str, argument:dict) -> list[types.TextContent]:
    try:
        logger.info(f"Received tool call: {name} with arguments: {json.dumps(argument)}")
        if name == 'find_entity':
            if "query" not in argument:
                logger.error("Missing required argument: query")
                return [types.TextContent(
                    type="text",
                    text="Missing required argument: query",
                    isError=True
                )]
            query = argument["query"]
            if 'bioconcept' in argument:
                bioconcept = argument['bioconcept']
            else:
                bioconcept = None
            if 'limit' in argument:
                limit = argument['limit']
            else:
                limit = 10
            logger.info(f"Processing search with query: {query}, limit: {limit}, bioconcept: str{bioconcept}")
            results = await pubtator_client.find_entity(query, bioconcept=bioconcept, limit=limit)
            return [
                types.TextContent(type='text', text=results)
            ]
        
        if name == 'search_pubtator':
            if "query" not in argument:
                logger.error("Missing required argument: query")
                return [types.TextContent(
                    type="text",
                    text="Missing required argument: query",
                    isError=True
                )]
            query = argument["query"]
            limit = argument.get("limit", 10)
            # relation = argument.get("relation", "ANY")
            logger.info(f"Processing PubTator search with query: {query}, limit: {limit}")
            
            results = await pubtator_client.search_pubtator(query, limit=limit)
            return [
                types.TextContent(type='text', text=results)
            ]
        if name == "get_paper_text":
            # Required: either pmids or pmcids must be provided in the argument
            pmids = argument.get("pmids")
            pmcids = argument.get("pmcids")
            format_ = argument.get("format", "biocjson")
            full = argument.get("full", None)

            if not pmids and not pmcids:
                logger.error("Missing required argument: either 'pmids' or 'pmcids' must be provided.")
                return [types.TextContent(
                    type="text",
                    text="Missing required argument: either 'pmids' or 'pmcids' must be provided.",
                    isError=True
                )]
            try:
                data = await pubtator_client.get_paper_text(
                    pmids=pmids,
                    pmcids=pmcids,
                    format=format_,
                    full=full
                )
            # If the requested format is "biocjson", extract only the passage text and combine it for output

                parsed = data
                passages = []
                # PubTator3: top level key, list of documents
                if "PubTator3" in parsed:
                    for doc in parsed["PubTator3"]:
                        # Each doc has "passages" field: list of dicts with "text"
                        for passage in doc.get("passages", []):
                            text = passage.get("text")
                            if text:
                                passages.append(text)
                # Final output is all passage texts joined with double-newlines
                data = "\n\n".join(passages)
                return [
                    types.TextContent(
                        type='text',
                        text = data
                    )
                ]
            except Exception as e:
                logger.exception("Failed to retrieve paper text")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error retrieving paper text: {str(e)}",
                        isError=True
                    )
                ]
    
        if name == "find_related_entities":
            entity_id = argument.get("entity_id")
            relation_type = argument.get("relation_type", None)
            entity_type = argument.get("entity_type", None)

            if not entity_id:
                logger.error("Missing required argument: 'entity_id' must be provided.")
                return [types.TextContent(
                    type="text",
                    text="Missing required argument: 'entity_id' must be provided.",
                    isError=True
                )]

            try:
                result_json = await pubtator_client.find_related_entities(
                    entity_id=entity_id,
                    relation_type=relation_type,
                    entity_type=entity_type
                )
                # Return result in pretty-printed JSON
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result_json, indent=2) if not isinstance(result_json, str) else result_json
                )]
            except Exception as e:
                logger.exception("Failed to retrieve related entities")
                return [types.TextContent(
                    type="text",
                    text=f"Error retrieving related entities: {str(e)}",
                    isError=True
                )]
    except Exception as e:
        logger.exception(f"Error in call_tool ({name})")
        return [types.TextContent(
            type="text",
            text=f"Error processing request: {str(e)}",
            isError=True
        )]



async def main():
    async with stdio_server() as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )



