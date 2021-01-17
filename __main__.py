import asyncio
import contextlib
import json
import logging
import os
import sys
from pathlib import Path

import gs6ex


@contextlib.contextmanager
def logger(name, level):
    l = logging.getLogger(name)
    l.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] (%(levelname)s) %(name)s: %(message)s'))

    l.addHandler(handler)

    yield l

    for hdlr in l.handlers[:]:
        l.removeHandler(hdlr)
        hdlr.close()


with logger('discord', logging.WARNING), logger('twitch', logging.DEBUG), logger('bot', logging.DEBUG) as log:
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 -m gs6ex <profile>')
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    cred_file = Path('credentials.json')

    if not cred_file.is_file():
        sys.exit("Error: credentials.json doesn't exist!")

    with open(cred_file) as f:
        credentials = json.load(f)
        if len(credentials) == 0:
            sys.exit("Error: credentials.json doesn't contain any credentials!")

    chosen_profile = sys.argv[1]

    if chosen_profile not in credentials:
        sys.exit(f'Error: {chosen_profile!r} does not have any credentials!\nValid profiles:\n' + '\n'.join(f'  {n!r}' for n in credentials))

    credentials = credentials[chosen_profile]

    db_path = (Path(__file__).parent / '.data' / chosen_profile / 'data.db').resolve()
    os.makedirs(db_path.parent, exist_ok=True)

    bot = gs6ex.Gs6Ex(credentials, chosen_profile, db_path)
    bot.run(credentials['discord_token'])
