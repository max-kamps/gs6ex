import os
import subprocess as subp
from shlex import quote

import gs6ex.module as mod


class SystemModule(mod.Module):
    def on_load(self):
        self.conf.setdefault('systemd_service_name', 'gs6ex')
        self.conf.sync()

    @mod.command(name='update', hidden=True)
    @mod.is_owner()
    async def update_cmd(self, ctx):
        failure = subp.call(['git', 'pull']) or subp.call(['git', 'submodule', 'update', '--recursive', '--remote'])
        await ctx.add_success_reaction(not failure)

    @mod.command(name='restart', hidden=True)
    @mod.is_owner()
    async def restart_cmd(self, ctx):
        service = self.conf['systemd_service_name']
        
        if not service:
            await ctx.add_success_reaction(False)

        else:
            # Normally, using os.system is not a good idea.
            # I think it's fine in this case because we don't
            # have any user controlled data and the command shuts down
            # the program anyway.
            # I tried using subprocess here, but it didn't work.
            # ~hmry (2019-10-21, 02:12)
            systemd_name = f'{self.conf["systemd_service_name"]}@{self.bot.profile_name}'
            os.system(f'systemctl --user restart {quote(systemd_name)}')
