import os

# change working directory to the root of the project
# yea yea yea i know i should make sdb a package so we can use relative imports
# but i'm lazy and this works for now
if os.pardir != os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))

from Core.bot import SDB
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    sdb = SDB()
    sdb.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
