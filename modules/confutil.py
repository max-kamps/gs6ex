from ast import literal_eval

from ..common import *
from .. import module as mod


class ConfUtilModule(mod.Module):
    @mod.group(name='config', hidden=True, invoke_without_command=True)
    @mod.is_superuser()
    async def config_cmd(self, ctx):
        pass

    @config_cmd.command(name='get')
    @mod.is_superuser()
    async def get_cmd(self, ctx, module: str):
        if module not in self.bot.modules:
            await ctx.add_success_reaction(False)
            await ctx.send(f"Module {module!r} is not loaded.")
            return

        await ctx.send_paginated(f'{{\n{NEW_LINE.join(f"    {k!r}: {v!r}," for k, v in self.bot.modules[module].conf.items())}\n}}')

    @config_cmd.command(name='set')
    @mod.is_superuser()
    async def set_cmd(self, ctx, module: str, key: str, *, value):
        if module not in self.bot.modules:
            await ctx.add_success_reaction(False)
            await ctx.send(f"Module {module!r} is not loaded.")
            return

        try:
            self.bot.modules[module].conf[key] = literal_eval(value)
        
        except Exception:
            await ctx.add_success_reaction(False)
            raise
        
        else:
            await ctx.add_success_reaction(True)
