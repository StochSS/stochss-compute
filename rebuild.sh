#!/bin/sh
# use this to force redeployment and update source docker image
docker build -t mdip226/stochss-compute:latest -f api.dockerfile .
docker push mdip226/stochss-compute:latest
cd kubernetes
kubectl delete -f api_deployment.yaml
kubectl delete --all pods
kubectl apply -f api_deployment.yaml
cd ..
# open up jupyter for testing
# source ./env/bin/activate
# cd ./examples
# jupyter notebook .
