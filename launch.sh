#!/bin/bash
gunicorn -w 1 --timeout 600 -b 0.0.0.0:5003 app:app
