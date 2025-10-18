#!/bin/bash

set -e

echo "🚀 Deploying DiagnoAI..."
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

# Apply all configurations
kubectl apply -f deployment/k8s/namespace.yaml
kubectl apply -f deployment/k8s/ollama-pvc.yaml
kubectl apply -f deployment/k8s/vector-store-pvc.yaml   
kubectl apply -f deployment/k8s/data-pvc.yaml
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/ollama-deployment.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml

# Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/diagnoai -n diagnoai --timeout=600s

echo "✅ Deployment completed successfully!"