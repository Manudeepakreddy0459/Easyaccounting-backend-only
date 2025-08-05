# 🚀 CA Assistant AI - Deployment Guide

## 📋 Prerequisites

1. **GitHub Account** - For code hosting
2. **API Key** - Perplexity Sonar Pro API key
3. **Node.js & npm** - For building the frontend

## 🎯 Deployment Options

### Option 1: Vercel (Frontend Only) + Railway (Backend) - RECOMMENDED

#### Frontend (Vercel):
1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Build the project:**
   ```bash
   npm run build
   ```

3. **Deploy to Vercel:**
   ```bash
   vercel
   ```

4. **Update API URL:**
   - After backend deployment, update `src/components/AutoLedger.jsx`
   - Change `http://localhost:8001` to your backend URL

#### Backend (Railway):
1. **Go to [Railway.app](https://railway.app)**
2. **Connect your GitHub repository**
3. **Create new service → Deploy from GitHub repo**
4. **Set environment variables:**
   - `SONAR_API_KEY`: Your Perplexity API key
5. **Deploy**

### Option 2: Railway (Full Stack)

1. **Go to [Railway.app](https://railway.app)**
2. **Connect your GitHub repository**
3. **Create new service → Deploy from GitHub repo**
4. **Set environment variables:**
   - `SONAR_API_KEY`: Your Perplexity API key
5. **Configure build settings:**
   - Build Command: `npm install && npm run build`
   - Start Command: `npm run dev`
6. **Deploy**

### Option 3: Render (Full Stack)

1. **Go to [Render.com](https://render.com)**
2. **Connect your GitHub repository**
3. **Create new Web Service**
4. **Configure:**
   - Build Command: `npm install && npm run build`
   - Start Command: `npm run dev`
5. **Set environment variables:**
   - `SONAR_API_KEY`: Your Perplexity API key
6. **Deploy**

### Option 4: Heroku (Full Stack)

1. **Install Heroku CLI:**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variables:**
   ```bash
   heroku config:set SONAR_API_KEY=your_api_key_here
   ```

4. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

## 🔧 Environment Variables

Set these in your deployment platform:

```bash
SONAR_API_KEY=your_perplexity_api_key_here
NODE_ENV=production
```

## 📝 Post-Deployment Checklist

### ✅ Frontend Updates Needed:
1. **Update API URL** in `src/components/AutoLedger.jsx`:
   ```javascript
   // Change from:
   const response = await fetch('http://localhost:8001/api/autoledger/process', {
   
   // To your backend URL:
   const response = await fetch('https://your-backend-url.com/api/autoledger/process', {
   ```

2. **Update CORS settings** in `backend/main.py`:
   ```python
   allow_origins=["https://your-frontend-url.com", "http://localhost:5173"],
   ```

### ✅ Backend Updates Needed:
1. **Update CORS origins** in `backend/main.py`
2. **Set production environment variables**
3. **Test API endpoints**

## 🧪 Testing Deployment

1. **Health Check:**
   ```bash
   curl https://your-backend-url.com/api/health
   ```

2. **Test File Upload:**
   - Go to your deployed frontend
   - Upload a PDF file
   - Check if processing works

## 🔒 Security Considerations

1. **API Key Security:**
   - Never commit API keys to Git
   - Use environment variables
   - Rotate keys regularly

2. **CORS Configuration:**
   - Only allow your frontend domain
   - Remove localhost in production

3. **File Upload Limits:**
   - Set reasonable file size limits
   - Validate file types

## 🚨 Troubleshooting

### Common Issues:

1. **CORS Errors:**
   - Update CORS origins in backend
   - Check frontend URL is correct

2. **API Key Not Working:**
   - Verify environment variable is set
   - Check API key is valid

3. **Build Failures:**
   - Check Node.js version compatibility
   - Verify all dependencies are installed

4. **File Upload Issues:**
   - Check file size limits
   - Verify PDF format support

## 📞 Support

If you encounter issues:
1. Check the deployment platform logs
2. Verify environment variables are set
3. Test locally first
4. Check API documentation

## 🎉 Success!

Once deployed, your CA Assistant AI will be available at:
- **Frontend:** `https://your-app-name.vercel.app`
- **Backend:** `https://your-backend-url.com`
- **API Docs:** `https://your-backend-url.com/docs` 