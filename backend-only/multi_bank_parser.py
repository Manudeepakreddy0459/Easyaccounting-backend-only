import re
import pdfplumber
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiBankParser:
    """Universal bank statement parser supporting multiple Indian banks"""
    
    def __init__(self):
        # Bank-specific patterns and configurations
        self.bank_patterns = {
            'sbi': {
                'name': 'State Bank of India',
                'date_pattern': r'^\d{1,2} [A-Za-z]{3} \d{4}',
                'amount_patterns': [
                    r'TRANSFER[^\d]*([\d,]+\.\d{2})',
                    r'(\d{1,3}(?:,\d{3})*\.\d{2})$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['CREDITED', 'UPI/CR', 'BY TRANSFER', 'FROM', 'CREDIT'],
                'debit_keywords': ['DEBITED', 'UPI/DR', 'TO TRANSFER', 'TO', 'DEBIT'],
                'upi_pattern': r'UPI/[CD]R/\d{8,}',
                'account_patterns': ['SBI', 'STATE BANK', 'SBIN']
            },
            'hdfc': {
                'name': 'HDFC Bank',
                'date_pattern': r'^\d{1,2}/\d{1,2}/\d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*DR$',
                    r'([\d,]+\.\d{2})\s*CR$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['CR', 'CREDIT', 'CREDITED', 'RECEIVED', 'FROM'],
                'debit_keywords': ['DR', 'DEBIT', 'DEBITED', 'PAID', 'TO'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': ['HDFC', 'HDFC BANK']
            },
            'icici': {
                'name': 'ICICI Bank',
                'date_pattern': r'^\d{1,2}-\d{1,2}-\d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*Dr$',
                    r'([\d,]+\.\d{2})\s*Cr$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['Cr', 'CREDIT', 'CREDITED', 'RECEIVED'],
                'debit_keywords': ['Dr', 'DEBIT', 'DEBITED', 'PAID'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': ['ICICI', 'ICICI BANK']
            },
            'axis': {
                'name': 'Axis Bank',
                'date_pattern': r'^\d{1,2}/\d{1,2}/\d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*DR$',
                    r'([\d,]+\.\d{2})\s*CR$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['CR', 'CREDIT', 'CREDITED', 'RECEIVED'],
                'debit_keywords': ['DR', 'DEBIT', 'DEBITED', 'PAID'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': ['AXIS', 'AXIS BANK']
            },
            'kotak': {
                'name': 'Kotak Mahindra Bank',
                'date_pattern': r'^\d{1,2}-\d{1,2}-\d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*DR$',
                    r'([\d,]+\.\d{2})\s*CR$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['CR', 'CREDIT', 'CREDITED', 'RECEIVED'],
                'debit_keywords': ['DR', 'DEBIT', 'DEBITED', 'PAID'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': ['KOTAK', 'KOTAK MAHINDRA']
            },
            'yes_bank': {
                'name': 'YES Bank',
                'date_pattern': r'^\d{1,2}/\d{1,2}/\d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*DR$',
                    r'([\d,]+\.\d{2})\s*CR$',
                    r'([\d,]+\.\d{2})\s*$'
                ],
                'credit_keywords': ['CR', 'CREDIT', 'CREDITED', 'RECEIVED'],
                'debit_keywords': ['DR', 'DEBIT', 'DEBITED', 'PAID'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': ['YES', 'YES BANK']
            },
            'generic': {
                'name': 'Generic Bank',
                'date_pattern': r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{1,2} [A-Za-z]{3} \d{4}',
                'amount_patterns': [
                    r'([\d,]+\.\d{2})\s*DR$',
                    r'([\d,]+\.\d{2})\s*CR$',
                    r'([\d,]+\.\d{2})\s*$',
                    r'(\d{1,3}(?:,\d{3})*\.\d{2})$'
                ],
                'credit_keywords': ['CR', 'CREDIT', 'CREDITED', 'RECEIVED', 'FROM', 'CR'],
                'debit_keywords': ['DR', 'DEBIT', 'DEBITED', 'PAID', 'TO', 'DR'],
                'upi_pattern': r'UPI/[A-Z]+/\d+',
                'account_patterns': []
            }
        }
    
    def detect_bank(self, text: str) -> str:
        """Detect bank type from PDF text"""
        text_upper = text.upper()
        
        for bank_code, config in self.bank_patterns.items():
            if bank_code == 'generic':
                continue
                
            for pattern in config['account_patterns']:
                if pattern.upper() in text_upper:
                    logger.info(f"Detected bank: {config['name']}")
                    return bank_code
        
        # If no specific bank detected, try to identify by date format
        if re.search(r'^\d{1,2} [A-Za-z]{3} \d{4}', text, re.MULTILINE):
            logger.info("Detected SBI-like format")
            return 'sbi'
        elif re.search(r'^\d{1,2}/\d{1,2}/\d{4}', text, re.MULTILINE):
            logger.info("Detected HDFC/Axis-like format")
            return 'hdfc'
        elif re.search(r'^\d{1,2}-\d{1,2}-\d{4}', text, re.MULTILINE):
            logger.info("Detected ICICI/Kotak-like format")
            return 'icici'
        
        logger.info("Using generic parser")
        return 'generic'
    
    def parse_date(self, date_str: str, bank_code: str) -> str:
        """Parse date string based on bank format"""
        try:
            if bank_code == 'sbi':
                # Format: "15 Jan 2024"
                return datetime.strptime(date_str, "%d %b %Y").strftime("%Y-%m-%d")
            elif bank_code in ['hdfc', 'axis', 'yes_bank']:
                # Format: "15/01/2024"
                return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            elif bank_code in ['icici', 'kotak']:
                # Format: "15-01-2024"
                return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
            else:
                # Try multiple formats
                for fmt in ["%d %b %Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                    except:
                        continue
                return date_str
        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_str}': {e}")
            return date_str
    
    def extract_amount(self, text: str, bank_code: str) -> Optional[str]:
        """Extract amount from text based on bank format"""
        config = self.bank_patterns[bank_code]
        
        for pattern in config['amount_patterns']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def determine_direction(self, text: str, bank_code: str) -> str:
        """Determine transaction direction based on bank format"""
        config = self.bank_patterns[bank_code]
        text_upper = text.upper()
        
        # Check for credit keywords
        for keyword in config['credit_keywords']:
            if keyword.upper() in text_upper:
                return 'credit'
        
        # Check for debit keywords
        for keyword in config['debit_keywords']:
            if keyword.upper() in text_upper:
                return 'debit'
        
        # Fallback: check for DR/CR indicators
        if re.search(r'\bDR\b', text_upper):
            return 'debit'
        elif re.search(r'\bCR\b', text_upper):
            return 'credit'
        
        return 'unknown'
    
    def extract_upi_reference(self, text: str, bank_code: str) -> str:
        """Extract UPI reference from text"""
        config = self.bank_patterns[bank_code]
        match = re.search(config['upi_pattern'], text)
        return match.group(0) if match else ""
    
    def process_transaction_lines(self, lines: List[str], bank_code: str) -> Optional[Dict[str, Any]]:
        """Process transaction lines based on bank format"""
        if not lines:
            return None
        
        config = self.bank_patterns[bank_code]
        first_line = lines[0].strip()
        
        # Find date
        date_match = re.search(config['date_pattern'], first_line)
        if not date_match:
            return None
        
        date_str = date_match.group(0)
        date = self.parse_date(date_str, bank_code)
        
        # Combine all lines for processing
        full_text = ' '.join(lines)
        
        # Extract amount
        amount = self.extract_amount(full_text, bank_code)
        if not amount:
            return None
        
        # Determine direction
        direction = self.determine_direction(full_text, bank_code)
        
        # Extract UPI reference
        upi_reference = self.extract_upi_reference(full_text, bank_code)
        
        # Create narrative (remove date and amount)
        narrative = full_text.replace(date_str, '').strip()
        
        return {
            'date': date,
            'upi_reference': upi_reference,
            'amount': amount,
            'direction': direction,
            'narrative': narrative,
            'bank_type': bank_code
        }
    
    def parse_pdf(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], List[List[str]], str]:
        """Parse PDF and return transactions, flagged entries, and detected bank"""
        transactions = []
        ambiguous_flags = []
        detected_bank = 'generic'
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # First, detect bank type from first few pages
                sample_text = ""
                for i, page in enumerate(pdf.pages[:3]):  # Check first 3 pages
                    text = page.extract_text()
                    if text:
                        sample_text += text + "\n"
                        if len(sample_text) > 5000:  # Enough text to detect
                            break
                
                detected_bank = self.detect_bank(sample_text)
                logger.info(f"Processing PDF with {self.bank_patterns[detected_bank]['name']} parser")
                
                # Reset PDF for full processing
                pdf = pdfplumber.open(pdf_path)
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if not text:
                            continue
                        
                        lines = text.split('\n')
                        buffer = []
                        
                        for line in lines:
                            line = line.strip()
                            # Check if line starts with a date pattern
                            if re.search(self.bank_patterns[detected_bank]['date_pattern'], line):
                                if buffer:
                                    txn = self.process_transaction_lines(buffer, detected_bank)
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
                            txn = self.process_transaction_lines(buffer, detected_bank)
                            if txn:
                                transactions.append(txn)
                            else:
                                ambiguous_flags.append(buffer)
                                
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            raise Exception(f"Error reading PDF: {str(e)}")
        
        logger.info(f"Parsed {len(transactions)} transactions, {len(ambiguous_flags)} flagged entries")
        return transactions, ambiguous_flags, detected_bank
    
    def get_supported_banks(self) -> List[Dict[str, str]]:
        """Get list of supported banks"""
        return [
            {'code': code, 'name': config['name']} 
            for code, config in self.bank_patterns.items() 
            if code != 'generic'
        ]

# Global parser instance
multi_bank_parser = MultiBankParser()
