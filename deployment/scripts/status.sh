#!/bin/bash
set -e

echo "📊 DiagnoAI Cluster Status"

# Check if k3s is running
if sudo systemctl is-active k3s >/dev/null 2>&1; then
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    
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

    # Check application health if running
    if kubectl get deployment diagnoai -n diagnoai &>/dev/null; then
        echo ""
        echo "🏥 Application Health:"
        POD_NAME=$(kubectl get pods -n diagnoai -l app=diagnoai -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        if [ -n "$POD_NAME" ]; then
            kubectl exec -it $POD_NAME -n diagnoai -- curl -s http://localhost:8000/health || echo "Health check failed"
        else
            echo "No running pods found"
        fi
    fi
    
    NODE_IP=$(hostname -I | awk '{print $1}')
    echo ""
    echo "🌐 Access URL: http://$NODE_IP:30080"
else
    echo "❌ k3s cluster is not running"
    echo "💡 Use the start-cluster.sh script to start the cluster"
fi