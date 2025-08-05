#!/bin/bash

echo "🔨 CA Assistant AI - Production Build"
echo "===================================="

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist
rm -rf node_modules/.vite

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project
echo "🔨 Building for production..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "📁 Build output: ./dist/"
    echo "📊 Build size:"
    du -sh dist/
    echo ""
    echo "🚀 Ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "1. Run: ./deploy.sh (for Vercel)"
    echo "2. Or upload ./dist/ to your hosting provider"
    echo "3. Don't forget to deploy your backend!"
else
    echo "❌ Build failed!"
    exit 1
fi 