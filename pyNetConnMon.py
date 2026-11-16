#!/usr/bin/env python3
# -*- coding: utf-8 -*

import argparse
import datetime
import socket
import time

from pySendMail import sendMail

class pyNetConnMon:
    default_address = '8.8.8.8'
    default_port = 53

    # all settings are specified in seconds
    default_interval = 2.0
    default_timeout = 2.0
    default_min_interruption = 5.0
    default_backoff_min = 1.0 * 60.0
    default_backoff_max = 60.0 * 60.0
    default_backoff_step = 5.0 * 60.0

    time_stamp_format = '%Y-%m-%d %H:%M:%S'
    mail_subject = 'pyNetConnMon'

    def __init__(self):
        self.address = self.default_address
        self.port = self.default_port

        # all settings are specified in seconds
        self.interval = self.default_interval
        self.timeout = self.default_timeout
        self.min_interruption = self.default_min_interruption
        self.backoff_min = self.default_backoff_min
        self.backoff_max = self.default_backoff_max
        self.backoff_step = self.default_backoff_step

        # mail state
        self.msg_list = list()
        self.mail_last_send = datetime.datetime.fromtimestamp(0)
        self.mail_backoff = None
        self.now = None

    def checkConnectivity(self):
        try:
            socket.setdefaulttimeout(self.timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.address, self.port))
            return True
        except socket.error as ex:
            return False
        except Exception as e:
            print(e)
            return False

    def sendMailReport(self):
        try:
            mail = sendMail.pySendMail()
            mail.subject = self.mail_subject
            mail.content = '\n'.join(self.msg_list)
            mail.send()

            self.msg_list = list()

            self.mail_last_send = self.now
            if not self.mail_backoff:
                self.mail_backoff = self.backoff_min
            else:
                self.mail_backoff += self.backoff_step
            self.mail_backoff = min(self.mail_backoff, self.backoff_max)
        except Exception as e:
            print('failed to send mail: %s, will try again' % e)

    def monitor(self):
        last_connectivity = True
        up_since = down_since = datetime.datetime.now()
        while True:
            self.now = datetime.datetime.now()
            connectivity = self.checkConnectivity()
            connectivity_change = connectivity != last_connectivity
            if connectivity_change:
                if not connectivity:
                    # we are down
                    down_since = self.now
                    duration = self.now - up_since
                else:
                    # we are up
                    up_since = self.now
                    duration = self.now - down_since

                msg = '%s connectivity changed to %s (%s: %s)' % (
                    self.now.strftime(self.time_stamp_format),
                    connectivity,
                    'downtime' if connectivity else 'uptime',
                    duration)

                if connectivity and duration < datetime.timedelta(seconds=self.min_interruption):
                    # minimum interruption time not reached, ignore it
                    msg += ' (ignored)'
                    # remove last message about up->down change
                    self.msg_list.pop()
                else:
                    self.msg_list.append(msg)

                print(msg)

            if self.msg_list and connectivity:
                # send mail report if enough time passed between last mail
                if not self.mail_backoff or self.now > (self.mail_last_send + datetime.timedelta(seconds=self.mail_backoff)):
                    self.sendMailReport()

            if self.mail_backoff and \
               self.now > (self.mail_last_send + datetime.timedelta(seconds=self.backoff_max)):
                # reset current backoff if we didn't send any mail recently
                self.mail_backoff = None

            if not connectivity_change:
                # only sleep when nothing has changed
                time.sleep(self.interval)

            last_connectivity = connectivity

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Monitor Internet or network connectivity and report downtime via mail.'
                        '\n\nAll time-based arguments are specified in seconds.')
    parser.add_argument('-a', '--address', help='host address to check (default: %s)' % pyNetConnMon.default_address)
    parser.add_argument('-p', '--port', type=int, help='host port to check (default: %d)' % pyNetConnMon.default_port)
    parser.add_argument('-i', '--interval', type=float, help='check interval (default: %.1f)' % pyNetConnMon.default_interval)
    parser.add_argument('-t', '--timeout', type=float, help='connection timeout (default: %.1f)' % pyNetConnMon.default_timeout)
    parser.add_argument('-m', '--min-interruption', type=float, help='ignore interruptions smaller than this (default: %.1f)' % pyNetConnMon.default_min_interruption)
    parser.add_argument('-bmin', '--backoff-min', type=float, help='minimum time to pass between mail reports (for backoff, default: %.1f)' % pyNetConnMon.default_backoff_min)
    parser.add_argument('-bmax', '--backoff-max', type=float, help='maximum time to pass between mail reports (for backoff, default: %.1f)' % pyNetConnMon.default_backoff_max)
    parser.add_argument('-bstep', '--backoff-step', type=float, help='backoff wait time increment for subsequent connection losses (default: %.1f)' % pyNetConnMon.default_backoff_step)
    parser.add_argument('-s', '--start', action='store_true', help='send a mail at startup')
    args = parser.parse_args()

    mon = pyNetConnMon()

    for arg_name in ['address', 'port', 'interval', 'timeout', 'min_interruption', 'backoff_min', 'backoff_max', 'backoff_step']:
        value = getattr(args, arg_name)
        if value is not None:
            setattr(mon, arg_name, value)

    if args.start:
        try:
            mail = sendMail.pySendMail()
            mail.subject = mon.mail_subject
            mail.content = '%s Starting network connectivity monitoring' % datetime.datetime.now().strftime(mon.time_stamp_format)
            mail.send()
        except Exception as e:
            print('failed to send startup mail: %s' % e)

    mon.monitor()
