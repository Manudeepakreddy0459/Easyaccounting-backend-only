# CA Assistant AI - Professional Accounting Dashboard

A comprehensive accounting dashboard for Chartered Accountants with AutoLedger functionality for automated bank statement processing.

## 🚀 Features

### Dashboard
- **Professional CA Dashboard** with modern UI
- **Key Metrics** tracking (clients, projects, revenue)
- **Quick Actions** for common tasks
- **Recent Activities** monitoring
- **Feature Cards** for different modules

### AutoLedger (Available Now)
- **PDF Bank Statement Processing** (SBI format)
- **AI-Powered Transaction Classification** using Perplexity Sonar Pro
- **Automatic Ledger Generation** with double-entry bookkeeping
- **Profit & Loss Reports** with detailed breakdowns
- **Transaction Analysis** with counterparty identification
- **Export Functionality** (JSON format)

### Coming Soon
- Journal Entries Management
- Ledger View with drill-down capabilities
- GST Filing automation
- TDS Filing management
- Client Database
- Push to Tally integration
- Compliance Alerts

## 🛠️ Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8 or higher
- Perplexity Sonar Pro API key (optional, for AI classification)

### Frontend Setup (React + Vite)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Access the application:**
   - Open http://localhost:5173 in your browser

### Backend Setup (FastAPI)

1. **Start the backend server:**
   ```bash
   ./start_backend.sh
   ```
   
   Or manually:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API documentation:**
   - Open http://localhost:8001/docs in your browser

### Environment Variables (Optional)

For AI-powered transaction classification, set the Perplexity API key:

```bash
export SONAR_API_KEY="your_perplexity_api_key_here"
```

## 📖 Usage

### Using AutoLedger

1. **Access AutoLedger:**
   - Click on the "Auto Ledger" feature card from the dashboard
   - Or navigate to the AutoLedger page

2. **Upload Bank Statement:**
   - Click "Choose PDF file" to select your SBI bank statement
   - Supported format: PDF files from SBI bank statements

3. **Process Statement:**
   - Click "Process Statement" to start the analysis
   - The system will:
     - Parse the PDF and extract transactions
     - Classify transactions using AI (if API key is configured)
     - Generate ledger entries
     - Calculate P&L summary

4. **Review Results:**
   - **Summary Tab:** Overview with key metrics and P&L chart
   - **Transactions Tab:** All parsed transactions with details
   - **Ledger Tab:** Double-entry ledger entries
   - **P&L Report Tab:** Detailed profit & loss breakdown
   - **Flagged Tab:** Transactions requiring manual review

5. **Export Data:**
   - Use the download buttons to export data in JSON format
   - Available exports: transactions, ledger, P&L report, flagged transactions

## 🏗️ Architecture

### Frontend (React + Vite)
- **Dashboard.jsx:** Main dashboard with navigation and overview
- **AutoLedger.jsx:** File upload and results display interface
- **FeatureCard.jsx:** Reusable component for feature cards
- **Modern CSS:** Professional styling with responsive design

### Backend (FastAPI)
- **main.py:** FastAPI application with CORS support
- **PDF Processing:** Uses pdfplumber for text extraction
- **AI Integration:** Perplexity Sonar Pro API for transaction classification
- **Data Processing:** Pandas for data manipulation and analysis

### Key Functions
- `parse_pdf_stage()`: Extract transactions from PDF
- `classify_flagged()`: AI-powered transaction classification
- `generate_ledger()`: Create double-entry ledger entries
- `compute_pnl()`: Calculate profit & loss summary

## 🔧 API Endpoints

- `GET /`: Health check
- `GET /api/health`: API status and configuration
- `POST /api/autoledger/process`: Process bank statement PDF

## 📊 Data Flow

1. **PDF Upload** → FastAPI backend
2. **Text Extraction** → Transaction parsing
3. **AI Classification** → Transaction categorization
4. **Ledger Generation** → Double-entry bookkeeping
5. **P&L Calculation** → Financial summary
6. **Results Display** → React frontend

## 🎨 UI Features

- **Responsive Design:** Works on desktop, tablet, and mobile
- **Modern Gradient Background:** Professional purple/blue theme
- **Interactive Cards:** Hover effects and smooth transitions
- **Tabbed Interface:** Organized data presentation
- **Download Functionality:** Export data in multiple formats
- **Loading States:** Visual feedback during processing

## 🔒 Security

- **CORS Configuration:** Secure cross-origin requests
- **File Validation:** PDF format verification
- **Error Handling:** Comprehensive error management
- **Temporary File Cleanup:** Automatic cleanup of uploaded files

## 🚀 Deployment

### Frontend Deployment
```bash
npm run build
# Deploy the 'dist' folder to your hosting service
```

### Backend Deployment
```bash
# Use uvicorn with production settings
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at http://localhost:8001/docs
2. Review the console logs for error messages
3. Ensure all dependencies are properly installed
4. Verify the backend server is running on port 8001

## 🔄 Updates

- **v1.0.0:** Initial release with AutoLedger functionality
- **Coming Soon:** Additional modules and enhanced features
# Updated Thu Aug  7 22:05:57 IST 2025
