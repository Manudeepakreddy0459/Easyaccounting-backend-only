from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import io
import pdfplumber
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import re
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Any
import tempfile
import shutil

app = FastAPI(title="CA Assistant AI - AutoLedger API", version="1.0.0")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "https://easyaccountings.web.app",  # Firebase hosting URL
        "https://caassistant.ai",  # Add your custom domain
        "https://www.caassistant.ai",  # Add www version
        "https://app.caassistant.ai",  # If using subdomain
        "*",  # Allow all origins for development/testing
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
SONAR_API_KEY = os.getenv("SONAR_API_KEY")

CATEGORIES = ["Income", "Expense", "Transfer", "Other", "Unknown"]

OWN_ACCOUNTS = [
    "YANAL", "9542900459", "4897732162091", "YESB", "PAYTM",
    "SELF ACCOUNT", "CURRENT ACCOUNT", "SBI"
]

ACCOUNT_MAP = {
    "PAYTM": "Wallet Expense",
    "SHACH": "Client Income",
    "YANAL": "Internal Transfer",
    "TGSPD": "Vendor",
    "UPI": "UPI Transfer Account"
}

BANK_ACCOUNT = "Current Account"
DEFAULT_INCOME_ACCOUNT = "Income"
DEFAULT_EXPENSE_ACCOUNT = "Expenses"

def process_raw_lines(lines):
    first_line = lines[0].strip()
    date_match = re.match(r'^(\d{1,2} [A-Za-z]{3} \d{4})', first_line)
    if not date_match:
        return None
    date = date_match.group(1)
    remainder = ' '.join(lines)[len(date):].strip()
    amount_match = re.search(r'TRANSFER[^\d]*([\d,]+\.\d{2})', remainder, re.IGNORECASE)
    if not amount_match:
        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', remainder)
    upi_id_match = re.search(r'UPI/[CD]R/\d{8,}', remainder)
    is_credit = any(kw in remainder.upper() for kw in ['CREDITED', 'UPI/CR', 'BY TRANSFER', 'FROM'])
    is_debit = any(kw in remainder.upper() for kw in ['DEBITED', 'UPI/DR', 'TO TRANSFER', 'TO'])
    if not amount_match:
        return None
    txn = {
        'date': date,
        'upi_reference': upi_id_match.group(0) if upi_id_match else "",
        'amount': amount_match.group(1),
        'direction': 'credit' if is_credit else 'debit' if is_debit else 'unknown',
        'narrative': remainder
    }
    return txn

def parse_pdf_stage(pdf_path):
    transactions = []
    ambiguous_flags = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split('\n')
            buffer = []
            for line in lines:
                line = line.strip()
                if re.match(r'^\d{1,2} [A-Za-z]{3} \d{4}', line):
                    if buffer:
                        txn = process_raw_lines(buffer)
                        if txn:
                            transactions.append(txn)
                        else:
                            ambiguous_flags.append(buffer)
                        buffer = []
                    buffer.append(line)
                else:
                    buffer.append(line)
            if buffer:
                txn = process_raw_lines(buffer)
                if txn:
                    transactions.append(txn)
                else:
                    ambiguous_flags.append(buffer)
    return transactions, ambiguous_flags

def call_sonar_api(prompt, api_key):
    if not api_key:
        return "API key not configured"
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "You are a financial statement classification expert."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            resp_json = response.json()
            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                return resp_json["choices"][0]["message"]["content"]
            else:
                return "No AI suggestion available."
        else:
            return f"API Error: {response.status_code}"
    except Exception as e:
        return f"API Error: {str(e)}"

def classify_flagged(flagged_entries, api_key):
    results = []
    for entry in flagged_entries:
        narration = ' '.join(entry) if isinstance(entry, list) else str(entry)
        prompt = (
            f"Classify this bank statement entry: '{narration}'. "
            f"Is it income, expense, transfer, or other? Please provide a brief explanation."
        )
        ai_suggestion = call_sonar_api(prompt, api_key)
        results.append({
            "narration": narration,
            "ai_suggestion": ai_suggestion,
            "category": None,
            "date": "",
            "amount": "",
            "counterparty": "",
            "action": None
        })
    return results

def extract_counterparty(narrative):
    match = re.search(r'UPI/[A-Z]+/\d+/([^/]+)/', narrative)
    if match:
        return match.group(1).strip().title()
    match_alt = re.search(r'FROM\s+([A-Z @0-9]+)', narrative.upper())
    if match_alt:
        return match_alt.group(1).title()
    match_to = re.search(r'TO\s+([A-Z @0-9]+)', narrative.upper())
    if match_to:
        return match_to.group(1).title()
    return "Unknown"

def refined_transaction_type(narration, direction, counterparty, own_accounts):
    narration_upper = narration.upper()
    counterparty_upper = counterparty.upper()
    if ("TO TRANSFER" in narration_upper or "BY TRANSFER" in narration_upper) and any(ac in counterparty_upper for ac in own_accounts):
        return "transfer"
    if direction == "debit" and "TO TRANSFER" in narration_upper and all(ac not in counterparty_upper for ac in own_accounts):
        return "expense"
    if direction == "credit" and "BY TRANSFER" in narration_upper and all(ac not in counterparty_upper for ac in own_accounts):
        return "income"
    if direction == "credit":
        return "income"
    if direction == "debit":
        return "expense"
    return "uncategorized"

def clean_and_classify_transactions(parsed_transactions):
    cleaned = []
    for txn in parsed_transactions:
        try:
            date_norm = datetime.strptime(txn['date'], "%d %b %Y").strftime("%Y-%m-%d")
        except Exception:
            date_norm = txn['date']
        try:
            amt = float(txn['amount'].replace(',', ''))
        except Exception:
            amt = 0.0
        counterparty = extract_counterparty(txn['narrative'])
        txn_type = refined_transaction_type(txn['narrative'], txn['direction'], counterparty, OWN_ACCOUNTS)
        cleaned.append({
            "date": date_norm,
            "amount": amt,
            "type": txn['direction'],
            "transaction_type": txn_type,
            "counterparty": counterparty,
            "account": BANK_ACCOUNT,
            "narrative": txn['narrative']
        })
    return cleaned

def map_counterparty_to_account(counterparty):
    if not counterparty:
        return "Unclassified"
    for key, account in ACCOUNT_MAP.items():
        if key.upper() in counterparty.upper():
            return account
    return "Unmapped Party"

def generate_ledger(cleaned_transactions):
    ledger_entries = []
    for txn in cleaned_transactions:
        date = txn['date']
        amount = txn['amount']
        narration = txn['narrative']
        txn_type = txn['transaction_type']
        direction = txn['type']
        counterparty = txn['counterparty']
        if amount <= 0:
            continue
        other_account = map_counterparty_to_account(counterparty)
        if txn_type == "income":
            debit_account = BANK_ACCOUNT
            credit_account = other_account if other_account != "Unmapped Party" else DEFAULT_INCOME_ACCOUNT
        elif txn_type == "expense":
            debit_account = other_account if other_account != "Unmapped Party" else DEFAULT_EXPENSE_ACCOUNT
            credit_account = BANK_ACCOUNT
        elif txn_type == "transfer":
            debit_account = BANK_ACCOUNT
            credit_account = other_account if other_account != "Unmapped Party" else "Transfer Account"
        else:
            debit_account = "Suspense"
            credit_account = "Suspense"
        ledger_entries.append({
            "date": date,
            "account": debit_account,
            "debit": amount,
            "credit": 0.0,
            "narration": narration,
            "transaction_type": txn_type,
            "counterparty": counterparty
        })
        ledger_entries.append({
            "date": date,
            "account": credit_account,
            "debit": 0.0,
            "credit": amount,
            "narration": narration,
            "transaction_type": txn_type,
            "counterparty": counterparty
        })
    return ledger_entries

def compute_pnl(ledger_entries):
    df = pd.DataFrame(ledger_entries)
    def is_income(acc): return any(k in acc.lower() for k in ["income", "client", "revenue", "received"])
    def is_expense(acc): return any(k in acc.lower() for k in ["expense", "vendor", "purchase", "wallet"])
    income_df = df[(df["credit"] > 0) & (df["transaction_type"] == "income") & df["account"].apply(is_income)]
    expense_df = df[(df["debit"] > 0) & (df["transaction_type"] == "expense") & df["account"].apply(is_expense)]
    total_income = income_df["credit"].sum()
    total_expense = expense_df["debit"].sum()
    net_profit = total_income - total_expense
    pnl_accounts = []
    for account, subdf in income_df.groupby("account"):
        pnl_accounts.append({"account": account, "amount": float(subdf["credit"].sum()), "type": "income"})
    for account, subdf in expense_df.groupby("account"):
        pnl_accounts.append({"account": account, "amount": -float(subdf["debit"].sum()), "type": "expense"})
    pnl_summary = {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "net_profit": float(net_profit),
        "breakdown": pnl_accounts
    }
    return pnl_summary

@app.get("/")
async def root():
    return {"message": "CA Assistant AI - AutoLedger API is running"}

@app.get("/api/test-cors")
async def test_cors():
    return {"message": "CORS is working correctly", "timestamp": datetime.now().isoformat()}

@app.post("/api/autoledger/process")
async def process_bank_statement(file: UploadFile = File(...)):
    """
    Process a bank statement PDF and generate ledger entries
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        # Parse PDF
        parsed_transactions, flagged = parse_pdf_stage(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if not parsed_transactions:
            raise HTTPException(status_code=400, detail="No transactions found in the PDF")
        
        # Process flagged entries with AI
        ai_results = []
        if flagged and SONAR_API_KEY:
            ai_results = classify_flagged(flagged, SONAR_API_KEY)
        
        # Clean and classify transactions
        cleaned_txns = clean_and_classify_transactions(parsed_transactions)
        
        # Generate ledger
        ledger_entries = generate_ledger(cleaned_txns)
        
        # Compute P&L
        pnl_summary = compute_pnl(ledger_entries)
        
        # Prepare response
        response_data = {
            "summary": {
                "total_transactions": len(parsed_transactions),
                "flagged_transactions": len(flagged),
                "cleaned_transactions": len(cleaned_txns),
                "ledger_entries": len(ledger_entries),
                "total_income": pnl_summary["total_income"],
                "total_expense": pnl_summary["total_expense"],
                "net_profit": pnl_summary["net_profit"]
            },
            "transactions": parsed_transactions,
            "flagged_transactions": ai_results,
            "cleaned_transactions": cleaned_txns,
            "ledger_entries": ledger_entries,
            "pnl_summary": pnl_summary
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "api_key_configured": bool(SONAR_API_KEY),
        "timestamp": datetime.now().isoformat(),
        "service": "CA Assistant AI - AutoLedger API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 