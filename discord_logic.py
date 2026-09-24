import discord
import json
import asyncio
from discord.ext import commands


class DiscordSelfBot:
    def __init__(self):
        """
        Initialize the Discord self bot with configuration and setup.
        Loads config from config.json and sets up the bot with required intents.
        """
        # Load configuration from JSON file

        self.config = self._load_config()
        self.token = self.config.get('credentials', {}).get('Token', '')
        self.prefix = '!'

        # Setup bot
        intents = discord.Intents.all()
        self.client = commands.Bot(
            command_prefix=self.prefix,
            intents=intents,
            self_bot=True
        )
        self.client.remove_command("help")

        # Setup events and commands
        self._setup_events()
        self._setup_commands()

    def _load_config(self) -> dict:
        """
        Load configuration from config.json file.
        Returns:
            dict: Configuration dictionary
        """
        try:
            with open("config.json") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("config.json not found")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in config.json")

    async def _fetch_message_selfbot(self, channel, message_id):
        """Self-bot compliant replacement for fetch_message()"""
        # 1. Check local cache first
        for msg in self.client.cached_messages:
            if msg.id == message_id:
                return msg

        # 2. Fall back to channel.history (allowed for user tokens)
        try:
            async for msg in channel.history(limit=10, around=discord.Object(id=message_id)):
                if msg.id == message_id:
                    return msg
        except Exception as e:
            print(f"Error reading history for target message: {e}")
        return None

    def _setup_events(self):
        """
        Setup event handlers for the bot.
        Uses decorator pattern to register events with the client.
        When the bot is running, we have two threads:

        The main thread running the GUI
        A separate thread running the Discord bot's event loop
        """

        @self.client.event
        async def on_ready():
            print(f"Logged in as {self.client.user.name}")

        @self.client.event
        async def on_message(message):
            await self.client.process_commands(message)

            # source_channel_ids = [1104477384838758633]
            source_channel_ids = [1259607738040979489]  # test general
            # destination_channel_id = 1331274153638232231
            destination_channel_id = 1338207422694559747  # test output

            if message.channel.id in source_channel_ids:
                try:
                    message_to_process = message

                    # Handle referenced/replied messages using self-bot history search
                    if hasattr(message, 'reference') and message.reference and message.reference.message_id:
                        ref_channel = self.client.get_channel(message.reference.channel_id)
                        if ref_channel:
                            fetched_msg = await self._fetch_message_selfbot(ref_channel, message.reference.message_id)
                            if fetched_msg:
                                message_to_process = fetched_msg

                    # Wait if message has links but embeds haven't populated yet
                    if not message_to_process.embeds and (
                            "http://" in message_to_process.content or "https://" in message_to_process.content):
                        print("URL detected without embed. Waiting 2 seconds for Discord to parse link...")
                        await asyncio.sleep(2.0)

                        # Re-fetch fresh message using history instead of fetch_message
                        updated_msg = await self._fetch_message_selfbot(message.channel, message_to_process.id)
                        if updated_msg:
                            message_to_process = updated_msg

                    destination_channel = self.client.get_channel(destination_channel_id)
                    if not destination_channel:
                        print(f"Could not find destination channel ID: {destination_channel_id}")
                        return

                    # Forward text content
                    if message_to_process.content:
                        await destination_channel.send(message_to_process.content)

                    # Forward direct attachments
                    if message_to_process.attachments:
                        for attachment in message_to_process.attachments:
                            await destination_channel.send(attachment.url)

                    # Forward embed images & thumbnails
                    if message_to_process.embeds:
                        for embed in message_to_process.embeds:
                            image_url = None
                            if embed.image:
                                image_url = embed.image.url or embed.image.proxy_url
                            elif embed.thumbnail:
                                image_url = embed.thumbnail.url or embed.thumbnail.proxy_url

                            if image_url:
                                print(f"Forwarding image URL: {image_url}")
                                await destination_channel.send(image_url)

                except Exception as e:
                    import traceback
                    print(f"Error processing message: {str(e)}")
                    print(traceback.format_exc())

    def _setup_commands(self):
        @self.client.command()
        async def test(ctx):
            await ctx.send("Hello World!")

    def run(self):
        """
        Start the bot using the token from config.
        This method blocks until the bot is shut down.
        """
        try:
            self.client.run(self.token, bot=False)
        except Exception as e:
            raise Exception(f"Failed to start bot: {str(e)}")
        finally:
            print("bot shutting down")