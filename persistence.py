import shelve


config_dir = None


opened_shelves = {}

def get_module_shelf(mod_name):
    if mod_name in opened_shelves:
        return opened_shelves[mod_name]

    s = shelve.open(str(config_dir / mod_name), writeback=True)

    opened_shelves[mod_name] = s
    return s


def close_module_shelf(mod_name):
    if mod_name in opened_shelves:
        opened_shelves[mod_name].close()
        del opened_shelves[mod_name]


def close_all_shelves():
    for s in opened_shelves.values():
        s.close()

    opened_shelves.clear()
