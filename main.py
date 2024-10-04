import discord
from discord import app_commands
import re
import asyncio
import json

# Read the config from config.json
with open('config.json') as f:
    config = json.load(f)
TOKEN = config['token']
ADMIN_ROLE_ID = config.get('AdminID') 

# Define a dictionary of color names to hex codes
COLOR_NAMES = {
    "red": 0xED4245,
    "blue": 0x3498DB,
    "green": 0x57F287,
    "yellow": 0xFEE75C,
    "purple": 0x9B59B6,
    "orange": 0xE67E22,
    "black": 0x23272A,
    "white": 0xFFFFFF,
    "pink": 0xFFC0CB,
    "teal": 0x1ABC9C,
    "gold": 0xF1C40F,
    "navy": 0x34495E,
}

class EmbedCreator(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = EmbedCreator()

def is_authorized(interaction: discord.Interaction):
    if not ADMIN_ROLE_ID:
        return True  # If no role ID is set, allow all users
    return interaction.user.get_role(int(ADMIN_ROLE_ID)) is not None

@client.tree.command(name="embed", description="Create a custom embed")
@app_commands.describe(
    title="The title of the embed (can include a link using [Text](URL) format)",
    description="The main content of the embed (use \\n for new lines)",
    color="The color of the embed (hex code or color name)",
    thumbnail="URL of the thumbnail image",
    footer="Footer text (optional)",
    image="URL of the main image (optional)"
)
async def create_embed(interaction: discord.Interaction, title: str, description: str, color: str, 
                       thumbnail: str, footer: str = None, image: str = None):
    
    if not is_authorized(interaction):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    # Process color input
    if color.lower() in COLOR_NAMES:
        embed_color = COLOR_NAMES[color.lower()]
    elif re.match(r'^#?(?:[0-9a-fA-F]{3}){1,2}$', color):
        color = color.lstrip('#')
        embed_color = int(color, 16)
    else:
        await interaction.response.send_message("Invalid color format. Please use a hex code (e.g., #FF0000) or a valid color name.", ephemeral=True)
        return

    # Validate thumbnail URL
    if not thumbnail.startswith(('http://', 'https://')):
        await interaction.response.send_message("Invalid thumbnail URL. Please provide a valid http or https URL.", ephemeral=True)
        return

    # Process title for hyperlink
    title_text = title
    title_url = None
    link_match = re.match(r'\[(.+?)\]\((.+?)\)', title)
    if link_match:
        title_text = link_match.group(1)
        title_url = link_match.group(2)

    # Process description for new lines
    description = description.replace('\\n', '\n')

    # Create embed
    embed = discord.Embed(
        title=title_text[:256],  # Enforce character limit
        description=description[:4096],  # Enforce character limit
        color=embed_color,
        url=title_url
    )

    embed.set_thumbnail(url=thumbnail)
    
    if footer:
        embed.set_footer(text=footer[:2048])  # Enforce character limit
    if image:
        embed.set_image(url=image)

    # Create buttons for actions
    preview_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Preview", custom_id="preview")
    send_button = discord.ui.Button(style=discord.ButtonStyle.success, label="Send", custom_id="send")
    cancel_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Cancel", custom_id="cancel")

    async def button_callback(interaction: discord.Interaction):
        if not is_authorized(interaction):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return
        
        if interaction.data["custom_id"] == "preview":
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif interaction.data["custom_id"] == "send":
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("Embed sent successfully!", ephemeral=True)
        elif interaction.data["custom_id"] == "cancel":
            await interaction.response.send_message("Embed creation cancelled.", ephemeral=True)

    for button in [preview_button, send_button, cancel_button]:
        button.callback = button_callback

    view = discord.ui.View()
    view.add_item(preview_button)
    view.add_item(send_button)
    view.add_item(cancel_button)

    await interaction.response.send_message("Embed created. What would you like to do?", view=view, ephemeral=True)

@create_embed.error
async def embed_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRequiredArgument):
        await interaction.response.send_message(f"Missing required argument: {error.param.name}", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

# Run the bot
client.run(TOKEN)