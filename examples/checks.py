from matrix import Bot, Context
from matrix.errors import CheckError

bot = Bot(config="config.yaml")

allowed_users = {"@alice:matrix.org", "@bob:matrix.org"}


@bot.command(name="secret")
async def secret_command(ctx: Context) -> None:
    await ctx.reply("🎉 Welcome to the secret club!")


@secret_command.check
async def is_allowed_user(ctx: Context) -> bool:
    if ctx.sender in allowed_users:
        return True
    return False


@secret_command.error(CheckError)
async def permission_error_handler(ctx: Context, error: CheckError) -> None:
    await ctx.reply(f"Access denied: {error}")


bot.start()
