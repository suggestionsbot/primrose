import disnake


class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value: bool = False

    @disnake.ui.button(label="Confirm", style=disnake.ButtonStyle.green)
    async def confirm(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_message("Confirming...", ephemeral=True)
        self.value = True
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.grey)
    async def cancel(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        await inter.response.send_message("Cancelling...", ephemeral=True)
        self.value = False
        self.stop()
