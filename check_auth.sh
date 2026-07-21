#!/bin/bash
echo "🔐 Checking Authentication System"
echo "=================================="

# Check if API is running
echo ""
echo "1. Checking API status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "❌ API is not running - start with: uvicorn backend.server:app --reload"
    exit 1
fi

# Check auth endpoint
echo ""
echo "2. Testing authentication endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mitsumi.ai","password":"admin123"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ Auth endpoint working"
    echo "   Response: $(echo $RESPONSE | python3 -m json.tool 2>/dev/null | head -10)"
else
    echo "❌ Auth endpoint failed"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "3. Test users available:"
echo "   📧 admin@mitsumi.ai  🔑 admin123"
echo "   📧 user@mitsumi.ai   🔑 password123"
echo "   📧 test@example.com  🔑 test123"

echo ""
echo "4. Check backend files:"
[ -f "backend/app/routers/auth.py" ] && echo "✅ auth.py exists" || echo "❌ auth.py missing"
[ -f "frontend/src/api/client.ts" ] && echo "✅ client.ts exists" || echo "❌ client.ts missing"
[ -f "frontend/.env.local" ] && echo "✅ .env.local exists" || echo "❌ .env.local missing"

echo ""
echo "=================================="
echo "✅ Auth check complete!"
