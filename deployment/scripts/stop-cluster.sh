#!/bin/bash
set -e

echo "🛑 Stopping DiagnoAI Cluster..."

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo "📉 Scaling down deployment..."
kubectl scale deployment diagnoai -n diagnoai --replicas=0

echo "⏳ Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=diagnoai -n diagnoai --timeout=180s || true

echo "🔄 Stopping k3s cluster..."
sudo systemctl stop k3s

echo "✅ Cluster stopped successfully!"
echo "💾 All data preserved in PVCs for next start"