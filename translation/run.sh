#!/bin/bash

docker run --rm --env AIRUN_API_KEY=${AIRUN_API_KEY} -p 7777:7777 diia_translate:latest
