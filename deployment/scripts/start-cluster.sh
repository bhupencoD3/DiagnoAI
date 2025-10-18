#!/bin/bash

set -e

echo "🚀 Starting DiagnoAI Cluster..."
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

# Create namespace
kubectl apply -f deployment/k8s/namespace.yaml

# Start PVCs first
kubectl apply -f deployment/k8s/ollama-pvc.yaml
kubectl apply -f deployment/k8s/vector-store-pvc.yaml
kubectl apply -f deployment/k8s/data-pvc.yaml

# Wait for PVCs to be bound
echo "⏳ Waiting for PVCs to be ready..."
kubectl wait --for=condition=ready pvc -l app -n diagnoai --timeout=120s

# Start Ollama first (model download takes longest)
echo "📥 Starting Ollama with Mistral model..."
kubectl apply -f deployment/k8s/ollama-deployment.yaml

# Wait for Ollama to be ready (with progress tracking)
echo "⏳ Waiting for Ollama to be ready (this can take 10-15 minutes)..."
for i in {1..60}; do
    if kubectl get pods -n diagnoai -l app=ollama -o jsonpath='{.items[0].status.phase}' 2>/dev/null | grep -q "Running"; then
        echo "✅ Ollama pod is running"
        break
    fi
    echo "⏱️  Still waiting for Ollama... ($i/60)"
    sleep 30
done

# Start main application
echo "🚀 Starting main application..."
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml

# Wait for main app
echo "⏳ Waiting for main application..."
kubectl rollout status deployment/diagnoai -n diagnoai --timeout=600s

# Get service info
echo "📊 Cluster Status:"
kubectl get pods -n diagnoai
echo ""
echo "🌐 Services:"
kubectl get svc -n diagnoai

# Get the service URL
SERVICE_IP=$(kubectl get svc diagnoai-service -n diagnoai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_IP" ]; then
    SERVICE_IP=$(kubectl get svc diagnoai-service -n diagnoai -o jsonpath='{.spec.clusterIP}')
    echo "🔗 Internal Service URL: http://$SERVICE_IP:8000"
else
    echo "🌐 External Service URL: http://$SERVICE_IP:8000"
fi

echo "✅ Cluster started successfully!"