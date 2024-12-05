#!/bin/bash
gunicorn -w 1 -b 0.0.0.0:5003 app:app --timeout 600