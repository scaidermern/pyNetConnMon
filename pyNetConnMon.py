#!/usr/bin/env python3
# -*- coding: utf-8 -*

import argparse
import datetime
import socket
import time

from pySendMail import sendMail

class pyNetConnMon:
    defaultHost = '8.8.8.8'
    defaultPort = 53

    # all settings are specified in seconds
    defaultCheckInterval = 2.0
    defaultCheckTimeout  = 2.0
    defaultMinInterruption = 5.0
    defaultBackoffMin  =  1.0 * 60.0
    defaultBackoffMax  = 60.0 * 60.0
    defaultBackoffStep =  5.0 * 60.0

    def __init__(self):
        self.host = self.defaultHost
        self.port = self.defaultPort

        # all settings are specified in seconds
        self.checkInterval = self.defaultCheckInterval
        self.checkTimeout = self.defaultCheckTimeout
        self.minInterruption = self.defaultMinInterruption
        self.backoffMin = self.defaultBackoffMin
        self.backoffMax = self.defaultBackoffMax
        self.backoffStep = self.defaultBackoffStep

    def checkConnectivity(self):
        try:
            socket.setdefaulttimeout(self.checkTimeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.host, self.port))
            return True
        except socket.error as ex:
            return False
        except Exception as e:
            print(e)
            return False

    def monitor(self):
        lastConnectivity = True
        upSince = downSince = datetime.datetime.now()
        mailLastSend = datetime.datetime.fromtimestamp(0)
        mailBackoff = None
        msgList = list()
        while True:
            now = datetime.datetime.now()
            connectivity = self.checkConnectivity()
            connectivityChange = connectivity != lastConnectivity
            if connectivityChange:
                if not connectivity:
                    # we are down
                    downSince = now
                    duration = now - upSince
                else:
                    # we are up
                    upSince = now
                    duration = now - downSince

                msg = '%s connectivity changed to %s (%s: %s)' % (
                    now.strftime('%Y-%m-%d %H:%M:%S'),
                    connectivity,
                    'downtime' if connectivity else 'uptime',
                    duration)

                if connectivity and duration < self.minInterruption:
                    # minimum interruption time not reached, ignore it
                    msg += ' (ignored)'
                    # remove last message about up->down change
                    msgList.pop()
                else:
                    msgList.append(msg)

                print(msg)

            if msgList and connectivity:
                # send mail report if enough time passed between last mail
                if not mailBackoff or now > (mailLastSend + datetime.timedelta(seconds=mailBackoff)):
                    try:
                        mail = sendMail.pySendMail()
                        mail.subject = 'pyNetConnMon'
                        mail.content = '\n'.join(msgList)
                        mail.send()

                        msgList = list()

                        mailLastSend = now
                        if not mailBackoff:
                            mailBackoff = self.backoffMin
                        else:
                            mailBackoff += self.backoffStep
                        mailBackoff = min(mailBackoff, self.backoffMax)
                    except Exception as e:
                        print('failed to send mail: %s, will try again' % e)

            if mailBackoff and \
               now > (mailLastSend + datetime.timedelta(seconds=self.backoffMax)):
                # reset current backoff if we didn't send any mail recently
                mailBackoff = None

            if not connectivityChange:
                # only sleep when nothing has changed
                time.sleep(self.checkInterval)

            lastConnectivity = connectivity

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Monitor Internet or network connectivity and report downtime via mail.'
                        '\n\nAll time-based arguments are specified in seconds.')
    parser.add_argument('-a', '--address', help='host address to check (default: %s)' % pyNetConnMon.defaultHost)
    parser.add_argument('-p', '--port', type=int, help='host port to check (default: %d)' % pyNetConnMon.defaultPort)
    parser.add_argument('-i', '--interval', type=float, help='check interval (default: %.1f)' % pyNetConnMon.defaultCheckInterval)
    parser.add_argument('-t', '--timeout', type=float, help='connection timeout (default: %.1f)' % pyNetConnMon.defaultCheckTimeout)
    parser.add_argument('-m', '--min-interruption', type=float, help='ignore interruptions smaller than this (default: %.1f)' % pyNetConnMon.defaultMinInterruption)
    parser.add_argument('-bmin', '--backoff-min', type=float, help='minimum time to pass between mail reports (for backoff, default: %.1f)' % pyNetConnMon.defaultBackoffMin)
    parser.add_argument('-bmax', '--backoff-max', type=float, help='maximum time to pass between mail reports (for backoff, default: %.1f)' % pyNetConnMon.defaultBackoffMax)
    parser.add_argument('-bstep', '--backoff-step', type=float, help='backoff wait time increment for subsequent connection losses (default: %.1f)' % pyNetConnMon.defaultBackoffStep)
    args = parser.parse_args()

    mon = pyNetConnMon()

    if args.address:
        mon.host = args.address
    if args.port:
        mon.port = args.port
    if args.interval:
        mon.checkInterval = args.interval
    if args.timeout:
        mon.checkTimeout = args.timeout
    if args.min_interruption:
        mon.minInterruption = args.min_interruption
    if args.backoff_min:
        mon.backoffMin = args.backoff_min
    if args.backoff_max:
        mon.backoffMax = args.backoff_max
    if args.backoff_step:
        mon.backoffStep = args.backoff_step

    mon.monitor()
