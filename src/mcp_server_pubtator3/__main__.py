import sys
import asyncio

from .server import main as async_main
def main():
    sys.exit(asyncio.run(async_main()))

if __name__ == '__main__':
    main()