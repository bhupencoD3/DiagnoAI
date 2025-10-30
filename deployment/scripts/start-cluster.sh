#!/bin/bash
set -e

echo "🚀 Starting DiagnoAI Cluster with Grok API..."

kubectl apply -f deployment/k8s/namespace.yaml

kubectl apply -f deployment/k8s/vector-store-pvc.yaml
kubectl apply -f deployment/k8s/data-pvc.yaml

echo "⏳ Waiting for PVCs to be ready..."
kubectl wait --for=condition=ready pvc -l app -n diagnoai --timeout=120s

echo "🚀 Starting main application..."
kubectl apply -f deployment/k8s/secrets.yaml
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml
kubectl apply -f deployment/k8s/hpa.yaml

echo "⏳ Waiting for main application..."
kubectl rollout status deployment/diagnoai -n diagnoai --timeout=300s

echo "📊 Cluster Status:"
kubectl get pods -n diagnoai
echo ""
echo "🌐 Services:"
kubectl get svc -n diagnoai

SERVICE_IP=$(kubectl get svc diagnoai-service -n diagnoai -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$SERVICE_IP" ]; then
    SERVICE_IP=$(kubectl get svc diagnoai-service -n diagnoai -o jsonpath='{.spec.clusterIP}')
    echo "🔗 Internal Service URL: http://$SERVICE_IP:8000"
else
    echo "🌐 External Service URL: http://$SERVICE_IP:8000"
fi

echo "✅ Cluster started successfully!"