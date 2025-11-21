import discord
from discord import app_commands
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="cooldown",
        description="Set a cooldown on a channel."
    )
    async def cooldown(
        self,
        interaction: discord.Interaction,
        seconds: int
    ):
        """Sets a cooldown on the current channel."""
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "You do not have permission to manage channels.",
                ephemeral=True
            )
            return

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "This command can only be used in text channels.",
                ephemeral=True
            )
            return

        await channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(
            f"Set a cooldown of {seconds} seconds on this channel.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Utils(bot))
