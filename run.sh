#!/bin/sh
gunicorn main:app -w 2 --threads 2 --access-logfile - -b 0.0.0.0:${PORT}
