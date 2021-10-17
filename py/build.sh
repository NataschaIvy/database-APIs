#!/bin/bash
docker build -t registry.ivy.cx/api:latest .
docker push registry.ivy.cx/api:latest 
kubectl delete pod -n api --selector=app=api
kubectl get pods -n api --watch
