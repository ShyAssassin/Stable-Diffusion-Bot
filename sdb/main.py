import os

# we load all cogs assuming we are in the sdb root directory but if we aren't we get nasty errors
# because cogs are loaded relative to the current working directory,
# so we just change directory to sdb if we aren't already in it
if os.pardir != "sdb":
    os.chdir("sdb")
from Core.bot import SDB
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    sdb = SDB()
    sdb.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
