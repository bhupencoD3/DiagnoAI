#!/bin/bash
set -e

echo "🚀 Deploying DiagnoAI with Grok API..."

KUBE_CMD="kubectl"

echo "🔧 Applying manifests..."

$KUBE_CMD apply -f deployment/k8s/namespace.yaml
echo "✅ Namespace created"

$KUBE_CMD apply -f deployment/k8s/vector-store-pvc.yaml
$KUBE_CMD apply -f deployment/k8s/data-pvc.yaml
echo "✅ PVCs created"

$KUBE_CMD apply -f deployment/k8s/secrets.yaml
$KUBE_CMD apply -f deployment/k8s/configmap.yaml
$KUBE_CMD apply -f deployment/k8s/deployment.yaml
$KUBE_CMD apply -f deployment/k8s/service.yaml
echo "✅ DiagnoAI application deployed"

echo "⏳ Waiting for DiagnoAI to be ready..."
$KUBE_CMD rollout status deployment/diagnoai -n diagnoai --timeout=600s

echo "✅ Deployment completed!"

NODE_IP=$(hostname -I | awk '{print $1}')
echo "📊 Current status:"
$KUBE_CMD get all -n diagnoai

echo ""
echo "🌐 Your DiagnoAI is available at: http://$NODE_IP:30080"
echo "💾 Vector store data is persisted in PVCs"