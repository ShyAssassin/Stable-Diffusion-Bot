import os
import disnake
from disnake.ext import commands
from typing import Union
from .config import SDBConfig


class SDB(commands.Bot):
    def __init__(self, **options):
        self.Ready: bool = False
        self.config: SDBConfig = SDBConfig()
        self.config.load()
        # NOTE: If folder structure ever changed update this
        self.CogPath: str = os.path.join("Core", "Cogs")
        # fmt: off
        super().__init__(
            reload=True,
            help_command=None,
            command_prefix=self.config.command_prefix,
            case_insensitive=True,
            intents=disnake.Intents.all(),
            **options
        )
        # fmt: on

    async def on_ready(self):
        # on_ready is called more than once sometimes
        if not self.Ready:
            print(self.generate_invite())
            print(f"Bot connect to {self.user}")
            print("Loading Extensions...")
            # Dynamically load all cogs
            for cog in os.listdir(self.CogPath):
                if not cog.startswith("_") and cog.endswith(".py"):
                    CurrentCogPath = str(os.path.join(self.CogPath, cog))
                    # TODO: this doesn't work on linux because linux uses / instead of \
                    CurrentCogModule = CurrentCogPath.replace("\\", ".")[:-3]
                    self.load_extension(CurrentCogModule)
                    print(f"Loaded Extension: sdb.{CurrentCogModule}")
            print("All Extension Loaded!")
            self.Ready = True

    def generate_invite(self, permissions: Union[int, disnake.Permissions] = 8) -> str:
        if isinstance(permissions, int):
            permission_value = permissions
        else:
            permission_value = permissions.value

        return f"https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions={permission_value}&scope=bot%20applications.commands"

    def run(self):
        super().run(os.getenv("DISCORD_TOKEN"))
