from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import io
import pdfplumber
from dotenv import load_dotenv
import asyncio
import aiohttp
import re
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Any
import tempfile
import shutil
import json
import time
from multi_bank_parser import multi_bank_parser

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="CA Assistant AI - AutoLedger API", version="1.0.0")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173",
        "https://easyaccountings.web.app",
        "https://caassistant.ai",
        "https://www.caassistant.ai",
        "https://app.caassistant.ai",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
SONAR_API_KEY = os.getenv("SONAR_API_KEY")
AI_TIMEOUT = 15  # 15 seconds timeout for AI calls
PDF_TIMEOUT = 30  # 30 seconds timeout for PDF processing

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
    """Optimized transaction line processing"""
    if not lines:
        return None
    
    first_line = lines[0].strip()
    date_match = re.match(r'^(\d{1,2} [A-Za-z]{3} \d{4})', first_line)
    if not date_match:
        return None
    
    date = date_match.group(1)
    remainder = ' '.join(lines)[len(date):].strip()
    
    # Optimized regex patterns
    amount_match = re.search(r'TRANSFER[^\d]*([\d,]+\.\d{2})', remainder, re.IGNORECASE)
    if not amount_match:
        amount_match = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})$', remainder)
    
    upi_id_match = re.search(r'UPI/[CD]R/\d{8,}', remainder)
    
    # Optimized direction detection
    remainder_upper = remainder.upper()
    is_credit = any(kw in remainder_upper for kw in ['CREDITED', 'UPI/CR', 'BY TRANSFER', 'FROM'])
    is_debit = any(kw in remainder_upper for kw in ['DEBITED', 'UPI/DR', 'TO TRANSFER', 'TO'])
    
    if not amount_match:
        return None
    
    return {
        'date': date,
        'upi_reference': upi_id_match.group(0) if upi_id_match else "",
        'amount': amount_match.group(1),
        'direction': 'credit' if is_credit else 'debit' if is_debit else 'unknown',
        'narrative': remainder
    }

def parse_pdf_stage_optimized(pdf_path):
    """Optimized PDF parsing with better error handling"""
    transactions = []
    ambiguous_flags = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Process pages more efficiently
            for page_num, page in enumerate(pdf.pages):
                try:
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
                    
                    # Process remaining buffer
                    if buffer:
                        txn = process_raw_lines(buffer)
                        if txn:
                            transactions.append(txn)
                        else:
                            ambiguous_flags.append(buffer)
                            
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")
                    continue
                    
    except Exception as e:
        print(f"Error opening PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    
    return transactions, ambiguous_flags

async def call_sonar_api_async(prompt, api_key, timeout=AI_TIMEOUT):
    """Asynchronous AI API call with timeout"""
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
        ],
        "max_tokens": 1000,  # Limit response size for faster processing
        "temperature": 0.1   # Lower temperature for more consistent results
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=timeout) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    if "choices" in resp_json and len(resp_json["choices"]) > 0:
                        return resp_json["choices"][0]["message"]["content"]
                    else:
                        return "No AI suggestion available."
                else:
                    return f"API Error: {response.status}"
    except asyncio.TimeoutError:
        return "AI API timeout - processing without AI classification"
    except Exception as e:
        return f"API Error: {str(e)}"

async def classify_flagged_async(flagged_entries, api_key):
    """Asynchronous flagged transaction classification"""
    if not flagged_entries or not api_key:
        return []
    
    # Limit the number of entries to process to avoid timeouts
    max_entries = 10
    if len(flagged_entries) > max_entries:
        flagged_entries = flagged_entries[:max_entries]
    
    narrations = [' '.join(entry) if isinstance(entry, list) else str(entry) for entry in flagged_entries]
    
    if not narrations:
        return []

    prompt = (
        f"Classify the following bank statement entries (max {max_entries}). For each entry, determine if it is income, expense, transfer, or other. Return as JSON array with 'narration' and 'ai_suggestion' keys.\n\n"
        + "\n".join([f"- '{n}'" for n in narrations])
    )
    
    ai_response_str = await call_sonar_api_async(prompt, api_key)
    
    try:
        ai_results = json.loads(ai_response_str)
        if isinstance(ai_results, list) and all(isinstance(item, dict) and 'narration' in item and 'ai_suggestion' in item for item in ai_results):
            return ai_results
    except json.JSONDecodeError:
        # Fallback processing
        ai_suggestions = ai_response_str.strip().split('\n')
        
        results = []
        for i, narration in enumerate(narrations):
            suggestion = ai_suggestions[i] if i < len(ai_suggestions) else "No specific suggestion found."
            results.append({
                "narration": narration,
                "ai_suggestion": suggestion,
                "category": None,
                "date": "",
                "amount": "",
                "counterparty": "",
                "action": None
            })
        return results

    # Final fallback
    return [{
        "narration": narration,
        "ai_suggestion": "Could not parse AI response.",
        "category": None,
        "date": "",
        "amount": "",
        "counterparty": "",
        "action": None
    } for narration in narrations]

def extract_counterparty(narrative):
    """Optimized counterparty extraction"""
    # Optimized regex patterns
    patterns = [
        r'UPI/[A-Z]+/\d+/([^/]+)/',
        r'FROM\s+([A-Z @0-9]+)',
        r'TO\s+([A-Z @0-9]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, narrative.upper())
        if match:
            return match.group(1).title()
    
    return "Unknown"

def refined_transaction_type(narration, direction, counterparty, own_accounts):
    """Optimized transaction type classification"""
    narration_upper = narration.upper()
    counterparty_upper = counterparty.upper()
    
    # Quick checks for common patterns
    if "TO TRANSFER" in narration_upper or "BY TRANSFER" in narration_upper:
        if any(ac in counterparty_upper for ac in own_accounts):
            return "transfer"
    
    if direction == "debit" and "TO TRANSFER" in narration_upper:
        return "expense" if all(ac not in counterparty_upper for ac in own_accounts) else "transfer"
    
    if direction == "credit" and "BY TRANSFER" in narration_upper:
        return "income" if all(ac not in counterparty_upper for ac in own_accounts) else "transfer"
    
    return "income" if direction == "credit" else "expense" if direction == "debit" else "uncategorized"

def clean_and_classify_transactions(parsed_transactions):
    """Optimized transaction cleaning and classification"""
    cleaned = []
    
    for txn in parsed_transactions:
        try:
            # Optimized date parsing
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
    """Optimized account mapping"""
    if not counterparty:
        return "Unclassified"
    
    counterparty_upper = counterparty.upper()
    for key, account in ACCOUNT_MAP.items():
        if key.upper() in counterparty_upper:
            return account
    
    return "Unmapped Party"

def generate_ledger(cleaned_transactions):
    """Optimized ledger generation"""
    ledger_entries = []
    
    for txn in cleaned_transactions:
        if txn['amount'] <= 0:
            continue
            
        date = txn['date']
        amount = txn['amount']
        narration = txn['narrative']
        txn_type = txn['transaction_type']
        counterparty = txn['counterparty']
        
        other_account = map_counterparty_to_account(counterparty)
        
        # Determine accounts based on transaction type
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
        
        # Add debit entry
        ledger_entries.append({
            "date": date,
            "account": debit_account,
            "debit": amount,
            "credit": 0.0,
            "narration": narration,
            "transaction_type": txn_type,
            "counterparty": counterparty
        })
        
        # Add credit entry
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
    """Optimized P&L computation"""
    if not ledger_entries:
        return {
            "total_income": 0.0,
            "total_expense": 0.0,
            "net_profit": 0.0,
            "breakdown": []
        }
    
    df = pd.DataFrame(ledger_entries)
    
    # Optimized filtering functions
    def is_income(acc): 
        acc_lower = acc.lower()
        return any(k in acc_lower for k in ["income", "client", "revenue", "received"])
    
    def is_expense(acc): 
        acc_lower = acc.lower()
        return any(k in acc_lower for k in ["expense", "vendor", "purchase", "wallet"])
    
    # Filter data efficiently
    income_mask = (df["credit"] > 0) & (df["transaction_type"] == "income") & df["account"].apply(is_income)
    expense_mask = (df["debit"] > 0) & (df["transaction_type"] == "expense") & df["account"].apply(is_expense)
    
    income_df = df[income_mask]
    expense_df = df[expense_mask]
    
    total_income = income_df["credit"].sum()
    total_expense = expense_df["debit"].sum()
    net_profit = total_income - total_expense
    
    # Build breakdown efficiently
    pnl_accounts = []
    
    for account, subdf in income_df.groupby("account"):
        pnl_accounts.append({
            "account": account, 
            "amount": float(subdf["credit"].sum()), 
            "type": "income"
        })
    
    for account, subdf in expense_df.groupby("account"):
        pnl_accounts.append({
            "account": account, 
            "amount": -float(subdf["debit"].sum()), 
            "type": "expense"
        })
    
    return {
        "total_income": float(total_income),
        "total_expense": float(total_expense),
        "net_profit": float(net_profit),
        "breakdown": pnl_accounts
    }

@app.get("/")
async def root():
    return {"message": "CA Assistant AI - AutoLedger API is running (Optimized Version)"}

@app.get("/api/test-cors")
async def test_cors():
    return {"message": "CORS is working correctly", "timestamp": datetime.now().isoformat()}

@app.post("/api/autoledger/process")
async def process_bank_statement(file: UploadFile = File(...)):
    """
    Optimized bank statement processing with async AI calls and timeouts
    """
    start_time = time.time()
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_path = tmp_file.name
        
        # Parse PDF with multi-bank parser and timeout
        try:
            parsed_transactions, flagged, detected_bank = await asyncio.wait_for(
                asyncio.to_thread(multi_bank_parser.parse_pdf, temp_path),
                timeout=PDF_TIMEOUT
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="PDF processing timeout - file may be too large or complex")
        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if not parsed_transactions:
            raise HTTPException(status_code=400, detail="No transactions found in the PDF")
        
        # Process flagged entries with AI (async with timeout)
        ai_results = []
        if flagged and SONAR_API_KEY:
            try:
                ai_results = await asyncio.wait_for(
                    classify_flagged_async(flagged, SONAR_API_KEY),
                    timeout=AI_TIMEOUT
                )
            except asyncio.TimeoutError:
                ai_results = [{"narration": "AI processing timeout", "ai_suggestion": "Processing completed without AI classification"}]
        
        # Clean and classify transactions
        cleaned_txns = clean_and_classify_transactions(parsed_transactions)
        
        # Generate ledger
        ledger_entries = generate_ledger(cleaned_txns)
        
        # Compute P&L
        pnl_summary = compute_pnl(ledger_entries)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            "summary": {
                "total_transactions": len(parsed_transactions),
                "flagged_transactions": len(flagged),
                "cleaned_transactions": len(cleaned_txns),
                "ledger_entries": len(ledger_entries),
                "total_income": pnl_summary["total_income"],
                "total_expense": pnl_summary["total_expense"],
                "net_profit": pnl_summary["net_profit"],
                "processing_time_seconds": round(processing_time, 2),
                "detected_bank": multi_bank_parser.bank_patterns[detected_bank]['name'],
                "bank_code": detected_bank
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
        "service": "CA Assistant AI - AutoLedger API (Optimized)",
        "timeouts": {
            "ai_timeout_seconds": AI_TIMEOUT,
            "pdf_timeout_seconds": PDF_TIMEOUT
        }
    }

@app.get("/api/supported-banks")
async def get_supported_banks():
    """Get list of supported banks"""
    return {
        "supported_banks": multi_bank_parser.get_supported_banks(),
        "total_banks": len(multi_bank_parser.get_supported_banks())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
