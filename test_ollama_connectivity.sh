#!/bin/bash

echo "Testing Ollama connectivity to 192.168.3.10..."
echo "=============================================="

# Test common Ollama ports and endpoints
REMOTE_IP="192.168.3.10"
PORTS=("11434" "8080" "8000" "3000")
ENDPOINTS=("/api/tags" "/v1/models" "/api/version")

for PORT in "${PORTS[@]}"; do
    echo "Testing port $PORT..."
    
    for ENDPOINT in "${ENDPOINTS[@]}"; do
        echo -n "  Checking http://$REMOTE_IP:$PORT$ENDPOINT ... "
        
        if curl -s --connect-timeout 5 "http://$REMOTE_IP:$PORT$ENDPOINT" > /dev/null 2>&1; then
            echo "✅ SUCCESS"
            echo "    URL: http://$REMOTE_IP:$PORT$ENDPOINT"
            echo "    Response:"
            curl -s "http://$REMOTE_IP:$PORT$ENDPOINT" | head -5
            echo ""
        else
            echo "❌ Failed"
        fi
    done
    echo ""
done

echo "Testing with OpenAI-compatible endpoint..."
for PORT in "${PORTS[@]}"; do
    echo -n "  Testing OpenAI endpoint http://$REMOTE_IP:$PORT/v1/models ... "
    
    if curl -s --connect-timeout 5 "http://$REMOTE_IP:$PORT/v1/models" > /dev/null 2>&1; then
        echo "✅ SUCCESS - This should work with the app!"
        echo "    Configure base_url as: http://$REMOTE_IP:$PORT/v1"
        echo "    Response:"
        curl -s "http://$REMOTE_IP:$PORT/v1/models" | jq . 2>/dev/null || curl -s "http://$REMOTE_IP:$PORT/v1/models"
        echo ""
    else
        echo "❌ Failed"
    fi
done
