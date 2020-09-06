`d-bug12` is both a Python api, and a command line interface for the Dbug-12 program flashed in Motorola's HC12 chips

d-bug12
========

## Installation

```bash
pip install dbug12
```

You should have Python's user base directory in your path for the CLI to work properly. In case it's not, use `python -m site --user-base` to get it and add it to your system path.

### Manually

Although the recommended way to install is using Python's package installer, there is an installation script (Linux only) in case you don't have `pip` set up.

```bash
sudo ./install
```

## CLI usage

```bash
dbug12 [flags] <command>
```

```
usage: dbug12 [-h] [-p PORT] <command> ...

positional arguments:
  <command>             dbug12 <command> -h will show further usage and
                        arguments, if any. Available commands are:

    load                Load a compiled program into memory
    next-instruction    Run a single instruction (from current PC)
    run                 Start execution from a specific point of memory
    monitor             Spawns a terminal that directly communicates with the board
    get-registers       Display CPU registers
    erase-memory        Erase a section of memory
    get-memory          Display a section of memory

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  serial communication port accessed by the board.
                        Default: "/dev/ttyUSB0"
```

## Examples

Examples for the Python api can be found in [examples](examples).

## Assembling

A command line implementation of the HC12 assembler for Linux can be found at [68hc12-linux](https://github.com/mlndz28/68hc12-linux).
