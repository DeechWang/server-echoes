from discord_logic import DiscordSelfBot  # Assuming the class is in discord_selfbot.py


def main():
    try:
        # Create an instance of the bot
        bot = DiscordSelfBot()

        # Run the bot
        print("Starting Discord bot...")
        bot.run()
    except Exception as e:
        print(f"Error running bot: {e}")


if __name__ == "__main__":
    main()