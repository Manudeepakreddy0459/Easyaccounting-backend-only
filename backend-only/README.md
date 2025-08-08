# EasyAccounting Backend API

A FastAPI-based backend service for the EasyAccounting application that provides automated ledger processing from bank statement PDFs.

## 🚀 Live API

**Production URL**: https://easyaccounting-backend-only-production.up.railway.app

## 📋 Features

- **PDF Processing**: Extract transactions from bank statement PDFs
- **AI Classification**: Use Perplexity AI to classify ambiguous transactions
- **Ledger Generation**: Automatically generate double-entry ledger entries
- **P&L Calculation**: Compute profit and loss summaries
- **CORS Enabled**: Ready for frontend integration

## 🛠️ API Endpoints

### Health Check
```
GET /api/health
```
Returns service health status and configuration info.

### CORS Test
```
GET /api/test-cors
```
Test endpoint to verify CORS configuration.

### Process Bank Statement
```
POST /api/autoledger/process
```
Upload a bank statement PDF and get processed ledger entries.

**Request**: Multipart form data with PDF file
**Response**: JSON with transactions, ledger entries, and P&L summary

## 🏗️ Tech Stack

- **Framework**: FastAPI
- **PDF Processing**: pdfplumber, pypdfium2
- **AI Integration**: Perplexity AI (Sonar API)
- **Data Processing**: pandas, numpy
- **Deployment**: Railway with Nixpacks

## 📦 Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pdfplumber==0.10.3
pandas>=2.2.0
requests==2.31.0
python-dotenv==1.0.0
```

## 🚀 Deployment

### Railway Configuration
- **Runtime**: Python 3.12
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check**: `/api/health`

### Environment Variables
- `SONAR_API_KEY`: Perplexity AI API key for transaction classification (optional)

## 📡 CORS Configuration

The API accepts requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (React dev server)
- `https://easyaccountings.web.app` (Firebase production)
- `https://caassistant.ai` (Custom domain)

## 🔍 Transaction Processing Flow

1. **PDF Upload**: Receive bank statement PDF via API
2. **Text Extraction**: Extract transaction data using pdfplumber
3. **Pattern Matching**: Identify dates, amounts, and transaction types
4. **AI Classification**: Use Perplexity AI for ambiguous transactions
5. **Ledger Generation**: Create double-entry accounting entries
6. **P&L Calculation**: Compute income, expenses, and net profit

## 📊 Response Format

```json
{
  "summary": {
    "total_transactions": 25,
    "flagged_transactions": 2,
    "cleaned_transactions": 25,
    "ledger_entries": 50,
    "total_income": 15000.00,
    "total_expense": 8500.00,
    "net_profit": 6500.00
  },
  "transactions": [...],
  "flagged_transactions": [...],
  "cleaned_transactions": [...],
  "ledger_entries": [...],
  "pnl_summary": {...}
}
```

## 🔧 Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in `.env` file
4. Run the server: `uvicorn main:app --reload`

## 📈 Status

✅ **Deployed and Running**  
✅ **API Endpoints Functional**  
✅ **CORS Configured**  
✅ **Health Checks Passing**  

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the EasyAccounting application suite.
