import os
import json
import threading
import argparse

""" Using original HTTP package to avoid:
    1. Binary file / cross-compiler not supported machine
    2. LAN only runtime env.
"""
import http.client

KEY_WS_ADDR = 'ws_addr'
KEY_WS_PORT = 'ws_port'
KEY_WS_TIMEOUT = 'ws_timeout'
KEY_WS_ENDPOINT = 'endpoint'
KEY_WS_HEADERS = 'http_headers'
KEY_WS_METHOD = 'method'

CONFIG_FILE = 'config.json'
WS_FILE = 'web_services.json'

g_env = 'lab'
g_config = dict()
g_endpoints = dict()
g_pwd = os.path.dirname(os.path.realpath(__file__))

CONFIG_FILE = os.path.join(g_pwd, CONFIG_FILE)
WS_FILE = os.path.join(g_pwd, WS_FILE)

def load_env(args):
    global g_env 
    g_env = args.env

def load_config():
    global g_config
    with open(CONFIG_FILE) as file:
        try:
            configs = json.load(file)
        except:
            raise
        else:
            if g_env not in configs.keys():
                raise Exception("ENV \"%s\" not on config file" % g_env)
            g_config = configs[g_env]

def load_endpoint():
    global g_env
    global g_endpoints
    with open(WS_FILE) as file:
        try:
            endpoints = json.load(file)
        except:
            raise
        else:
            if g_env not in endpoints.keys():
                raise Exception("ENV \"%s\" not on WS file" % g_env)
            g_endpoints = endpoints[g_env]

class FileSemaphore:
    SIG_LOCKED = 1
    SIG_UNLOCKED = 0
    SIG_FAILED = -1

    REQUEST_FILE = 'request'
    RESPONSE_FILE = 'response'
    SEMAPHORE_FILE = 'semaphore'
    STATUS_FILE = 'status'
    SEMAPHORES_DIR = 'semaphores'

    def __init__(self, base, name):
        path = os.path.join(base, FileSemaphore.SEMAPHORES_DIR, name)
        try:
            os.makedirs(path, exist_ok=True)
        except:
            raise
        else:
            self._dir = path
            self._name = name
            # self._semaphore = FileSemaphore.SIG_UNLOCKED
            # self._request = None
            self._status = None
            self._response = None
            self.semaphore_read()
            self.request_read()

    def file_read(self, file):
        try:
            with open(os.path.join(self._dir, file), 'r', encoding='utf8') as file:
                lines = file.readlines()
                return lines
        except:
                return None

    def file_write(self, file, data):
        with open(os.path.join(self._dir, file), 'w', encoding='utf8') as file:
            file.write(data)
    
    def request_read(self):
        lines = self.file_read(FileSemaphore.REQUEST_FILE)
        if lines is None:
            self._request = None
        else:
            self._request = "\r\n".join(lines)
        return self._request

    def response_write(self, data):
        escape_of_xml = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": "\"",
            "&apos;": "'",
        }
        for escape in escape_of_xml.keys():
            data = data.replace(escape, escape_of_xml[escape])
        self._response = data
        self.file_write(FileSemaphore.RESPONSE_FILE, self._response)

    def semaphore_read(self):
        try:
            with open(os.path.join(self._dir, FileSemaphore.SEMAPHORE_FILE)
                    , 'r', encoding='utf8') as file:
                line = file.readline()
                self._semaphore = int(line)
        except:
            self._semaphore = FileSemaphore.SIG_UNLOCKED
        finally:
            return self._semaphore

    def semaphore_write(self, signal):
        self._semaphore = int(signal)
        with open(os.path.join(self._dir, FileSemaphore.SEMAPHORE_FILE)
                , 'w', encoding='utf8') as file:
            file.write(str(self._semaphore))

    def status_write(self, status_code):
        self._status = status_code
        with open(os.path.join(self._dir, FileSemaphore.STATUS_FILE)
                , 'w', encoding='utf8') as file:
            file.write(str(self._status))


def agent_work_task(host, port, timeout, dir, endpoint_name, endpoint):
    semaphore = FileSemaphore(dir, endpoint_name)
    signal = semaphore.semaphore_read()

    if signal != FileSemaphore.SIG_LOCKED:
        return

    try:
        conn = http.client.HTTPConnection(host ,port, timeout)
        conn.request(method=endpoint[KEY_WS_METHOD],
                    url=endpoint[KEY_WS_ENDPOINT],
                    headers=endpoint[KEY_WS_HEADERS],
                    body=semaphore.request_read())
        response = conn.getresponse()
        statue_code = response.status
        semaphore.response_write(response.read().decode('utf8', 'ignore'))
        semaphore.status_write(statue_code)
        semaphore.semaphore_write(FileSemaphore.SIG_UNLOCKED)
    except Exception as ex:
        print(ex)
        semaphore.status_write(FileSemaphore.SIG_FAILED)
        semaphore.semaphore_write(FileSemaphore.SIG_FAILED)

def agent_work_consumer_sample(args):
    global g_config
    global g_endpoints
    global g_pwd
    threads = list()

    for endpoint_name in g_endpoints.keys():
        host = g_config[KEY_WS_ADDR]
        port = g_config[KEY_WS_PORT]
        timeout = g_config[KEY_WS_TIMEOUT]
        endpoint = g_endpoints[endpoint_name]
        if args.endpoints is not None and endpoint_name not in args.endpoints:
            continue
        threads.append(
            threading.Thread(target=agent_work_task,
                            args=(host, port, timeout, args.work_dir, endpoint_name, endpoint),
                            daemon=True)
        )

        threads[-1].start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-dir', dest="work_dir", required=False, type=str, 
                        metavar="<path>",
                        default=g_pwd,
                        help="Agent WS files saved path. Default = $PWD",
                        )
    parser.add_argument('--env', dest="env", required=False, type=str, 
                        metavar="<env (name of config sets)>",
                        default='lab',
                        help="Use config sets which defined in config.json. Default = lab",
                        )
    parser.add_argument('--endpoints', dest="endpoints", required=False, type=str, 
                        metavar="<endpoint_name [endpoint_name, ...]>",
                        nargs="*",
                        help="Run specific endpoint(s). Default = ALL",
                        )
    args = parser.parse_args()
    load_env(args)
    load_config()
    load_endpoint()
    agent_work_consumer_sample(args)
    