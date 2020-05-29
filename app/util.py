import syslog
import os
import datetime as dt

def log(text, log_level=None):
    print("[{}] {}".format(dt.datetime.now().strftime("%H:%M:%S"), text))
    if (log_level == None):
        log_level = syslog.LOG_NOTICE

    syslog.syslog(log_level, text)

def import_env():
    filepath = os.path.dirname(os.path.realpath(__file__)) + "/../.env"
    if not os.path.isfile(filepath):
        return

    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            parts = line.split("=", 1)
            if len(parts) == 2:
                os.environ[parts[0].strip()] = parts[1].strip()