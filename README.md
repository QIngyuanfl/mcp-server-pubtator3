# Pubtator MCP Server

This project provides an async Python server for interacting with the [PubTator3 API](https://www.ncbi.nlm.nih.gov/research/pubtator3-api/). It exposes multiple biomedical text-mining tools compatible with the MCP agent protocol, supporting tasks such as entity lookup, biomedical literature search, and text extraction from PubMed/PMC articles.


## Features

- **Entity Autocomplete:** Find biomedical entities (genes, diseases, chemicals, variants) using free-text queries.
- **Literature Search:** Search the PubTator3 database using keywords, entity IDs, or entity relations.
- **Article Retrieval:** Download and extract text from PubMed/PMC articles in multiple formats.
- **Find Related Entities:** Query for entities related to a given identifier via customizable relation and type filters.
- **Async and Fast:** Uses `aiohttp` for non-blocking HTTP requests; designed for integration into broader MCP environments.

## Available Tools

The server provides the following tools to interact with the PubTator3 API, accessible via the MCP protocol. These tools allow programmatic access to biomedical concept lookup, literature search, full-text extraction, and entity relation discovery.

### 1. `find_entity`
- **Purpose:** Find the identifier(s) for a specific bioconcept using a free text query.
- **Input:**  
  - `query` (string, required): Free text of the concept to look up (e.g. "breast cancer", "BRCA1").
  - `bioconcept` (string, optional): Restrict results to a concept type: one of `'disease'`, `'gene'`, `'chemical'`, `'variant'`.
  - `limit` (integer, optional): Maximum number of results (default 10, max 50).
- **Returns:**  
  A list of matching entities, each with PubTator identifiers, labels, and concept types.

### 2. `search_pubtator`
- **Purpose:** Search for relevant PubMed/PMC articles in PubTator3 using flexible queries.
- **Input:**  
  - `query` (string, required): Free text, PubTator concept ID, or a relations query.
  - `relation` (string, optional): Specific relation type (default `'ANY'`).
  - `limit` (integer, optional): Number of results to retrieve (default 10, max 50).
- **Returns:**  
  A JSON list including article IDs and brief summaries.

### 3. `get_paper_text`
- **Purpose:** Download and extract the text content from a PubMed or PMC article.
- **Input:**  
  - `pmid` or `pmcid` (string, required): Article identifier (PubMed ID or PMC ID).
- **Returns:**  
  The plain text content of the article if available.

### 4. `find_related_entities`
- **Purpose:** Find entities related to a specific PubTator entity, filtered by relation type or entity type.
- **Input:**  
  - `entity_id` (string, required): The PubTator entity ID to query (e.g., `@GENE_BRCA1`).
  - `relation_type` (string, optional): Restrict relations by type (e.g., `'interacts_with'`, `'associated_with'`).
  - `entity_type` (string, optional): Restrict related entities to a concept type.
- **Returns:**   
  A pretty-printed JSON with related entity IDs and relation details.

---

Each tool's full input schema, description, and examples are provided in the `list_tools` endpoint within `server.py`.  
Use these tools to integrate sophisticated PubTator3-powered biomedical knowledge access in compatible platforms or agents.

## Installation

1. **Installation** 3.10+ and required libraries (see below).
   ```bash
   pip install mcp-server-pubtator3
   ```
2. **Run the server:**
   ```bash
   mcp-server-pubtator3
   ```
   or
   ```bash
   uv run mcp-server-pubtator3
   ```


