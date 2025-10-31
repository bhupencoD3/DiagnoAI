#!/bin/bash
set -e

echo "🚀 Starting DiagnoAI Cluster..."

# Start k3s if not running
if ! sudo systemctl is-active k3s >/dev/null 2>&1; then
    echo "🔧 Starting k3s cluster..."
    sudo systemctl start k3s
    sleep 15
fi

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

kubectl apply -f deployment/k8s/namespace.yaml

kubectl apply -f deployment/k8s/vector-store-pvc.yaml
kubectl apply -f deployment/k8s/data-pvc.yaml

echo "⏳ Waiting for PVCs to be bound..."
kubectl wait --for=condition=ready pvc vector-store-pvc -n diagnoai --timeout=120s
kubectl wait --for=condition=ready pvc data-pvc -n diagnoai --timeout=120s

echo "🚀 Starting main application..."
kubectl apply -f deployment/k8s/secrets.yaml
kubectl apply -f deployment/k8s/configmap.yaml
kubectl apply -f deployment/k8s/deployment.yaml
kubectl apply -f deployment/k8s/service.yaml

echo "⏳ Waiting for main application to be ready..."
kubectl rollout status deployment/diagnoai -n diagnoai --timeout=600s

echo "📊 Cluster Status:"
kubectl get pods -n diagnoai -o wide

NODE_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "🌐 External Service URL: http://$NODE_IP:30080"
echo "✅ Cluster started successfully! Vector store data preserved."