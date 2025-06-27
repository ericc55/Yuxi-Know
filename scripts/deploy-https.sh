#!/bin/bash

echo "🚀 Setting up HTTPS for yuknow.net..."

# Check if Docker is running
if ! sudo docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Stop existing services
echo "🛑 Stopping existing services..."
sudo docker compose down

# Build and start the core services (without nginx first)
echo "🏗️  Building and starting core services..."
sudo docker compose up -d api web graph etcd minio milvus

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Initialize Let's Encrypt certificates
echo "🔐 Setting up SSL certificates..."
sudo ./scripts/init-letsencrypt.sh

echo "✅ HTTPS setup complete!"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "   https://yuknow.net"
echo ""
echo "📝 Note: If this is the first time setting up SSL, it may take a few minutes"
echo "   for the certificates to propagate. If you encounter issues, try:"
echo "   sudo docker compose logs nginx"
echo "   sudo docker compose logs certbot" 