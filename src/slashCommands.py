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
import sqlite3


class Commands(Extension):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect("checklists.db")  # Create/connect to the database
        self.create_table()
        self.cancel_button = Button(
            style=ButtonStyle.DANGER,
            label="Cancel",
            custom_id="cancel",
        )

    def create_table(self):
        cursor = self.db.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS checklists (
                user_id INTEGER PRIMARY KEY,
                checklist_items TEXT
            )
        """
        )
        self.db.commit()

    @slash_command(name="checklist", description="Create or update a checklist")
    async def checklist(self, ctx: SlashContext):
        user_id = ctx.author.id
        checklist_items = self.load_checklist(user_id)
        await self.send_checklist_embed(ctx, checklist_items)

    def load_checklist(self, user_id):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT checklist_items FROM checklists WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        return row[0].split(",") if row else []

    def save_checklist(self, user_id, checklist_items):
        items_str = ",".join(checklist_items)
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO checklists (user_id, checklist_items) VALUES (?, ?)",
            (user_id, items_str),
        )
        self.db.commit()

    async def send_checklist_embed(self, ctx, checklist_items):
        embed = Embed(
            title=f"{ctx.author.display_name}'s Checklist",
            description="\n".join(
                [f"{i+1}. {item}" for i, item in enumerate(checklist_items)]
            ),
        )
        add_button = Button(
            style=ButtonStyle.PRIMARY,
            label="Add",
            custom_id="add_item",
        )
        complete_button = Button(
            style=ButtonStyle.SUCCESS,
            label="Complete",
            custom_id="complete_item",
        )
        delete_button = Button(
            style=ButtonStyle.DANGER,
            label="Delete",
            custom_id="delete_item",
        )
        buttons = ActionRow(add_button, complete_button, delete_button)

        await ctx.send(embeds=[embed], components=[buttons])

    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx
        user_id = ctx.author.id
        checklist_items = self.load_checklist(user_id)

        if ctx.custom_id == "add_item":
            await self.handle_add_item(ctx, user_id, checklist_items)
        elif ctx.custom_id == "delete_item":
            await self.handle_delete_item(ctx, user_id, checklist_items)
        elif ctx.custom_id == "complete_item":
            await self.handle_complete_item(ctx, user_id, checklist_items)

    async def handle_add_item(self, ctx: SlashContext, user_id, checklist_items):
        modal = Modal(
            ShortText(label="Enter the new item", custom_id="short_text"),
            title="Add a new item to your checklist",
        )

        try:
            await ctx.send_modal(modal=modal)
            modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
            user_input = modal_ctx.responses["short_text"]

            # Append the new item to the checklist_items list
            checklist_items.append(user_input)
            self.save_checklist(user_id, checklist_items)  # Save to the database

            await modal_ctx.defer()
            original_message = ctx.message
            await original_message.delete()
            await modal_ctx.delete()
            await self.send_checklist_embed(ctx, checklist_items)
        except TimeoutError:
            await ctx.send("Checklist timed out. Please try again.")
        except Exception as e:
            await ctx.send("Something went wrong. Please try again.")
            print(f"Error handling add_item modal: {e}")

    async def handle_complete_item(self, ctx, user_id, checklist_items):
        # iterate through the checklist items and display buttons for each item in the checklist
        checklistItemButtons = []
        for item in checklist_items:
            # If item is striked through, don't display it
            if "~~" in item:
                pass
            else:
                list_items = Button(
                    style=ButtonStyle.PRIMARY,
                    label=item,
                    custom_id=item,
                )
                checklistItemButtons.append(list_items)
        if not checklistItemButtons:
            await ctx.send("No items to complete.")
            return
        buttons = ActionRow(*checklistItemButtons, self.cancel_button)
        await ctx.send(components=[buttons])
        # when a button is clicked, strike through the item
        try:
            event: Component = await ctx.bot.wait_for(Component)
            # when cancel button is clicked, remove the buttons
            if event.ctx.custom_id == "cancel":
                await event.ctx.defer()
                buttons_message = event.ctx.message
                original_message = ctx.message
                await buttons_message.delete()
                await original_message.delete()
                await event.ctx.delete()
                await self.send_checklist_embed(ctx, self.load_checklist(user_id))

            if event.ctx.custom_id in checklist_items:
                # strike through the item
                item_index = checklist_items.index(event.ctx.custom_id)
                checklist_items[item_index] = f"~~{event.ctx.custom_id}~~"
                self.save_checklist(user_id, checklist_items)
                await event.ctx.defer()
                buttons_message = event.ctx.message
                original_message = ctx.message
                await buttons_message.delete()
                await original_message.delete()
                await event.ctx.delete()
                await self.send_checklist_embed(ctx, self.load_checklist(user_id))
        except TimeoutError:
            await ctx.send("Checklist timed out. Please try again.")
        except Exception as e:
            await ctx.send("Something went wrong. Please try again.")
            print(f"Error handling complete_item: {e}")

    async def handle_delete_item(self, ctx, user_id, checklist_items):
        # iterate through the checklist items and display buttons for each item in the checklist
        checklistItemButtons = []
        # if item is striked through, remove the ~~ from the item
        for item in checklist_items:
            display_label = item.replace("~~", "")
            list_items = Button(
                style=ButtonStyle.PRIMARY,
                label=display_label,
                custom_id=item,
            )
            checklistItemButtons.append(list_items)
        if not checklistItemButtons:
            await ctx.send("No items to delete.")
            return
        buttons = ActionRow(*checklistItemButtons, self.cancel_button)
        await ctx.send(components=[buttons])
        try:
            event: Component = await ctx.bot.wait_for(Component)
            # when cancel button is clicked, remove the buttons
            if event.ctx.custom_id == "cancel":
                await event.ctx.defer()
                buttons_message = event.ctx.message
                original_message = ctx.message
                await buttons_message.delete()
                await original_message.delete()
                await event.ctx.delete()
                await self.send_checklist_embed(ctx, self.load_checklist(user_id))

            # remove the item from the checklist
            if event.ctx.custom_id in checklist_items:
                checklist_items.remove(event.ctx.custom_id)
                self.save_checklist(user_id, checklist_items)
                await event.ctx.defer()
                buttons_message = event.ctx.message
                original_message = ctx.message
                await buttons_message.delete()
                await original_message.delete()
                await event.ctx.delete()
                await self.send_checklist_embed(ctx, self.load_checklist(user_id))
        except TimeoutError:
            await ctx.send("Checklist timed out. Please try again.")
        except Exception as e:
            await ctx.send("Something went wrong. Please try again.")
            print(f"Error handling delete_item: {e}")


def setup(bot):
    Commands(bot)
