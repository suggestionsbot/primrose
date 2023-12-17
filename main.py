import asyncio
import logging
import os
import secrets

import disnake
from disnake.ext import commands
from disnake.ext.commands import InteractionBot

from status_views import Confirm

logging.basicConfig(level=logging.DEBUG)


async def main():
    channel_id = 602332642456764426
    status_events: dict[str, (disnake.Embed, int, int)] = {}
    colors: dict[str, hex] = {
        "On going": 0xF44336,
        "Upcoming": 0xBCBCBC,
        "Resolved": 0x8FCE00,
    }
    bot: InteractionBot = InteractionBot(intents=disnake.Intents.default())

    @bot.event
    async def on_ready():
        channel = await bot.fetch_channel(602332642456764426)
        async for message in channel.history(limit=25):
            if not message.embeds:
                continue

            embed: disnake.Embed = message.embeds[0]
            try:
                _, code = embed.footer.text.split(": ")
            except:
                continue

            status_events[code] = (embed, message.id, channel.id)

        print("Bot is ready")

    @bot.slash_command()
    async def create_status_event(
        interaction: disnake.GuildCommandInteraction,
        outage_type: str = commands.Param(choices=["Unplanned", "Maintenance"]),
        current_status: str = commands.Param(
            choices=["On going", "Upcoming", "Resolved"], default="On going"
        ),
    ):
        """Create and publish a new status message."""
        await interaction.response.send_modal(
            title="Status update",
            custom_id="status_modal",
            components=[
                disnake.ui.TextInput(
                    label="Outage description",
                    placeholder="A sentence or few tldr'ing whats happening",
                    custom_id="desc",
                    style=disnake.TextInputStyle.paragraph,
                ),
                disnake.ui.TextInput(
                    label="Affected products",
                    placeholder="Whats affected by this outage",
                    custom_id="products",
                    style=disnake.TextInputStyle.paragraph,
                ),
            ],
        )
        try:
            modal_inter: disnake.ModalInteraction = await bot.wait_for(
                "modal_submit",
                check=lambda i: i.custom_id == "status_modal"
                and i.author.id == interaction.author.id,
                timeout=600,
            )
        except asyncio.TimeoutError:
            # The user didn't submit the modal in the specified period of time.
            # This is done since Discord doesn't dispatch any event for when a modal is closed/dismissed.
            return

        desc = modal_inter.text_values["desc"]
        products = modal_inter.text_values["products"]
        code = str(secrets.token_urlsafe(4))
        embed: disnake.Embed = (
            disnake.Embed(
                title=f"{outage_type} outage",
                description=f"{desc}\n\n**Affected products**\n{products}",
                timestamp=disnake.utils.utcnow(),
                colour=colors[current_status],
            )
            .add_field(name="Current status", value=current_status)
            .set_footer(text=f"Status code: {code}")
        )

        confirm_view = Confirm()
        await modal_inter.send(
            content="Would you like to publish this?",
            embed=embed,
            view=confirm_view,
            ephemeral=True,
        )
        await confirm_view.wait()
        if confirm_view.value is False:
            await modal_inter.send(
                "Aight, I wont send that status update.", ephemeral=True
            )
            return

        channel = await bot.fetch_channel(channel_id)
        message: disnake.Message = await channel.send(embed=embed)
        # await message.publish()
        await modal_inter.send("Published status update", ephemeral=True)
        status_events[code] = (embed, message.id, channel.id)

    @bot.slash_command()
    async def update_status_event(
        interaction: disnake.CommandInteraction,
        status_code: str,
        new_status: str = commands.Param(
            choices=["On going", "Upcoming", "Resolved"],
        ),
    ):
        """Update a status event embeds"""
        await interaction.response.defer(ephemeral=True)
        embed, message_id, v_channel_id = status_events[status_code]
        chan = await bot.fetch_channel(v_channel_id)
        message = await chan.fetch_message(message_id)
        embed: disnake.Embed = embed
        embed.fields[0].value = new_status
        embed.colour = colors[new_status]
        await message.edit(embed=embed)
        await interaction.send("I've edited that status event for you.", ephemeral=True)

    @update_status_event.autocomplete("status_code")
    async def get_sid_for(
        interaction: disnake.ApplicationCommandInteraction,
        user_input: str,
    ):
        values = list(status_events.keys())

        possible_choices = [v for v in values if user_input.lower() in v.lower()]

        if len(possible_choices) > 25:
            return []

        return possible_choices

    await bot.start(os.environ["TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
