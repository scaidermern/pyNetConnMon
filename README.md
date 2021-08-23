# pyNetConnMon

Monitor Internet (or network) connectivity. Send mail on network interruptions.

## Description

pyNetConnMon is an Internet connectivity monitor.
It tries to periodically connect to a given service and reports failures via mail.

## Checkout and configuration of pySendMail submodule

pyNetConnMon uses git submodules, specifically it uses [pySendMail](https://github.com/scaidermern/pySendMail) to send mail reports about connectivity losses.
After checkout, submodules have to be populated by the following commands:
```
git submodule init
git submodule update
```

Afterwards it is necessary to configure pySendMail in order to be able to send mails. 
Refer to the documentation of [pySendMail](https://github.com/scaidermern/pySendMail) and create a config file in the pySendMail subdirectory.

## Options

All of the following time-based arguments are specified in seconds.

- `-h, --help`: show this help message and exit
- `-a ADDRESS, --address ADDRESS`: host address to check (default: 8.8.8.8)
- `-p PORT, --port PORT`: host port to check (default: 53)
- `-i INTERVAL, --interval  INTERVAL`: check interval (default: 2.0)
- `-t TIMEOUT, --timeout TIMEOUT`: connection timeout (default: 2.0)
- `-m MIN_INTERRUPTION, --min-interruption MIN_INTERRUPTION`: ignore interruptions smaller than this (default: 5.0)
- `-bmin BACKOFF_MIN, --backoff-min BACKOFF_MIN`: minimum time to pass between mail reports (for backoff, default: 60.0)
- `-bmax BACKOFF_MAX, --backoff-max BACKOFF_MAX`: maximum time to pass between mail reports (for backoff, default: 3600.0)
- `-bstep BACKOFF_STEP, --backoff-step BACKOFF_STEP`: backoff wait time increment for subsequent connection losses (default: 300.0)

## Example

Monitor Internet connectivity by using Google's DNS server `8.8.8.8:53` from the default settings:
```
./pyNetConnMon.py
```

## Backoff mechanism

Repeated, continuous failures will result in a flood of mail reports.
Therefore pyNetConnMon comes with a simple backoff mechanism.
After each mail, the wait time until the next mail will be send is increased by `BACKOFF_STEP`, starting with `BACKOFF_MIN` for the first increment.
As soon as this wait time has passed, a mail report will get sent, including all network interruptions from that time span.
Continuous network failures increase this backoff, with an upper bound of `BACKOFF_MAX`.
`BACKOFF_MAX` is also used as time after which to reset the backoff to zero if interruptions stay absent.

# License
[GPL v3](http://www.gnu.org/licenses/gpl.html)
(c) Alexander Heinlein
