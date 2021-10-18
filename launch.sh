#!/bin/sh
# to be run after starting up minikube
url=$(minikube service --url stochss-compute-service)
ngrok http $url