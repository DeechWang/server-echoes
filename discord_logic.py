import discord
import json
from discord.ext import commands
from typing import Callable
from asyncio import get_running_loop
from datetime import datetime
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

        # Store the callback

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
            """Called when the bot is ready and connected to Discord"""
            ready_message = f"Logged in as {self.client.user.name}"
            print(ready_message)  # Keep console logging

        @self.client.event
        async def on_message(message):
            await self.client.process_commands(message)

            source_channel_id = [1259607738040979489]
            destination_channel_id = 1338207422694559747
            if message.channel.id in source_channel_id:
                try:
                    async for latest_message in message.channel.history(limit=1):
                        content_description = []
                        message_to_process = None

                        if hasattr(latest_message, 'reference') and latest_message.reference:
                            original_channel = self.client.get_channel(latest_message.reference.channel_id)
                            if original_channel:
                                async for hist_message in original_channel.history(limit=100):
                                    if hist_message.id == latest_message.reference.message_id:
                                        #print("Found original message!")
                                        message_to_process = hist_message
                                        break
                        else:
                            print("Processing direct message!")
                            message_to_process = latest_message

                        if message_to_process:
                            # Process the content and handle role mentions
                            if message_to_process.content:
                                content = message_to_process.content

                                content_description.append(f"{content}")
                            print("content description: ",content_description)
                            # Forward the message
                            destination_channel = self.client.get_channel(destination_channel_id)
                            if destination_channel:
                                channel_message = (
                                    f"{'\n'.join(content_description)}\n"
                                )
                                await destination_channel.send(channel_message)

                                # Handle attachments and embeds
                                if message_to_process.attachments:
                                    for attachment in message_to_process.attachments:
                                        await destination_channel.send(attachment.url)

                                if message_to_process.embeds:
                                    for embed in message_to_process.embeds:
                                        if embed.image and embed.image.url:  # Check if image exists and has URL
                                            #if embed.image.url.startswith('https://dubclub.win/iv/'):
                                            print(f"Embed image URL: {embed.image.url}")
                                            await destination_channel.send(embed.image.url)

                                #print(f"Message forwarded to channel: {destination_channel.name}")
                            else:
                                print(f"Could not find destination channel with ID: {destination_channel_id}")

                except Exception as e:
                    print(f"Error in message processing: {str(e)}")
                    import traceback
                    print(f"Full error: {traceback.format_exc()}")
        @self.client.event
        async def on_command(ctx):
            """Called whenever a command is executed"""
            print(f"Command used - {ctx.command.name}")

    def _setup_commands(self):
        @self.client.command()
        async def test(ctx):
            """Test command to verify bot functionality"""
            try:
                print(f"Starting test command execution in channel: {ctx.channel.name}")

                try:
                    await ctx.message.delete()
                    print("Successfully deleted command message")
                except Exception as e:
                    print(f"Error deleting message: {str(e)}")

                try:
                    await ctx.send("Hello World!")
                    print("Successfully sent response message")
                except Exception as e:
                    print(f"Error sending response: {str(e)}")

            except Exception as e:
                print(f"Overall command error: {str(e)}")

    def run(self):
        """
        Start the bot using the token from config.
        This method blocks until the bot is shut down.
        """
        try:
            self.client.run(self.token, bot=False)
            #self.client.run(self.token)
        except discord.LoginFailure:
            raise ValueError("Invalid token in config.json")
        except Exception as e:
            raise Exception(f"Failed to start bot: {str(e)}")
        finally:
            print("bot shutting down")