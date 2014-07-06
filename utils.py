#coding:utf-8

import os
import sys
import signal
import atexit
from signal import SIGTERM

class Daemon(object):
    def __init__(self, pidfile,curdir='/', stdin='/dev/null', stdout=sys.stderr, stderr=sys.stderr):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.curdir= curdir

    def _daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
        os.setsid()
        os.chdir(self.curdir)
        os.umask(0)
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        os.dup2(si.fileno(), sys.stdin.fileno())
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write('%s\n' % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running?\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        self._daemonize()
        self._run()

    def stop(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?\n'
            sys.stderr.write(message % self.pidfile)
            return

        try:
            while 1:
                os.kill(pid, SIGTERM)
        except OSError, err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

