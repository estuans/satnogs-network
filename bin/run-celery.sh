#!/bin/bash

celery -A network worker -B -l INFO
