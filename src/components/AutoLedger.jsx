import React, { useState } from 'react';
import './AutoLedger.css';

const AutoLedger = ({ onBackToDashboard = () => {} }) => {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid PDF file');
      setFile(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Use Railway backend URL - update this with your actual Railway URL
      const API_BASE_URL = 'https://easyaccounting-backend-only-production.up.railway.app';
      const response = await fetch(`${API_BASE_URL}/api/autoledger/process`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      setActiveTab('summary');
    } catch (err) {
      setError(`Error processing file: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-IN');
    } catch {
      return dateStr;
    }
  };

  const downloadData = (data, filename, type = 'json') => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="autoledger-container">
      <div className="autoledger-header">
        <div className="header-top">
          <button 
            className="back-button"
            onClick={onBackToDashboard}
          >
            ← Back to Dashboard
          </button>
        </div>
        <h1>🏦 Auto Ledger</h1>
        <p>Upload your bank statement PDF to automatically generate ledger entries and P&L reports</p>
      </div>

      {!results && (
        <div className="upload-section">
          <div className="upload-card">
            <div className="upload-icon">📄</div>
            <h3>Upload Bank Statement</h3>
            <p>Supported format: PDF (SBI Bank Statements)</p>
            
            <form onSubmit={handleSubmit} className="upload-form">
              <div className="file-input-wrapper">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="file-input"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="file-input-label">
                  {file ? file.name : 'Choose PDF file'}
                </label>
              </div>
              
              {error && <div className="error-message">{error}</div>}
              
              <button 
                type="submit" 
                className="process-button"
                disabled={!file || isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Process Statement'}
              </button>
            </form>

            {isProcessing && (
              <div className="processing-indicator">
                <div className="spinner"></div>
                <p>Processing your bank statement...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {results && (
        <div className="results-section">
          <div className="results-header">
            <h2>Processing Results</h2>
            <button 
              className="new-upload-button"
              onClick={() => {
                setResults(null);
                setFile(null);
                setError(null);
              }}
            >
              Upload New File
            </button>
          </div>

          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="summary-card">
              <div className="summary-icon">📊</div>
              <div className="summary-content">
                <h3>Total Transactions</h3>
                <p className="summary-value">{results.summary.total_transactions}</p>
              </div>
            </div>
            
            <div className="summary-card">
              <div className="summary-icon">⚠️</div>
              <div className="summary-content">
                <h3>Flagged Transactions</h3>
                <p className="summary-value">{results.summary.flagged_transactions}</p>
              </div>
            </div>
            
            <div className="summary-card">
              <div className="summary-icon">💰</div>
              <div className="summary-content">
                <h3>Total Income</h3>
                <p className="summary-value income">{formatCurrency(results.summary.total_income)}</p>
              </div>
            </div>
            
            <div className="summary-card">
              <div className="summary-icon">💸</div>
              <div className="summary-content">
                <h3>Total Expenses</h3>
                <p className="summary-value expense">{formatCurrency(results.summary.total_expense)}</p>
              </div>
            </div>
            
            <div className="summary-card">
              <div className="summary-icon">📈</div>
              <div className="summary-content">
                <h3>Net Profit</h3>
                <p className={`summary-value ${results.summary.net_profit >= 0 ? 'income' : 'expense'}`}>
                  {formatCurrency(results.summary.net_profit)}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="results-tabs">
            <button 
              className={`tab-button ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={() => setActiveTab('summary')}
            >
              📊 Summary
            </button>
            <button 
              className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
              onClick={() => setActiveTab('transactions')}
            >
              📝 Transactions
            </button>
            <button 
              className={`tab-button ${activeTab === 'ledger' ? 'active' : ''}`}
              onClick={() => setActiveTab('ledger')}
            >
              📋 Ledger
            </button>
            <button 
              className={`tab-button ${activeTab === 'pnl' ? 'active' : ''}`}
              onClick={() => setActiveTab('pnl')}
            >
              📈 P&L Report
            </button>
            <button 
              className={`tab-button ${activeTab === 'flagged' ? 'active' : ''}`}
              onClick={() => setActiveTab('flagged')}
            >
              ⚠️ Flagged
            </button>
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'summary' && (
              <div className="summary-tab">
                <div className="pnl-chart">
                  <h3>Profit & Loss Overview</h3>
                  <div className="pnl-bars">
                    <div className="pnl-bar income">
                      <div className="bar-label">Income</div>
                      <div className="bar" style={{ width: `${Math.min(100, (results.summary.total_income / Math.max(results.summary.total_income, results.summary.total_expense)) * 100)}%` }}></div>
                      <div className="bar-value">{formatCurrency(results.summary.total_income)}</div>
                    </div>
                    <div className="pnl-bar expense">
                      <div className="bar-label">Expenses</div>
                      <div className="bar" style={{ width: `${Math.min(100, (results.summary.total_expense / Math.max(results.summary.total_income, results.summary.total_expense)) * 100)}%` }}></div>
                      <div className="bar-value">{formatCurrency(results.summary.total_expense)}</div>
                    </div>
                  </div>
                  <div className="net-profit">
                    <strong>Net Profit: {formatCurrency(results.summary.net_profit)}</strong>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'transactions' && (
              <div className="transactions-tab">
                <div className="table-header">
                  <h3>All Transactions</h3>
                  <button 
                    className="download-button"
                    onClick={() => downloadData(results.transactions, 'transactions.json')}
                  >
                    Download JSON
                  </button>
                </div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Type</th>
                        <th>Narrative</th>
                        <th>UPI Reference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.transactions.map((txn, index) => (
                        <tr key={index}>
                          <td>{txn.date}</td>
                          <td className={txn.direction === 'credit' ? 'income' : 'expense'}>
                            {formatCurrency(parseFloat(txn.amount.replace(',', '')))}
                          </td>
                          <td>
                            <span className={`type-badge ${txn.direction}`}>
                              {txn.direction.toUpperCase()}
                            </span>
                          </td>
                          <td className="narrative-cell">{txn.narrative}</td>
                          <td>{txn.upi_reference || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'ledger' && (
              <div className="ledger-tab">
                <div className="table-header">
                  <h3>Double-Entry Ledger</h3>
                  <button 
                    className="download-button"
                    onClick={() => downloadData(results.ledger_entries, 'ledger.json')}
                  >
                    Download JSON
                  </button>
                </div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Account</th>
                        <th>Debit</th>
                        <th>Credit</th>
                        <th>Transaction Type</th>
                        <th>Counterparty</th>
                        <th>Narration</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.ledger_entries.map((entry, index) => (
                        <tr key={index}>
                          <td>{formatDate(entry.date)}</td>
                          <td>{entry.account}</td>
                          <td className={entry.debit > 0 ? 'debit' : ''}>
                            {entry.debit > 0 ? formatCurrency(entry.debit) : '-'}
                          </td>
                          <td className={entry.credit > 0 ? 'credit' : ''}>
                            {entry.credit > 0 ? formatCurrency(entry.credit) : '-'}
                          </td>
                          <td>
                            <span className={`type-badge ${entry.transaction_type}`}>
                              {entry.transaction_type}
                            </span>
                          </td>
                          <td>{entry.counterparty}</td>
                          <td className="narrative-cell">{entry.narration}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'pnl' && (
              <div className="pnl-tab">
                <div className="table-header">
                  <h3>Profit & Loss Breakdown</h3>
                  <button 
                    className="download-button"
                    onClick={() => downloadData(results.pnl_summary, 'pnl_report.json')}
                  >
                    Download JSON
                  </button>
                </div>
                <div className="pnl-summary">
                  <div className="pnl-totals">
                    <div className="pnl-total income">
                      <h4>Total Income</h4>
                      <p>{formatCurrency(results.pnl_summary.total_income)}</p>
                    </div>
                    <div className="pnl-total expense">
                      <h4>Total Expenses</h4>
                      <p>{formatCurrency(results.pnl_summary.total_expense)}</p>
                    </div>
                    <div className={`pnl-total ${results.pnl_summary.net_profit >= 0 ? 'income' : 'expense'}`}>
                      <h4>Net Profit</h4>
                      <p>{formatCurrency(results.pnl_summary.net_profit)}</p>
                    </div>
                  </div>
                  
                  <div className="pnl-breakdown">
                    <h4>Account Breakdown</h4>
                    <div className="table-container">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Account</th>
                            <th>Type</th>
                            <th>Amount</th>
                          </tr>
                        </thead>
                        <tbody>
                          {results.pnl_summary.breakdown.map((item, index) => (
                            <tr key={index}>
                              <td>{item.account}</td>
                              <td>
                                <span className={`type-badge ${item.type}`}>
                                  {item.type}
                                </span>
                              </td>
                              <td className={item.amount >= 0 ? 'income' : 'expense'}>
                                {formatCurrency(Math.abs(item.amount))}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'flagged' && (
              <div className="flagged-tab">
                <div className="table-header">
                  <h3>Flagged Transactions</h3>
                  <button 
                    className="download-button"
                    onClick={() => downloadData(results.flagged_transactions, 'flagged_transactions.json')}
                  >
                    Download JSON
                  </button>
                </div>
                {results.flagged_transactions.length > 0 ? (
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Narration</th>
                          <th>AI Suggestion</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.flagged_transactions.map((item, index) => (
                          <tr key={index}>
                            <td className="narrative-cell">{item.narration}</td>
                            <td className="ai-suggestion">{item.ai_suggestion}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="no-flagged">
                    <p>No flagged transactions found. All transactions were processed successfully!</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AutoLedger; 