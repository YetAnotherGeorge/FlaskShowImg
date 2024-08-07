#!/bin/bash
podman build . -t flaskshowimg --build-arg VERSION=1.0.8 --build-arg HOST="devbuild-oel.kbclab.ro" \
   && podman-compose up -d --force-recreate