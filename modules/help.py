from discord import Embed

from ..common import *
from .. import module as mod


def cmd_str(c):
    return f'**{c.usage or c.name}**\n{c.description or "No description"}\n'


def cmd_str_debug(c):
    return f'**{c.usage or c.name}** [{", ".join(check.__qualname__.split(".", maxsplit=1)[0] for check in c.checks)}]\n{c.description or "No description"}\n'


class HelpModule(mod.Module):
    @mod.command(name='help', usage='help', description='Show this message')
    async def help_cmd(self, ctx):
        commands = [c for c in ctx.bot.commands if not c.hidden]
        commands.sort(key=lambda c: c.name)
        commands.sort(key=lambda c: c.name != 'help')

        embed = Embed(colour=getattr(ctx.me, 'color', 0), description='\n'.join(cmd_str(c) for c in commands))
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)

        await ctx.send(embed=embed)

    @mod.command(name='_help', hidden=True, usage='_help', description='Show debug information about all commands')
    @mod.is_superuser()
    async def _help_cmd(self, ctx):
        commands = [c for c in ctx.bot.commands]
        commands.sort(key=lambda c: c.name)
        commands.sort(key=lambda c: c.name != 'help')

        embed = Embed(colour=getattr(ctx.me, 'color', 0), description='\n'.join(cmd_str_debug(c) for c in commands))
        embed.set_author(name=ctx.me.name, icon_url=ctx.me.avatar_url)

        await ctx.send(embed=embed)
