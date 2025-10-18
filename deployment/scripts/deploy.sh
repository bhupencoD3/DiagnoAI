#!/bin/bash
set -e

echo "🚀 Deploying DiagnoAI..."
echo "🔧 Using kubeconfig file: $KUBECONFIG_FILE"

# Get absolute path to kubeconfig
KUBECONFIG_PATH=$(realpath "$KUBECONFIG_FILE")
echo "📁 Kubeconfig absolute path: $KUBECONFIG_PATH"

# Use explicit --kubeconfig flag with absolute path for EVERY command
KUBE_CMD="kubectl --kubeconfig=$KUBECONFIG_PATH --request-timeout=30s"

# Skip connection test and go straight to deployment
echo "🔧 Applying manifests with validation disabled..."

# Apply base resources with validation disabled
$KUBE_CMD apply -f deployment/k8s/namespace.yaml --validate=false
echo "✅ Namespace created"

$KUBE_CMD apply -f deployment/k8s/ollama-pvc.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/vector-store-pvc.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/data-pvc.yaml --validate=false
echo "✅ PVCs created"

# Start Ollama FIRST (model download takes 15-20 mins)
echo "📦 Deploying Ollama..."
$KUBE_CMD apply -f deployment/k8s/ollama-deployment.yaml --validate=false
echo "✅ Ollama deployment started"

# Wait for Ollama to be ready (with validation disabled)
echo "⏳ Waiting for Ollama to download Mistral model (this takes 15-20 minutes)..."
$KUBE_CMD wait --for=condition=ready pod -l app=ollama -n diagnoai --timeout=2400s --validate=false
echo "✅ Ollama is ready"

# Deploy main application
echo "🚀 Deploying DiagnoAI application..."
$KUBE_CMD apply -f deployment/k8s/configmap.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/deployment.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/service.yaml --validate=false
echo "✅ DiagnoAI application deployed"

# Wait for main app
echo "⏳ Waiting for DiagnoAI to be ready..."
$KUBE_CMD rollout status deployment/diagnoai -n diagnoai --timeout=300s

# Get service info
echo "✅ Deployment completed!"
echo "📊 Checking services..."
$KUBE_CMD get all -n diagnoai

# Get external IP
EXTERNAL_IP=$($KUBE_CMD get svc diagnoai-service -n diagnoai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || echo "Pending")
echo "🌐 Your DiagnoAI will be available at: http://$EXTERNAL_IP:8000"