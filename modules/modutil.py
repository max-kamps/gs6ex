from ..common import *
from .. import module as mod


class ModUtilModule(mod.Module):
    @mod.group(name='modules', hidden=True, invoke_without_command=True)
    @mod.is_owner()
    async def modules_cmd(self, ctx):
        await ctx.send(f'```Loaded modules:\n{NEW_LINE.join(self.bot.modules)}```')

    @modules_cmd.command(name='load')
    @mod.is_owner()
    async def load_cmd(self, ctx, *, modules: str):
        modules = tuple(self.bot.modules.keys()) if modules == 'all' else modules.split()

        try:
            for module in modules:
                await self.bot.load_module(module)
            
        except Exception:
            await ctx.add_success_reaction(False)
            raise
        
        else:
            await ctx.add_success_reaction(True)

    @modules_cmd.command(name='unload')
    @mod.is_owner()
    async def unload_cmd(self, ctx, *, modules: str):
        modules = tuple(self.bot.modules.keys()) if modules == 'all' else modules.split()

        try:
            for module in modules:
                await self.bot.unload_module(module)
            
        except Exception:
            await ctx.add_success_reaction(False)
            raise
        
        else:
            await ctx.add_success_reaction(True)
