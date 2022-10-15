# quake3-rcon
*An async Quake 3 RCON implementation for Python*

## Installation
```
pip install quake3-rcon
```
or with the cli extra
```
pip install quake3-rcon[cli]
```

## CLI Usage
```
Usage: q3rcon [OPTIONS] ADDRESS PASSWORD

Options:
  -p, --port INTEGER RANGE        [1<=x<=65535]
  --timeout FLOAT RANGE           [x>=0.01]
  --fragment-read-timeout, --fr-timeout FLOAT RANGE
                                  [x>=0.01]
  --retries INTEGER RANGE         [x>=1]
  --debug
  --help                          Show this message and exit.
```

## API Reference
#### [Examples Folder](examples)

#### *class* [`Client`](quake3_rcon/client.py)(`host`: *`str`*, `port`: *`int`*, `timeout`: *`float`*, `fragment_read_timeout`: *`float`*, `retries`: *`int`*, `logger`: *`Logger | None`*)
- Parameters:
  - `host`: *`str`* - *the host / IP / domain of the server to connect to*
  - `port`: *`port`* - *the port of the server to connect to*
    - default value is `27960`
  - `timeout`: *`float`* - *the timeout for network operations*
    - default value is `2.0`
    - for network operations with retries, the timeout applies to the rewrite attempts as a whole, rather than being per retry
  - `fragment_read_timeout`: *`float`* - *the timeout for waiting on potentially fragmented responses*
    - default value is `.25`
    - the Quake 3 server can sometimes send fragmented responses, since there is no consistent way to tell if a response is fragmented or not, the best solution is to wait for fragmented responses from the server whether they exist or not. This value is the timeout for waiting for those responses.
  - `retries`: *`int`* - *the amount of retries per network operation*
    - default value is `2`
    - all network operations except for reads are wrapped in retry logic
  - `logger`: *`Logger | None`* - *the logger instance*
    - default value is `None`
    - if there is no logger specified, a logger that has `disabled` set to `True` will be used instead
    - currently only some debug information is logged
- Methods:
  - `connect`(`verify`: *`bool`* = `True`) -> *`None`*
    - *connects to the server*
    - *if `verify` is `True`, then the `heartbeat` RCON command is sent and the password is checked as well*
    - *if `Client` is being used as a context manager, this will be called automatically upon enter*
  - `close`() -> *`None`*
    - *closes the connection to the server*
    - *if `Client` is being used as a context manager, this will be called automatically upon exit*
#### *exception* [`RCONError`](quake3_rcon/errors.py)
- Base exception all quake3-rcon errors derive from
#### *exception* [`IncorrectPasswordError`](quake3_rcon/errors.py)
- Raised when the provided password is incorrect
