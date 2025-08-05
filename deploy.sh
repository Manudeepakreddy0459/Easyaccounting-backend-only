#!/bin/bash

echo "🚀 CA Assistant AI - Deployment Script"
echo "======================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Build the project
echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix the errors and try again."
    exit 1
fi

echo "✅ Build successful!"

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📝 Next steps:"
echo "1. Deploy your backend to Railway or Render"
echo "2. Update the API URL in src/components/AutoLedger.jsx"
echo "3. Set your SONAR_API_KEY environment variable"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions" 