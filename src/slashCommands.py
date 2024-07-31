from interactions import (
    slash_command,
    SlashContext,
    Extension,
    Button,
    ButtonStyle,
    ActionRow,
    Embed,
    listen,
    Modal,
    ShortText,
    ModalContext,
)
from interactions.api.events import Component


class Commands(Extension):
    checklists = {}  # Store checklists

    @slash_command(name="checklist", description="Create or update a checklist")
    async def checklist(self, ctx: SlashContext):
        user_id = ctx.author.id
        if user_id not in self.checklists:
            self.checklists[user_id] = []

        await self._send_checklist_embed(ctx, user_id)

    async def _send_checklist_embed(self, ctx, user_id):
        embed = Embed(
            title=f"{ctx.author.display_name}'s Checklist",
            description="\n".join(
                [f"{i+1}. {item}" for i, item in enumerate(self.checklists[user_id])]
            ),
        )

        add_button = Button(
            style=ButtonStyle.PRIMARY,
            label="Add Item",
            custom_id="add_item",
        )
        complete_button = Button(
            style=ButtonStyle.SUCCESS,
            label="Complete Item",
            custom_id="complete_item",
        )
        buttons = ActionRow(add_button, complete_button)

        await ctx.send(embeds=[embed], components=[buttons])

    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx
        user_id = ctx.author.id

        if ctx.custom_id == "add_item":
            await self._handle_add_item(ctx, user_id)
        elif ctx.custom_id == "complete_item":
            # ... (handle completion logic here)
            pass

    async def _handle_add_item(self, ctx: SlashContext, user_id):
        modal = Modal(
            ShortText(label="Enter the new item", custom_id="short_text"),
            title="Add a new item to your checklist",
        )

        try:
            await ctx.send_modal(modal=modal)
            modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
            short_text = modal_ctx.responses["short_text"]
            self.checklists[user_id].append(short_text)
            await modal_ctx.defer()
            await modal_ctx.delete()  # Delete the defer response message
            await self._send_checklist_embed(ctx, user_id)
        except TimeoutError:
            await ctx.send("Checklist timed out. Please try again.")
        except Exception as e:
            await ctx.send("Something went wrong. Please try again.")
            print(f"Error handling add_item modal: {e}")


def setup(bot):
    Commands(bot)


# handle the Complete Item button
# implement a db to store the checklists
# add a Delete Item button
