import asyncio
import inspect
import textwrap
from datetime import datetime as dt, timezone as tz

import discord

import gs6ex.module as mod
from . import compress


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

    @mod.command(name='eval', usage='eval <code>', description='Evaluate a piece of python code')
    @mod.is_owner()
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

    @mod.command(name='exec', usage='exec <code>', description='Execute a piece of python code')
    @mod.is_owner()
    async def exec_cmd(self, ctx, *, code: str):
        code = clean_code(code)

        env = self.create_env(ctx)
        code = f'import asyncio\nasync def _func():\n{textwrap.indent(code, "    ")}'

        exec(code, env)

        result = await env['_func']()

        if result is not None:
            await ctx.send_paginated(result)

    @mod.command(name='execc', usage='execc <code>', description='Execute a compressed piece of python code')
    @mod.is_owner()
    async def execc_cmd(self, ctx, *, code: str):
        code = clean_code(code)
        code = compress.base32768_decode_bytes(code).decode()

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


    @mod.command(name='times', usage='times', description='Show uptime stats')
    async def times_cmd(self, ctx):
        await ctx.send(f'```prolog\nFirst Ready: {self.bot.first_ready}\nLast Ready:  {self.bot.last_ready}\nLast Resume: {self.bot.last_resume}\nUptime:      {dt.now(tz.utc) - self.bot.first_ready}```')

    @mod.group(name='superuser', invoke_without_command=True)
    @mod.is_owner()
    async def superuser_cmd(self, ctx):
        su_list = await asyncio.gather(*(self.bot.fetch_user(u) for u in self.bot.conf.superusers))
        await ctx.send_paginated('Superusers:\n' + '\n'.join(f' - {su}' for su in su_list))

    @superuser_cmd.command(name='add')
    @mod.is_owner()
    async def superuser_add_cmd(self, ctx, user: discord.User):
        self.bot.conf.superusers.add(user.id)
        await self.bot.conf.commit()
        await ctx.send(f'Added {user} to superusers\n')

    @superuser_cmd.command(name='remove')
    @mod.is_owner()
    async def superuser_remove_cmd(self, ctx, user: discord.User):
        self.bot.conf.superusers.discard(user.id)
        await self.bot.conf.commit()
        await ctx.send(f'Removed {user} from superusers\n')
