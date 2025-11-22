#!/bin/bash

docker run --rm --env AIRUN_API_KEY=${AIRUN_API_KEY} -p 8000:8000 diia_translate:latest
