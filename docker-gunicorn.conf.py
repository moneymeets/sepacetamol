bind = "0.0.0.0:8000"
worker = 2
threads = 4
keepalive = 5
wsgi_app = "config.wsgi"
loglevel = "debug"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" "%(M)s"'
errorlog = "-"  # log to stderr
accesslog = "-"  # log to stdout
# Enable inheritance for stdio file descriptors in daemon mode, allows to stream more logs to stdout
enable_stdio_inheritance = True
