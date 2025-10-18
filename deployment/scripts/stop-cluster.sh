#!/bin/bash

set -e

echo "🛑 Stopping DiagnoAI Cluster..."
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

# Scale down deployments to 0 (preserves PVCs)
echo "📉 Scaling down deployments..."
kubectl scale deployment diagnoai -n diagnoai --replicas=0
kubectl scale deployment ollama -n diagnoai --replicas=0

# Wait for pods to terminate
echo "⏳ Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app -n diagnoai --timeout=300s

echo "✅ Cluster stopped successfully!"
echo "💾 All data preserved in PVCs for next start"