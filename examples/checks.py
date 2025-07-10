from matrix import Bot, Context

bot = Bot("examples/config.yaml")

allowed_users = {"@alice:matrix.org", "@bob:matrix.org"}


@bot.command("secret")
async def secret_command(ctx: Context):
    await ctx.reply("🎉 Welcome to the secret club!")


@secret_command.check
async def is_allowed_user(ctx: Context) -> bool:
    if ctx.sender in allowed_users:
        return True
    await ctx.reply("You do not have permission to use this command.")
    return False


bot.start()
