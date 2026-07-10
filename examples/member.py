from matrix import Bot

bot = Bot()


@bot.command()
async def profile(ctx):
    member = ctx.member

    name = await member.get_display_name()
    avatar = await member.get_avatar_url()
    level = await member.get_room_power_level(ctx.room)
    presence = await member.get_presence()
    has_permission = await member.has_room_permission(ctx.room, "ban")
    has_event_permission = await member.has_event_permission(
        ctx.room, "m.room.history_visibility"
    )

    await ctx.reply(
        f"Welcome {member.mention()}!\n"
        f"Display name: {name}\n"
        f"Avatar URL: {avatar}\n"
        f"Power level: {level}\n"
        f"Presence: {presence}\n"
        f"Has permission to ban users: {has_permission}\n"
        f"Has permission to see history: {has_event_permission}"
    )


bot.start(config="config.yaml")
