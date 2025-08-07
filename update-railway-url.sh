#!/bin/bash

echo "🚀 Railway Backend Connection Setup"
echo "=================================="
echo ""

# Get Railway URL from user
read -p "Enter your Railway backend URL (e.g., https://myapp.railway.app): " RAILWAY_URL

if [ -z "$RAILWAY_URL" ]; then
    echo "❌ No URL provided. Exiting."
    exit 1
fi

# Update .env file
echo "VITE_API_URL=$RAILWAY_URL" > .env
echo "✅ Updated .env file with Railway URL: $RAILWAY_URL"

# Build and deploy
echo ""
echo "🔨 Building frontend..."
npm run build

echo ""
echo "🚀 Deploying to Firebase..."
firebase deploy --only hosting

echo ""
echo "✅ Done! Your app should now be connected to Railway backend."
echo "🌐 Visit: https://easyaccountings.web.app"
echo ""
echo "📝 Note: Make sure your Railway backend has the SONAR_API_KEY environment variable set." 