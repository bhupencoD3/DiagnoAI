#!/bin/bash
set -e

echo "🚀 Deploying DiagnoAI..."
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

# Apply base resources
kubectl apply -f deployment/k8s/namespace.yaml
kubectl apply -f deployment/k8s/ollama-pvc.yaml
kubectl apply -f deployment/k8s/vector-store-pvc.yaml
kubectl apply -f deployment/k8s/data-pvc.yaml

# Start Ollama FIRST (model download takes 15-20 mins)
echo "📦 Deploying Ollama..."
kubectl apply -f deployment/k8s/ollama-deployment.yaml

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to download Mistral model (this takes 15-20 minutes)..."
kubectl wait --for=condition=ready pod -l app=ollama -n diagnoai --timeout=2400s

# Deploy main application
echo "🚀 Deploying DiagnoAI application..."
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml

# Wait for main app
echo "⏳ Waiting for DiagnoAI to be ready..."
kubectl rollout status deployment/diagnoai -n diagnoai --timeout=300s

# Get service info
echo "✅ Deployment completed!"
echo "📊 Checking services..."
kubectl get all -n diagnoai

# Get external IP
EXTERNAL_IP=$(kubectl get svc diagnoai-service -n diagnoai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || echo "Pending")
echo "🌐 Your DiagnoAI will be available at: http://$EXTERNAL_IP:8000"