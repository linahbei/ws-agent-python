# Web Service Agent

File based and semaphore-like web service (WS) requesting agent for legacy code project using, feature extension, etc.

--

## Project and App layout

### Static files
* ``ws_agent.py`` -- Main program
* ``config.json(.example)`` -- WS connection configs
* ``web_services.json(.example)`` -- Endpoint and request method configs of WS


### Runtime files
```
+ semaphores directory
  All file based IPC data of WS Agent
  /--- {endpoint} directory
       Files splitted and saved by WS endpoint 
       /--- semaphore file
            For Agent IPC communications lock and signale exchanging.
            0 = Idle
            1 = request or response files on write
            -1 = Requesting finished and WS timeout
       /--- request file
            Used and saved requesting to WS **XML escape encoded** data
       /--- response file
            Used and saved responsed from WS **XML escape decoded** data
  /--- {endpoint} directory
       ...
```

## Usage

### ``config.json`` -- WS address setup

The based URLs of WS are configured on ``config.json``. The layout of file as the following.

```json
{
    "lab":{
        "ws_addr": "{server address}",
        "ws_port": {port ID},
        "ws_timeout": {timeout seconds}
    },
    "prod":{
        ...
    }
}
```

### ``web_services.json`` -- WS endpoints setup

The based URLs of WS endpoints are configured in ``web_services.json``. The layout of file as the following.

```json
{
    "lab":{
        "{endpoint}":{
            "endpoint": "/v0.1/BookServices.asmx",
            "method": "POST",
            "http_headers": {
                "Content-Type": "text/xml;charset=utf-8"
            }
        },
        ...
    },
    "prod":{
        ...
    }
}
```

### ``ws_agent.py`` -- Main program

```shell
usage: ws_agent.py [-h] [--work-dir <path>] [--env <env name of config sets>]
                   [--endpoints <endpoint_name [endpoint_name, ...]>]

optional arguments:
  -h, --help            show this help message and exit
  --work-dir <path>     Agent WS files saved path. Default = $PWD
  --env <env (name of config sets)>
                        Use config sets which defined in config.json. Default
                        = lab
  --endpoints <endpoint_name [endpoint_name, ...]>
                        Run specific endpoint(s). Default = ALL

```


#### Runtime enverinment (config sets) setup

Agent used command line argument ``--env`` ~~a OS env. attritube ``WS_AGENT_ENV``~~ to assign runtime config sets which saved on config file ``config.json``. And default config sets is named ``lab``.


#### Configure example

Consider a full request URL of WS as the following.

```
http://192.168.1.100/v0.1/BookServices.asmx?op=GetISBN
```

The part of WS ~~address~~ host is
```
192.168.1.100
```

and endpoint is

```
/v0.1/BookServices.asmx?op=GetISBN
```
