import asyncio
from . import server

async def main():
    """Main entry point for the package."""
    asyncio.run(server.main())

__version__ = "0.1.0"