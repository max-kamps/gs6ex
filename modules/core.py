import inspect
import textwrap
from datetime import datetime as dt, timezone as tz

import discord

import gs6ex.module as mod


def clean_code(content):
    content = content.strip()

    if content.startswith('```py'):
        content = content[5:]

    if content.startswith('```'):
        content = content[3:]

    if content.endswith('```'):
        content = content[:-3]

    return content.strip('`').strip()


class CoreModule(mod.Module):
    def create_env(self, ctx):
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'dsc': discord,
        }
        env.update(globals())
        return env

    @mod.command(name='eval', hidden=True, usage='eval <code>', description='Evaluate a piece of python code')
    @mod.is_superuser()
    async def eval_cmd(self, ctx, *, code: str):
        code = clean_code(code)

        result = eval(code, self.create_env(ctx))
        if inspect.isawaitable(result):
            result = await result

        await ctx.send_paginated(result)

    @eval_cmd.error
    async def eval_err(self, ctx, error):
        if isinstance(error, mod.CheckFailure):
            pass
        
        else:
            await ctx.send_paginated(error)

    @mod.command(name='exec', hidden=True, usage='exec <code>', description='Execute a piece of python code')
    @mod.is_superuser()
    async def exec_cmd(self, ctx, *, code: str):
        code = clean_code(code)

        env = self.create_env(ctx)
        code = f'import asyncio\nasync def _func():\n{textwrap.indent(code, "    ")}'

        exec(code, env)

        result = await env['_func']()

        if result is not None:
            await ctx.send_paginated(result)

    @exec_cmd.error
    async def exec_err(self, ctx, error):
        if isinstance(error, mod.CheckFailure):
            pass
        
        else:
            await ctx.send_paginated(error)


    @mod.command(name='times', hidden=True, usage='times', description='Show uptime stats')
    async def times_cmd(self, ctx):
        await ctx.send(f'```prolog\nFirst Ready: {self.bot.first_ready}\nLast Ready:  {self.bot.last_ready}\nLast Resume: {self.bot.last_resume}\nUptime:      {dt.now(tz.utc) - self.bot.first_ready}```')
