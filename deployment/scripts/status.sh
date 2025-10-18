#!/bin/bash

set -e

echo "📊 DiagnoAI Cluster Status"
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

echo ""
echo "📦 Pods:"
kubectl get pods -n diagnoai -o wide

echo ""
echo "🔧 Services:"
kubectl get svc -n diagnoai

echo ""
echo "💾 PVCs:"
kubectl get pvc -n diagnoai

echo ""
echo "📈 Deployments:"
kubectl get deployments -n diagnoai

# Check app health
if kubectl get deployment diagnoai -n diagnoai &>/dev/null; then
    echo ""
    echo "🏥 Application Health:"
    kubectl exec -it deployment/diagnoai -n diagnoai -- curl -s http://localhost:8000/health || echo "Health check failed"
fi