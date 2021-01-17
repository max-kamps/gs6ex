import typing
import asyncio
import re
from datetime import datetime as dt, timezone as tz
import logging

import aiosqlite
import discord.ext.commands as cmd
from discord.ext.commands.view import StringView

from . import module


log = logging.getLogger('bot')
asyncio.get_event_loop().set_exception_handler(lambda loop, ctx: log.error(ctx['message'], exc_info=ctx.get('exception')))


class Gs6Ex(cmd.Bot):
    class Config(module.Config):
        active_modules: set[str] = set()
        superusers: set[int] = set()

    def __init__(self, credentials, profile_name, db_path):
        super().__init__(command_prefix='', description='', pm_help=False, help_attrs={})
        super().remove_command('help')

        self.profile_name = profile_name
        self.db_path = db_path
        
        self.db = None
        self.conf = None
        self.credentials = credentials

        self.first_ready = None
        self.last_ready = None
        self.last_resume = None

        self.command_regex = None
        self.command_dms_regex = None

        self.modules = {}

    async def on_ready(self):
        log.info(f'Ready with Username {self.user.name!r}, ID {self.user.id!r}')

        now = dt.now(tz.utc)
        self.last_ready = now

        self.command_regex = re.compile(fr'(?s)^<@!?{self.user.id}>(.*)$')
        self.command_dms_regex = re.compile(fr'(?s)^(?:<@!?{self.user.id}>)?(.*)$')

        if self.first_ready is None:
            self.db = await aiosqlite.connect(self.db_path)

            async with self.db.execute('PRAGMA user_version;') as cursor:
                user_version, = await cursor.fetchone()
                log.info(f'Schema version {user_version}')
                if user_version == 0:
                    log.warning(f'Initializing database...')
                    await self.db.execute('''
                        CREATE TABLE IF NOT EXISTS config (
                            name TEXT PRIMARY KEY,
                            data BLOB NOT NULL
                        );''')
                    await self.db.execute('PRAGMA user_version = 1;')
                    await self.db.commit()

            self.conf = self.Config(self.db, 'gs6ex')
            await self.conf.load()
            
            self.first_ready = now
            # The core module should always be loaded, so we can use eval to repair misconfigurations
            for mod_name in {'core', *self.conf.active_modules}:
                try:
                    await self.load_module(mod_name)
                except:
                    log.error(f'Error loading module {mod_name}', exc_info=True)

    async def on_resumed(self):
        log.warning(f'Resumed')
        self.last_resume = dt.now(tz.utc)

    async def close(self):
        log.info('Closing...')
        for mod in self.modules.copy():
            await self.unload_module(mod, persistent=False)

        if self.db:
            await self.db.close()

        await super().close()

    async def load_module(self, name, persistent=True):
        if name in self.modules:
            await self.unload_module(name, persistent=False)
        
        C = module.get_module_class(name)

        instance = C(self)
        await instance._on_load()
        self.modules[name] = instance
        self.add_cog(instance)

        if persistent:
            self.conf.active_modules.add(name)
            await self.conf.commit()

    async def unload_module(self, name, persistent=True):
        if name in self.modules:
            self.remove_cog(name)
            await self.modules[name]._on_unload()
            del self.modules[name]
        
        if persistent:
            self.conf.active_modules.discard(name)
            await self.conf.commit()

    async def is_superuser(self, user):
        return user.id in self.conf.superusers or await self.is_owner(user)

    async def get_context(self, message, *, cls=cmd.Context):
        # This function is called internally by discord.py.
        # We have to fiddle with it because we are using a dynamic prefix (our mention string),
        # as well as no prefix inside of DMs.
        # The included prefix matching functions could not deal with this case.
        # If it ever becomes possible, we should probably switch to that.

        # Frankly, I don't really remember what I did here, but it might be good
        # to periodically check the get_context method on the base class and
        # port over any changes that happened there. ~hmry (2019-08-14, 02:25)

        if self.command_regex is None:
            return cls(prefix=None, view=None, bot=self, message=message)

        cmd_regex = self.command_dms_regex if message.guild is None else self.command_regex
        match = cmd_regex.match(message.content)

        if not match:
            return cls(prefix=None, view=None, bot=self, message=message)

        view = StringView(match.group(1).strip())
        ctx = cls(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.user.id):
            return ctx

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.command = self.all_commands.get(invoker)
        return ctx
