#!/bin/bash
echo "🔐 Testing Login Endpoint"
echo "========================="

echo ""
echo "Testing admin login..."
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mitsumi.ai","password":"admin123"}' | python3 -m json.tool

echo ""
echo "Testing user login..."
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@mitsumi.ai","password":"password123"}' | python3 -m json.tool

echo ""
echo "Testing test user login..."
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | python3 -m json.tool
