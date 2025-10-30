#!/bin/bash
set -e

echo "🚀 Deploying DiagnoAI with Grok API..."

KUBE_CMD="kubectl --request-timeout=30s"

echo "🔧 Applying manifests..."

$KUBE_CMD apply -f deployment/k8s/namespace.yaml --validate=false
echo "✅ Namespace created"

$KUBE_CMD apply -f deployment/k8s/vector-store-pvc.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/data-pvc.yaml --validate=false
echo "✅ PVCs created"

$KUBE_CMD apply -f deployment/k8s/secrets.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/configmap.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/deployment.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/service.yaml --validate=false
$KUBE_CMD apply -f deployment/k8s/hpa.yaml --validate=false
echo "✅ DiagnoAI application deployed"

echo "⏳ Waiting for DiagnoAI to be ready..."
$KUBE_CMD rollout status deployment/diagnoai -n diagnoai --timeout=300s

echo "✅ Deployment completed!"
echo "📊 Checking services..."
$KUBE_CMD get all -n diagnoai

EXTERNAL_IP=$($KUBE_CMD get svc diagnoai-service -n diagnoai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' || echo "Pending")
echo "🌐 Your DiagnoAI will be available at: http://$EXTERNAL_IP:8000"