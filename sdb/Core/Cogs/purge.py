import disnake
from disnake.ext import commands
from Core import SDB


# god this whole class is a mess but it works
# TODO: Clean this up, this entire thing was written in like 10 minutes at 2am
class Purge(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    def is_bot(self, message):
        return message.author == self.bot.user

    def is_failed_command(self, message):
        return (
            message.interaction is not None and message.interaction.response is None or message.interaction.response.is_done() is False
        )

    def is_slash_command(m):
        return isinstance(m, disnake.Message) and m.type == disnake.MessageType.application_command

    @commands.slash_command(name="purge-failed", description="Purge all failed slash command responses from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def PurgeFailed(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=None, check=self.is_bot)
        deleted = await interaction.channel.purge(check=lambda m: self.is_slash_command(m) and self.is_failed_command(m))
        await interaction.edit_original_message(f"Deleted {len(deleted)} failed slash commands.")

    @commands.slash_command(name="purge", description="Purge a specified amount of messages from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def Purge(self, interaction: disnake.CommandInteraction, amount: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount)
        await interaction.edit_original_message(content=f"Purged {amount} messages from {interaction.channel.mention}")

    @commands.slash_command(name="purge-all", description="Purge all content from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def PurgeAll(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=None)
        await interaction.edit_original_message(content=f"Purged {len(deleted)} messages from {interaction.channel.mention}")

    @commands.slash_command(name="purge-bot", description="Purge a specified amount of bot messages from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def PurgeBot(self, interaction: disnake.CommandInteraction, amount: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount, check=self.is_bot)
        await interaction.edit_original_message(content=f"Purged {amount} messages from {interaction.channel.mention}")

    @commands.slash_command(name="purge-bot-all", description="Purge all bot messages from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def PurgeBotAll(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=None, check=self.is_bot)
        await interaction.edit_original_message(content=f"Purged {len(deleted)} messages from {interaction.channel.mention}")

    @commands.command(name="purge")
    async def PurgeCTX(self, ctx: commands.Context):
        await ctx.reply(content=f"Use the slash command!")


def setup(bot: SDB):
    bot.add_cog(Purge(bot))
