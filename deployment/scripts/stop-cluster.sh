#!/bin/bash
set -e

echo "🛑 Stopping DiagnoAI Cluster..."
echo "$KUBECONFIG" > kubeconfig
export KUBECONFIG=kubeconfig

echo "📉 Scaling down deployment..."
kubectl scale deployment diagnoai -n diagnoai --replicas=0

echo "⏳ Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=diagnoai -n diagnoai --timeout=180s

echo "✅ Cluster stopped successfully!"
echo "💾 All data preserved in PVCs for next start"