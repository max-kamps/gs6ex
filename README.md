# Gs6Ex

A highly modular Discord bot written in Python.

## Table of Contents
- [Usage](#usage)
- [Installation](#installation)
- [Setup](#setup)

## Usage
To use the bot, mention it with your command.

```@Gs6Ex help```

In direct messages the mention is optional.

Use the `help` command to list available commands, or `_help` to list all commands, even hidden ones.

## Installation
This bot requires Python 3.6+ or higher.

This is the recommended installation for Linux servers.
We will create a new user for the bot, place all the code in that users home directory and then create a systemd user service to run the bot.
```sh
# Create new user
$ sudo useradd -m gs6ex
$ sudo passwd -l gs6ex
$ sudo loginctl enable-linger gs6ex
$ sudo su gs6ex
$ cd ~

# Install Gs6Ex
$ git clone https://github.com/max-kamps/gs6ex.git gs6ex
$ cd gs6ex

# Add any module sets you want to use as submodules
# This is just an example, use your own git repo
$ git submodules add https://github.com/max-kamps/helper modules/helper

# Create virtualenv, install dependencies
$ python3 -m venv .
$ source bin/activate
$ python -m pip install -r requirements.txt
$ deactivate

# Create the credentials file
$ cp credentials.example.json credentials.json

# Make sure to edit the credentials file
# You can add multiple profiles and their tokens to run multiple instances of the bot if you want to

# Create the user service
$ mkdir -p ~/.config/systemd/user
$ ln -s ~/gs6ex/gs6ex@.service ~/.config/systemd/user/gs6ex@.service
$ export XDG_RUNTIME_DIR=/run/user/`id -u`  # Work around some weird XDG issues

# Replace main with any profile name you want to run
$ systemctl --user enable gs6ex@main
$ systemctl --user start gs6ex@main

# We're done, exit su
$ exit
```

Alternatively, you can install the bot without creating a service.
Note that this means you will have to manually restart the bot if it crashes.
This is the recommended installation if you want to work on the bot or create a module set.
```sh
# Install Gs6Ex
$ git clone https://github.com/max-kamps/gs6ex.git gs6ex
$ cd gs6ex

# Add any module sets you want to use as submodules
# This is just an example, use your own git repo
$ git submodules add https://github.com/max-kamps/helper modules/helper

# Alternatively, you can also symlink any module sets you're developing locally
$ ln -s ../helper modules/helper

# Create the credentials file
$ cp credentials.example.json credentials.json
# Make sure to edit the credentials file
# You can add multiple profiles and their tokens to run multiple instances of the bot if you want to

# Create virtualenv, install dependencies
$ python3 -m venv .
$ source bin/activate
$ python -m pip install -r requirements.txt
$ deactivate
$ cd ..

# Run the bot!
$ gs6ex/bin/python -m gs6ex main
```

## Setup
When first started, only the `core` module is loaded. To load the other standard modules, we can use `modutil`.
Run the following commands:

```sh
# Inside of Discord, mentioning the bot as necessary
$ eval bot.load_module('modutil')
$ modules load confutil help system
```
