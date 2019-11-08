import discord

from .common import *


async def _send_paginated(self, *args, **kwargs):
    for page in paginate(*args, **kwargs):
        await self.send(page)

discord.abc.Messageable.send_paginated = _send_paginated


async def _add_success_reaction(self, success):
    await self.message.add_reaction('\N{HEAVY CHECK MARK}' if success else '\N{CROSS MARK}')

discord.ext.commands.Context.add_success_reaction = _add_success_reaction


_permission_bits = [name for name in dir(discord.Permissions) if isinstance(getattr(discord.Permissions, name), property)]

def _permission_str(self):
    return f'Perms({"|".join(name for name in _permission_bits if getattr(self, name))})'

discord.Permissions.__str__ = _permission_str
discord.Permissions.__repr__ = _permission_str
