#!/usr/bin/env python3
import os
import time
import sys
import configparser
import threading
import signal

import twitch
import server
import commands
import goodgame
import peka2tv
import payments
import common
import youtube


def load_smiles():
    smiles = {}

    if 'twitch' in config:
        smiles['twitch'] = twitch.Twitch.load_smiles(config, messages)

    if 'goodgame' in config:
        smiles['goodgame'] = goodgame.GoodGame.load_smiles(messages)

    if 'peka2tv' in config:
        smiles['peka2tv'] = peka2tv.Peka2tv.load_smiles(messages)

    return smiles


def main():
    threads.append(server.Server(config, messages, base_dir))

    if 'twitch' in config:
        for channel in config['twitch'].getlist('channels'):
            threads.append(twitch.Twitch(channel, config, messages,
                                         smiles['twitch'], stop_event))

    if 'goodgame' in config:
        for channel in config['goodgame'].getlist('channels'):
            threads.append(goodgame.GoodGame(channel, config, messages,
                                             smiles['goodgame'], stop_event))

    if 'peka2tv' in config:
        for channel in config['peka2tv'].getlist('channels'):
            threads.append(peka2tv.Peka2tv(channel, config, messages,
                                           smiles['peka2tv'], stop_event))

    if config['base'].getboolean('is_youtube'):
        threads.append(youtube.YouTube(None, config, messages,
                                       None, stop_event, base_dir))

    if 'commands' in config:
        threads.append(commands.Commands(config, messages, stop_event))

    threads.append(payments.Payments(config, messages, stop_event))


def shutdown(*args):
    stop_event.set()
    [thread.stop() for thread in threads]


def restart_watcher():
    start_timestamp = os.path.getmtime(config_path)

    while not stop_event.is_set():
        time.sleep(5)

        if start_timestamp != os.path.getmtime(config_path) or \
           config['base'].getboolean('is_restart'):
            shutdown()
            stop_event.clear()
            # Время на обнуление offset в браузере.
            time.sleep(5)

            break


if __name__ == '__main__':
    stop_event = threading.Event()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    smiles = {}
    config_path = os.path.join(base_dir, 'config.ini')
    config = configparser.ConfigParser(converters={'list': common.str_to_list})

    signal.signal(signal.SIGINT, shutdown)

    while not stop_event.is_set():
        threads = []
        config.read(config_path)
        config['base']['is_restart'] = 'false'
        messages = common.UserList(config)

        if not smiles:
            smiles = load_smiles()

        main()
        restart_watcher()

    sys.exit()