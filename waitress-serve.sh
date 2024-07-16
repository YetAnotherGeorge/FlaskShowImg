#!/bin/bash

waitress-serve --port=8020 --call 'flaskr:create_app'