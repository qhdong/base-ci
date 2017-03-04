#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import argparse
import os
import sys
import subprocess
import socket
import socketserver
import time

import helpers

def poll():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher-server",
                        help="dispatcher host:port, " \
                        "by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

    while True:
        try:
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("Could not update and check repository. " +
                            "Reason: {}".format(e.output))

        if os.path.isfile(".commit_id"):
            try:
                response = helpers.communicate(dispatcher_host,
                                                int(dispatcher_port),
                                                "status")
            except socket.error as e:
                raise Exception("Could not communicate with dispatcher server:"
                        "{}".format(e))

            if response == 'OK':
                commit = ""
                with open('.commit_id', 'r') as f:
                    commit = f.readline()
                response = helpers.communicate(dispatcher_host,
                                                int(dispatcher_port),
                                                "dispatch:{}".format(commit))
                if response != 'OK':
                    raise Exception("Could not dispatch the test:{}"
                            .format(response))
                print("dispatched")
            else:
                raise Exception("Could not dispatch the test: {}"
                        .format(response))
        time.sleep(5)

if __name__ == '__main__':
    poll()
