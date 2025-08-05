import streamlit as st
import os
import io
import pdfplumber
import re
import pandas as pd
import requests
from datetime import datetime

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

def df_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

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
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        resp_json = response.json()
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            return resp_json["choices"][0]["message"]["content"]
        else:
            return "No AI suggestion available."
    else:
        return f"API Error: {response.status_code}"

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

def manual_review_ui(flagged_ai_data):
    st.header("Manual Review & Correction of Flagged Transactions")
    review_results = []

    for idx, txn in enumerate(flagged_ai_data):
        st.markdown(f"### Transaction {idx + 1}")

        st.text_area(f"Original Narration", txn["narration"], height=75, key=f"narr_{idx}", disabled=True)
        st.markdown("**AI Suggested Classification:**")
        st.info(txn["ai_suggestion"])

        default_category = "Unknown"
        for cat in CATEGORIES:
            if cat.lower() in txn["ai_suggestion"].lower():
                default_category = cat
                break

        with st.form(key=f"form_{idx}"):
            category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(default_category), key=f"cat_{idx}")
            date_input = st.text_input("Date (YYYY-MM-DD)", value=txn.get("date", ""), key=f"date_{idx}")
            amount_input = st.text_input("Amount", value=txn.get("amount", ""), key=f"amt_{idx}")
            counterparty_input = st.text_input("Counterparty", value=txn.get("counterparty", ""), key=f"cp_{idx}")

            accepted = st.form_submit_button("Accept")
            edited = st.form_submit_button("Save Edit")
            rejected = st.form_submit_button("Reject")

            action = None
            if accepted:
                action = "accept"
            elif edited:
                action = "edit"
            elif rejected:
                action = "reject"

            if action is not None:
                review_results.append({
                    "narration": txn["narration"],
                    "ai_suggestion": txn["ai_suggestion"],
                    "final_category": category,
                    "date": date_input,
                    "amount": amount_input,
                    "counterparty": counterparty_input,
                    "action": action
                })
                st.success(f"Transaction {idx + 1} {action.upper()}ED")

    return review_results

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

def save_uploaded_file(uploaded_file, save_dir="uploads"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def main():
    st.title("SBI Bank Statement Automation MVP: Upload → Parse → AI → Review → Ledger & P&L")

    uploaded_file = st.file_uploader("Upload SBI Bank Statement PDF", type=["pdf"])

    if uploaded_file:
        file_path = save_uploaded_file(uploaded_file)
        st.success(f"File uploaded to {file_path}")

        with st.spinner("Parsing PDF and detecting flagged transactions..."):
            parsed_transactions, flagged = parse_pdf_stage(file_path)

        st.write(f"Total Transactions Parsed: {len(parsed_transactions)}")
        st.write(f"Total Ambiguous Entries Flagged: {len(flagged)}")

        df_all = pd.DataFrame(parsed_transactions)
        st.subheader("All Parsed Transactions")
        st.dataframe(df_all)
        st.download_button("Download All Transactions (Excel)", data=df_to_excel_bytes(df_all),
                           file_name="all_transactions.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Download All Transactions (JSON)", data=df_all.to_json(orient="records", indent=2),
                           file_name="all_transactions.json",
                           mime="application/json")

        ai_results = []
        if flagged:
            if not SONAR_API_KEY:
                st.warning("Sonar Pro API key not set. Skipping AI classification.")
            else:
                with st.spinner("Sending flagged entries to AI for classification..."):
                    ai_results = classify_flagged(flagged, SONAR_API_KEY)

        if ai_results:
            df_flags = pd.DataFrame(ai_results)
            st.subheader("Flagged Transactions with AI Suggestions")
            st.dataframe(df_flags)
            st.download_button("Download Flagged Entries (Excel)", data=df_to_excel_bytes(df_flags),
                               file_name="flagged_entries.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            review_results = manual_review_ui(ai_results)
            if review_results:
                review_df = pd.DataFrame(review_results)
                st.subheader("Review Summary (After Manual Correction)")
                st.dataframe(review_df)
                st.download_button("Download Review Results (Excel)", data=df_to_excel_bytes(review_df),
                                   file_name="review_results.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        else:
            st.info("No flagged entries requiring AI classification or manual review.")

        cleaned_txns = clean_and_classify_transactions(parsed_transactions)
        ledger_entries = generate_ledger(cleaned_txns)
        pnl_summary = compute_pnl(ledger_entries)

        df_ledger = pd.DataFrame(ledger_entries)
        st.subheader("Double-Entry Ledger")
        st.dataframe(df_ledger)
        st.download_button("Download Ledger (Excel)", data=df_to_excel_bytes(df_ledger),
                           file_name="ledger.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Download Ledger (JSON)", data=df_ledger.to_json(orient="records", indent=2),
                           file_name="ledger.json",
                           mime="application/json")

        st.subheader("Profit & Loss Summary")
        st.json(pnl_summary)
        pnl_breakdown_df = pd.DataFrame(pnl_summary["breakdown"])
        st.dataframe(pnl_breakdown_df)
        st.download_button("Download Profit & Loss (Excel)", data=df_to_excel_bytes(pnl_breakdown_df),
                           file_name="pnl_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Download Profit & Loss (JSON)", data=pnl_breakdown_df.to_json(orient="records", indent=2),
                           file_name="pnl_report.json",
                           mime="application/json")

    else:
        st.info("Please upload an SBI bank statement PDF to start.")

if __name__ == "__main__":
    main()
