import sys
import asyncio

from .server import main

sys.exit(asyncio.run(main()))