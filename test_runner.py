#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import argparse
import errno
import os
import re
import socket
import socketserver
import subprocess
import time
import threading
import unittest

import helpers

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    dispatcher_server = None
    last_communication = None
    busy = False
    dead = False

class TestHandler(socketserver.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        command_groups = self.command_re.match(self.data.decode())
        command = command_groups.group(1)
        if not command:
            self.request.sendall(b"Invalid command")
            return
        if command == "ping":
            print("pinged")
            self.server.last_communication = time.time()
            self.request.sendall(b"pong")
        elif command == "runtest":
            print("got runtest command: am I busy? {}".format(self.server.busy))
            if self.server.busy:
                self.request.sendall(b"BUSY")
            else:
                self.request.sendall(b"OK")
                print("running")
                commit_id = command_groups.group(2)[1:]
                self.server.busy = True
                self.run_tests(commit_id, self.server.repo_folder)
                self.server.busy = False
        else:
            self.request.sendall(b"Invalid command")

    def run_tests(self, commit_id, repo_folder):
        output = subprocess.check_output(["./test_runner_script.sh",
                                        repo_folder, commit_id])
        print(output)
        test_folder = os.path.join(repo_folder, "tests")
        suite = unittest.TestLoader().discover(test_folder)
        result_file = open("results", "w")
        unittest.TextTestRunner(result_file).run(suite)
        result_file.close()
        result_file = open("results", "r")
        output = result_file.read()
        helpers.communicate(self.server.dispatcher_server["host"],
                            int(self.server.dispatcher_server["port"]),
                            "results:{}:{}:{}".format(commit_id, len(output), output))

def serve():
    range_start = 8900
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="runner's host, by default it uses localhost",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="runner's port, by default it uses values >={}".format(range_start),
                        action="store")
    parser.add_argument("--dispatcher-server",
                        help="dispatcher host:port, by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str, help="path to the repository this will observe")
    args = parser.parse_args()

    runner_host = args.host
    runner_port = None

    tries = 0
    if not args.port:
        runner_port = range_start
        while tries < 100:
            try:
                server = ThreadingTCPServer((runner_host, runner_port),
                                            TestHandler)
                print(server)
                print(runner_port)
                break
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    tries += 1
                    runner_port = runner_port + tries
                    continue
                else:
                    raise e
        else:
            raise Exception("Could not bind to ports in range {}-{}".format(range_start, range_start+tries))
    else:
        runner_port = int(args.port)
        server = ThreadingTCPServer((runner_host, runner_port), TestHandler)
    server.repo_folder = args.repo

    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    server.dispatcher_server = {"host":dispatcher_host, "port":dispatcher_port}
    response = helpers.communicate(server.dispatcher_server["host"],
                                    int(server.dispatcher_server["port"]),
                                    "register:{}:{}".format(runner_host, runner_port))

    if response != "OK":
        raise Exception("Can't register with dispatcher")

    def dispatcher_checker(server):
        while not server.dead:
            time.sleep(5)
            if (time.time() - server.last_communication) > 10:
                try:
                    response = helpers.communicate(
                            server.dispatcher_server["host"],
                            int(server.dispatcher_server["port"]),
                            "status")
                    if response != "OK":
                        print("Dispatcher is no longer functional")
                        server.shutdown()
                        return
                except socket.error as e:
                    print("Can't communicate with dispatcher: {}".format(e))
                    server.shutdown()
                    return
    t = threading.Thread(target=dispatcher_checker, args=(server,))
    try:
        t.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        t.join()


if __name__ == "__main__":
    serve()
