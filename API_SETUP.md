# 🔑 API Key Setup Guide

## Perplexity Sonar Pro API Key Setup

The AutoLedger feature uses Perplexity's Sonar Pro AI to classify bank transactions automatically. Here's how to set it up:

### **Step 1: Get Your API Key**

1. **Visit Perplexity AI:** Go to https://www.perplexity.ai/
2. **Sign Up/Login:** Create an account or log in
3. **Go to Settings:** Click on your profile → Settings
4. **API Section:** Navigate to the API section
5. **Generate Key:** Click "Generate API Key" or "Create New Key"
6. **Copy the Key:** Save your API key securely

### **Step 2: Set Up the API Key**

#### **Method 1: Using .env File (Recommended)**

1. **Edit the .env file:**
   ```bash
   cd backend
   nano .env
   ```

2. **Replace the placeholder with your actual API key:**
   ```env
   # Perplexity Sonar Pro API Key
   # Get your API key from: https://www.perplexity.ai/settings/api
   SONAR_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. **Save the file and restart the backend:**
   ```bash
   # Stop the current backend (Ctrl+C)
   # Then restart it
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```

#### **Method 2: Environment Variable**

1. **Set the environment variable:**
   ```bash
   export SONAR_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

2. **Start the backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```

#### **Method 3: Direct in Terminal**

1. **Start the backend with the API key:**
   ```bash
   cd backend
   source venv/bin/activate
   SONAR_API_KEY="pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```

### **Step 3: Verify Setup**

1. **Check API Status:**
   ```bash
   curl http://localhost:8001/api/health
   ```

2. **Expected Response:**
   ```json
   {
     "status": "healthy",
     "api_key_configured": true
   }
   ```

### **Step 4: Test the AI Classification**

1. **Upload a bank statement PDF** in the AutoLedger interface
2. **Look for AI suggestions** in the "Flagged" tab
3. **Transactions should show AI classification** instead of "API key not configured"

## 🔒 Security Notes

- **Never commit your API key** to version control
- **Keep your .env file secure** and don't share it
- **The .env file is already in .gitignore** to prevent accidental commits
- **Rotate your API key** periodically for security

## 💰 Pricing

- **Perplexity Sonar Pro** has usage-based pricing
- **Check current rates** at https://www.perplexity.ai/pricing
- **Monitor your usage** in your Perplexity dashboard

## 🚨 Troubleshooting

### **API Key Not Working**

1. **Check the key format:** Should start with `pplx-`
2. **Verify the key is valid:** Test it in the Perplexity dashboard
3. **Check environment variable:** `echo $SONAR_API_KEY`
4. **Restart the backend** after setting the key

### **Rate Limiting**

1. **Check your usage** in Perplexity dashboard
2. **Upgrade your plan** if needed
3. **Implement caching** for repeated requests

### **No AI Suggestions**

1. **Verify API key is set:** Check `/api/health` endpoint
2. **Check browser console** for errors
3. **Ensure backend is running** on port 8001

## 📞 Support

- **Perplexity API Docs:** https://docs.perplexity.ai/
- **API Status:** https://status.perplexity.ai/
- **Contact Support:** Through Perplexity dashboard

## 🔄 Alternative Setup

If you don't want to use AI classification:

1. **The app will work without the API key**
2. **Transactions will be classified using basic rules**
3. **Manual review will be required** for ambiguous transactions
4. **All other features** (PDF parsing, ledger generation, P&L) will work normally 