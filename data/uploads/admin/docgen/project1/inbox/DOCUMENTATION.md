# Enhanced EDGAR MCP Tools - Complete Documentation

**Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.**  
**Email:** ajsinha@gmail.com  
**Version:** 1.0.0  
**Last Updated:** November 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Tool List](#complete-tool-list)
3. [Installation](#installation)
4. [API Key Requirements](#api-key-requirements)
5. [Rate Limits](#rate-limits)
6. [Tool Descriptions](#tool-descriptions)
7. [Usage Examples](#usage-examples)
8. [Sample Code](#sample-code)
9. [Limitations](#limitations)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Legal Notice](#legal-notice)

---

## Overview

Enhanced EDGAR MCP Tools is a comprehensive Python toolkit providing programmatic access to the U.S. Securities and Exchange Commission (SEC) EDGAR database through **20 specialized tools**. Access company filings, financial data, insider transactions, institutional holdings, and more.

### Key Features

- ✅ **No API Key Required** - Free access to SEC public data
- ✅ **20 Specialized Tools** - Granular access to different data types
- ✅ **XBRL Support** - Structured financial data extraction
- ✅ **Rate Limit Handling** - Built-in compliance with SEC limits
- ✅ **Python Standard Library** - No external dependencies
- ✅ **Comprehensive Coverage** - All major SEC filing types

---

## Complete Tool List

### Company Discovery & Search (3 tools)
1. **edgar_company_search** - Search by name or ticker
2. **edgar_company_tickers_by_exchange** - Filter by stock exchange
3. **edgar_companies_by_sic** - Search by industry (SIC code)

### Company Information (2 tools)
4. **edgar_company_submissions** - All filings and company metadata
5. **edgar_filing_details** - Specific filing by accession number

### Financial Data (4 tools)
6. **edgar_company_facts** - ALL XBRL financial facts
7. **edgar_company_concept** - Time-series for specific metric
8. **edgar_financial_ratios** - Auto-calculated ratios
9. **edgar_frame_data** - Market-wide aggregated data

### Filing Types (6 tools)
10. **edgar_filings_by_form** - Filter by form type (10-K, 10-Q, etc.)
11. **edgar_current_reports** - 8-K material events
12. **edgar_proxy_statements** - DEF 14A shareholder info
13. **edgar_registration_statements** - S-1, S-3, S-4, S-8 (IPOs)
14. **edgar_foreign_issuers** - 20-F, 6-K, 40-F
15. **edgar_amendments** - Track corrections (/A forms)

### Ownership & Holdings (4 tools)
16. **edgar_insider_transactions** - Form 4 insider trades
17. **edgar_ownership_reports** - SC 13D/G beneficial ownership
18. **edgar_institutional_holdings** - 13F institutional portfolios
19. **edgar_mutual_fund_holdings** - N-PORT fund positions

### Advanced Analysis (1 tool)
20. **edgar_xbrl_frames_multi_concept** - Batch concept retrieval

---

## Installation

### System Requirements
- Python 3.7+
- Internet connection
- 2 GB RAM (recommended)

### Step 1: Download Files

```
enhanced_edgar_tools/
├── enhanced_edgar_tool.py (2542 lines)
├── base_mcp_tool.py
└── configs/
    ├── edgar_company_search.json
    ├── edgar_company_submissions.json
    ├── edgar_company_facts.json
    ├── edgar_company_concept.json
    ├── edgar_filings_by_form.json
    ├── edgar_insider_transactions.json
    ├── edgar_institutional_holdings.json
    ├── edgar_mutual_fund_holdings.json
    ├── edgar_frame_data.json
    ├── edgar_company_tickers_by_exchange.json
    ├── edgar_companies_by_sic.json
    ├── edgar_filing_details.json
    ├── edgar_ownership_reports.json
    ├── edgar_proxy_statements.json
    ├── edgar_registration_statements.json
    ├── edgar_foreign_issuers.json
    ├── edgar_current_reports.json
    ├── edgar_financial_ratios.json
    ├── edgar_amendments.json
    └── edgar_xbrl_frames_multi_concept.json
```

### Step 2: Test Installation

```python
import sys
sys.path.append('/path/to/enhanced_edgar_tools')

from enhanced_edgar_tool import EDGAR_TOOLS

print(f"✓ Successfully loaded {len(EDGAR_TOOLS)} tools")
for name in EDGAR_TOOLS.keys():
    print(f"  - {name}")
```

---

## API Key Requirements

### ✅ NO API KEY NEEDED!

The SEC EDGAR API is **completely free** and does not require registration or API keys.

### ⚠️ REQUIRED: User-Agent Header

The SEC **requires** a User-Agent header with:
1. Your company/application name
2. Your email address

**Already configured in this toolkit:**
```python
headers = {
    'User-Agent': 'Enhanced EDGAR Tool ashutosh.sinha@research.com'
}
```

### Customizing User-Agent

```python
from enhanced_edgar_tool import EDGARBaseTool

# Create custom tool with your information
class MyEDGARTool(EDGARBaseTool):
    def __init__(self, config=None):
        super().__init__(config)
        self.headers['User-Agent'] = 'MyCompany contact@mycompany.com'
```

### Why This Matters

- ❌ Missing User-Agent = **HTTP 403 Forbidden**
- ✅ Proper User-Agent = Full API access
- SEC uses this to track usage and contact users if needed

---

## Rate Limits

### SEC EDGAR Rate Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Requests/second | 10 | Strict |
| Requests/day | Unlimited | None |
| Burst limit | 10 | Per second |

### Built-in Protection

```python
# Automatically enforced in all tools
self.rate_limit_delay = 0.11  # 110ms between requests
```

### Best Practices

1. ✅ Use caching for repeated queries
2. ✅ Batch operations with delays
3. ✅ Schedule large jobs during off-peak hours
4. ✅ Implement retry logic with exponential backoff
5. ❌ Don't make parallel requests

---

## Tool Descriptions

### 1. edgar_company_search
**Find companies by name or ticker symbol**

```python
from enhanced_edgar_tool import EDGARCompanySearchTool

tool = EDGARCompanySearchTool()
result = tool.execute({
    'query': 'Apple',
    'search_type': 'name',
    'limit': 5
})

for company in result['companies']:
    print(f"{company['ticker']}: {company['title']} (CIK: {company['cik']})")
```

**Output:**
```
AAPL: Apple Inc (CIK: 0000320193)
```

---

### 2. edgar_company_tickers_by_exchange
**Get all companies on a specific exchange**

```python
from enhanced_edgar_tool import EDGARCompanyTickersByExchangeTool

tool = EDGARCompanyTickersByExchangeTool()
result = tool.execute({
    'exchange': 'NYSE',
    'limit': 10
})

print(f"Found {result['companies_count']} NYSE companies")
```

**Use Case:** Build exchange-specific indices or screens

---

### 3. edgar_companies_by_sic
**Search companies by industry (SIC code)**

```python
from enhanced_edgar_tool import EDGARCompaniesBySICTool

tool = EDGARCompaniesBySICTool()
result = tool.execute({
    'sic_code': '7372',  # Software
    'limit': 20
})

print(f"Software companies: {result['companies_count']}")
```

**Common SIC Codes:**
- `7372` - Prepackaged Software
- `3674` - Semiconductors
- `6022` - Commercial Banks
- `2834` - Pharmaceuticals

---

### 4. edgar_company_submissions
**Get all company filings and metadata**

```python
from enhanced_edgar_tool import EDGARCompanySubmissionsTool

tool = EDGARCompanySubmissionsTool()
result = tool.execute({'cik': '320193'})  # Apple

print(f"Company: {result['name']}")
print(f"Industry: {result['sicDescription']}")
print(f"Recent filings: {result['filings_count']}")

for filing in result['recent_filings'][:5]:
    print(f"  {filing['form']} - {filing['filingDate']}")
```

---

### 5. edgar_filing_details
**Get specific filing details by accession number**

```python
from enhanced_edgar_tool import EDGARFilingDetailsTool

tool = EDGARFilingDetailsTool()
result = tool.execute({
    'cik': '320193',
    'accession_number': '0000320193-23-000106'
})

print(f"Form: {result['form']}")
print(f"Filed: {result['filingDate']}")
print(f"URL: {result['document_url']}")
```

---

### 6. edgar_company_facts
**Get ALL financial facts (XBRL) - WARNING: Large response**

```python
from enhanced_edgar_tool import EDGARCompanyFactsTool

tool = EDGARCompanyFactsTool()
result = tool.execute({'cik': '320193'})

print(f"Company: {result['entityName']}")
print(f"Total facts: {result['facts_count']}")
print(f"Taxonomies: {result['taxonomies']}")

# Access specific fact
revenue_data = result['facts']['us-gaap']['Revenues']
print(f"Revenue concept available: {revenue_data['label']}")
```

**⚠️ Response Size:** Can be 5-50 MB for large companies

---

### 7. edgar_company_concept
**Get time-series for a specific metric**

```python
from enhanced_edgar_tool import EDGARCompanyConceptTool

tool = EDGARCompanyConceptTool()
result = tool.execute({
    'cik': '320193',
    'taxonomy': 'us-gaap',
    'concept': 'Revenues'
})

# Print revenue history
for unit_type, values in result['units'].items():
    print(f"\n{unit_type} values:")
    for obs in values[-5:]:  # Last 5 observations
        print(f"  {obs['end']}: ${obs['val']:,.0f} (FY{obs['fy']}{obs['fp']})")
```

**Common Concepts:**
- `Revenues` / `Revenue`
- `Assets` / `Liabilities`
- `NetIncomeLoss`
- `EarningsPerShareBasic`
- `CashAndCashEquivalents`
- `StockholdersEquity`

---

### 8. edgar_financial_ratios
**Auto-calculate financial ratios**

```python
from enhanced_edgar_tool import EDGARFinancialRatiosTool

tool = EDGARFinancialRatiosTool()
result = tool.execute({
    'cik': '320193',
    'fiscal_year': 2023,
    'fiscal_period': 'FY'
})

print(f"Company: {result['entityName']}")
print(f"\nProfitability:")
print(f"  Gross Margin: {result['profitability_ratios'].get('gross_margin')}%")
print(f"  Net Margin: {result['profitability_ratios'].get('net_margin')}%")
print(f"  ROE: {result['profitability_ratios'].get('return_on_equity')}%")

print(f"\nLiquidity:")
print(f"  Current Ratio: {result['liquidity_ratios'].get('current_ratio')}")

print(f"\nSolvency:")
print(f"  Debt/Equity: {result['solvency_ratios'].get('debt_to_equity')}")
```

**Ratios Calculated:**
- **Profitability:** Gross/Operating/Net Margin, ROA, ROE
- **Liquidity:** Current, Quick, Cash Ratios
- **Solvency:** Debt/Equity, Debt/Assets, Equity Multiplier

---

### 9. edgar_frame_data
**Get market-wide data for benchmarking**

```python
from enhanced_edgar_tool import EDGARFrameDataTool

tool = EDGARFrameDataTool()
result = tool.execute({
    'taxonomy': 'us-gaap',
    'concept': 'Revenues',
    'unit': 'USD',
    'year': 2023,
    'quarter': 'CY'
})

print(f"Frame: {result['frame']}")
print(f"Companies: {result['units_count']}")

# Find top revenue companies
sorted_data = sorted(result['data'], key=lambda x: x['val'], reverse=True)
print("\nTop 10 by Revenue:")
for i, company in enumerate(sorted_data[:10], 1):
    print(f"{i}. {company['entityName']}: ${company['val']:,.0f}")
```

---

### 10. edgar_filings_by_form
**Filter filings by form type**

```python
from enhanced_edgar_tool import EDGARFilingsByFormTool

tool = EDGARFilingsByFormTool()

# Get 10-K annual reports
result = tool.execute({
    'cik': '320193',
    'form_type': '10-K',
    'limit': 5
})

print(f"10-K Filings: {result['filings_count']}")
for filing in result['filings']:
    print(f"  {filing['filingDate']}: {filing['reportDate']}")
    print(f"    URL: {filing['document_url']}")
```

**Major Form Types:**
- `10-K` - Annual Report
- `10-Q` - Quarterly Report
- `8-K` - Current Report
- `DEF 14A` - Proxy Statement
- `4` - Insider Trading
- `13F-HR` - Institutional Holdings

---

### 11. edgar_current_reports
**Track 8-K material events**

```python
from enhanced_edgar_tool import EDGARCurrentReportsTool

tool = EDGARCurrentReportsTool()
result = tool.execute({
    'cik': '320193',
    'start_date': '2024-01-01',
    'limit': 10
})

print(f"8-K Reports in 2024: {result['reports_count']}")
for report in result['reports']:
    print(f"  {report['filingDate']}: {report['primaryDocDescription']}")
```

**8-K Triggers:** Earnings, M&A, CEO changes, bankruptcies, etc.

---

### 12. edgar_proxy_statements
**Get shareholder voting information**

```python
from enhanced_edgar_tool import EDGARProxyStatementsTool

tool = EDGARProxyStatementsTool()
result = tool.execute({'cik': '320193', 'limit': 3})

print(f"Proxy Statements: {result['statements_count']}")
```

**Contains:** Executive compensation, board elections, shareholder proposals

---

### 13. edgar_registration_statements
**Track IPOs and securities registrations**

```python
from enhanced_edgar_tool import EDGARRegistrationStatementsTool

tool = EDGARRegistrationStatementsTool()
result = tool.execute({
    'cik': '1318605',  # Tesla
    'form_type': 'S-1',
    'limit': 5
})
```

**Form Types:**
- `S-1` - IPO Registration
- `S-3` - Shelf Registration
- `S-4` - Merger/Acquisition
- `S-8` - Employee Stock Plans

---

### 14. edgar_foreign_issuers
**Access foreign company filings**

```python
from enhanced_edgar_tool import EDGARForeignIssuersTool

tool = EDGARForeignIssuersTool()
result = tool.execute({
    'cik': '0001679788',  # Example foreign issuer
    'form_type': '20-F',  # Annual report
    'limit': 5
})
```

**Forms:**
- `20-F` - Annual Report (Foreign)
- `6-K` - Current Report (Foreign)
- `40-F` - Annual Report (Canadian)

---

### 15. edgar_amendments
**Track corrected filings**

```python
from enhanced_edgar_tool import EDGARAmendmentsTool

tool = EDGARAmendmentsTool()
result = tool.execute({'cik': '320193', 'limit': 10})

print(f"Amendments: {result['amendments_count']}")
for amendment in result['amendments']:
    print(f"  {amendment['form']} - {amendment['filingDate']}")
```

**⚠️ Red Flag:** Multiple amendments may indicate accounting issues

---

### 16. edgar_insider_transactions
**Monitor Form 4 insider trades**

```python
from enhanced_edgar_tool import EDGARInsiderTransactionsTool

tool = EDGARInsiderTransactionsTool()
result = tool.execute({'cik': '320193', 'limit': 20})

print(f"Insider Transactions: {result['transactions_count']}")
for txn in result['transactions'][:5]:
    print(f"  Filed: {txn['filingDate']} - {txn['reportDate']}")
```

**Who Files:** Officers, directors, 10%+ shareholders

---

### 17. edgar_ownership_reports
**Track activist investors (SC 13D/G)**

```python
from enhanced_edgar_tool import EDGAROwnershipReportsTool

tool = EDGAROwnershipReportsTool()
result = tool.execute({
    'cik': '320193',
    'form_type': 'SC 13D',  # Activist
    'limit': 10
})
```

**SC 13D vs 13G:**
- `SC 13D` - Activist intent (control/influence)
- `SC 13G` - Passive investment

---

### 18. edgar_institutional_holdings
**Access 13F portfolio holdings**

```python
from enhanced_edgar_tool import EDGARInstitutionalHoldingsTool

tool = EDGARInstitutionalHoldingsTool()

# Berkshire Hathaway portfolio
result = tool.execute({
    'cik': '1067983',  # Warren Buffett's Berkshire
    'limit': 8
})

print(f"13F Filings: {result['filings_count']}")
```

**Notable Institutions:**
- `1067983` - Berkshire Hathaway
- `0000102909` - Vanguard
- `1037389` - Renaissance Technologies

---

### 19. edgar_mutual_fund_holdings
**Get mutual fund positions (N-PORT)**

```python
from enhanced_edgar_tool import EDGARMutualFundHoldingsTool

tool = EDGARMutualFundHoldingsTool()
result = tool.execute({
    'cik': '0000862084',  # Example mutual fund
    'limit': 6
})
```

**Filed:** Monthly with 30-day lag

---

### 20. edgar_xbrl_frames_multi_concept
**Batch retrieve multiple metrics**

```python
from enhanced_edgar_tool import EDGARXBRLFramesMultiConceptTool

tool = EDGARXBRLFramesMultiConceptTool()
result = tool.execute({
    'taxonomy': 'us-gaap',
    'concepts': ['Revenues', 'NetIncomeLoss', 'Assets'],
    'year': 2023,
    'quarter': 'CY'
})

print(f"Concepts retrieved: {result['concepts_retrieved']}")
for concept, data in result['data_by_concept'].items():
    print(f"\n{concept}: {data['units_count']} companies")
```

---

## Sample Code

### Complete Example: Company Analysis

```python
#!/usr/bin/env python3
"""
Complete EDGAR company analysis example
Demonstrates using multiple tools together
"""

from enhanced_edgar_tool import (
    EDGARCompanySearchTool,
    EDGARCompanySubmissionsTool,
    EDGARCompanyConceptTool,
    EDGARFinancialRatiosTool,
    EDGARInsiderTransactionsTool
)

def analyze_company(ticker_or_name):
    """Complete company analysis workflow"""
    
    # Step 1: Find company CIK
    print(f"\n{'='*60}")
    print(f"Analyzing: {ticker_or_name}")
    print('='*60)
    
    search_tool = EDGARCompanySearchTool()
    search_result = search_tool.execute({'query': ticker_or_name, 'limit': 1})
    
    if search_result['results_count'] == 0:
        print("❌ Company not found")
        return
    
    company = search_result['companies'][0]
    cik = company['cik']
    print(f"\n✓ Found: {company['title']} ({company['ticker']})")
    print(f"  CIK: {cik}")
    print(f"  Exchange: {company['exchange']}")
    
    # Step 2: Get company information
    print(f"\n{'─'*60}")
    print("COMPANY INFORMATION")
    print('─'*60)
    
    submissions_tool = EDGARCompanySubmissionsTool()
    info = submissions_tool.execute({'cik': cik})
    
    print(f"Industry: {info['sicDescription']} (SIC: {info['sic']})")
    print(f"Fiscal Year End: {info['fiscalYearEnd']}")
    print(f"Category: {info['category']}")
    print(f"Recent Filings: {info['filings_count']}")
    
    # Step 3: Get revenue history
    print(f"\n{'─'*60}")
    print("REVENUE HISTORY (Last 5 Years)")
    print('─'*60)
    
    concept_tool = EDGARCompanyConceptTool()
    try:
        revenue = concept_tool.execute({
            'cik': cik,
            'concept': 'Revenues'
        })
        
        # Get annual revenues
        usd_values = revenue['units'].get('USD', [])
        annual = [v for v in usd_values if v.get('fp') == 'FY']
        
        for obs in sorted(annual, key=lambda x: x['fy'], reverse=True)[:5]:
            print(f"  FY{obs['fy']}: ${obs['val']:,.0f}")
    except:
        print("  Revenue data not available")
    
    # Step 4: Calculate financial ratios
    print(f"\n{'─'*60}")
    print("FINANCIAL RATIOS (Latest Year)")
    print('─'*60)
    
    ratios_tool = EDGARFinancialRatiosTool()
    try:
        ratios = ratios_tool.execute({'cik': cik, 'fiscal_year': 2023})
        
        print("\nProfitability:")
        prof = ratios['profitability_ratios']
        if prof.get('gross_margin'):
            print(f"  Gross Margin: {prof['gross_margin']:.1f}%")
        if prof.get('net_margin'):
            print(f"  Net Margin: {prof['net_margin']:.1f}%")
        if prof.get('return_on_equity'):
            print(f"  ROE: {prof['return_on_equity']:.1f}%")
        
        print("\nLiquidity:")
        liq = ratios['liquidity_ratios']
        if liq.get('current_ratio'):
            print(f"  Current Ratio: {liq['current_ratio']:.2f}")
        
        print("\nSolvency:")
        solv = ratios['solvency_ratios']
        if solv.get('debt_to_equity'):
            print(f"  Debt/Equity: {solv['debt_to_equity']:.2f}")
    except Exception as e:
        print(f"  Ratios not available: {e}")
    
    # Step 5: Check insider activity
    print(f"\n{'─'*60}")
    print("RECENT INSIDER TRANSACTIONS")
    print('─'*60)
    
    insider_tool = EDGARInsiderTransactionsTool()
    try:
        insider = insider_tool.execute({'cik': cik, 'limit': 5})
        print(f"  Found {insider['transactions_count']} recent Form 4 filings")
        for txn in insider['transactions'][:3]:
            print(f"  - {txn['filingDate']}: Form 4 filed")
    except:
        print("  No recent insider transactions")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    # Analyze companies
    companies = ['AAPL', 'MSFT', 'TSLA']
    
    for ticker in companies:
        try:
            analyze_company(ticker)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}\n")
```

### Run the Analysis

```bash
python analyze_company.py
```

**Output:**
```
============================================================
Analyzing: AAPL
============================================================

✓ Found: Apple Inc (AAPL)
  CIK: 0000320193
  Exchange: Nasdaq

────────────────────────────────────────────────────────────
COMPANY INFORMATION
────────────────────────────────────────────────────────────
Industry: Services-Prepackaged Software (SIC: 7372)
Fiscal Year End: 0930
Category: Large Accelerated Filer
Recent Filings: 184

────────────────────────────────────────────────────────────
REVENUE HISTORY (Last 5 Years)
────────────────────────────────────────────────────────────
  FY2023: $383,285,000,000
  FY2022: $394,328,000,000
  FY2021: $365,817,000,000
  FY2020: $274,515,000,000
  FY2019: $260,174,000,000

────────────────────────────────────────────────────────────
FINANCIAL RATIOS (Latest Year)
────────────────────────────────────────────────────────────

Profitability:
  Gross Margin: 44.1%
  Net Margin: 25.3%
  ROE: 172.1%

Liquidity:
  Current Ratio: 1.02

Solvency:
  Debt/Equity: 1.81

────────────────────────────────────────────────────────────
RECENT INSIDER TRANSACTIONS
────────────────────────────────────────────────────────────
  Found 85 recent Form 4 filings
  - 2024-10-04: Form 4 filed
  - 2024-10-03: Form 4 filed
  - 2024-10-02: Form 4 filed

============================================================
```

---

## Limitations

### 1. SEC Data Limitations

| Limitation | Description | Impact |
|------------|-------------|--------|
| **Historical Coverage** | XBRL data available from ~2009 onwards | Pre-2009 data limited |
| **Foreign Issuers** | Some foreign companies use IFRS, not US-GAAP | Concept names differ |
| **Private Companies** | No data for private companies | Public companies only |
| **Real-time Data** | Filings available after SEC processing | Minutes to hours delay |
| **Small Companies** | May not file XBRL or have limited data | Data gaps possible |

### 2. Technical Limitations

| Issue | Description | Workaround |
|-------|-------------|------------|
| **Response Size** | Company facts can be 50+ MB | Use `edgar_company_concept` for specific metrics |
| **Rate Limits** | Max 10 requests/second | Built-in rate limiting handles this |
| **Network Timeouts** | Large responses may timeout | Implement retry logic |
| **Concept Naming** | XBRL concepts vary (Revenue vs Revenues) | Try multiple concept names |
| **Missing Data** | Not all companies report all metrics | Handle None values |

### 3. Data Quality Issues

⚠️ **Potential Issues:**
- Amended filings may contain corrections
- Restatements can change historical data
- Concept tagging inconsistencies across companies
- Voluntary disclosure varies by company

**Best Practice:** Always verify critical data with official SEC filings

### 4. Use Case Limitations

❌ **NOT suitable for:**
- Real-time trading signals (delayed data)
- Private company analysis (no data)
- Pre-2009 historical analysis (limited data)
- International companies not registered with SEC

✅ **EXCELLENT for:**
- Fundamental analysis
- Long-term investment research
- Academic research
- Compliance monitoring
- Industry analysis

---

## Best Practices

### 1. Caching Strategy

```python
import json
import os
from datetime import datetime, timedelta

class EDGARCache:
    def __init__(self, cache_dir='edgar_cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key, max_age_hours=24):
        """Get cached data if not expired"""
        cache_file = f"{self.cache_dir}/{key}.json"
        
        if not os.path.exists(cache_file):
            return None
        
        # Check age
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        age = datetime.now() - file_time
        
        if age > timedelta(hours=max_age_hours):
            return None
        
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    def set(self, key, data):
        """Cache data"""
        cache_file = f"{self.cache_dir}/{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f)

# Usage
cache = EDGARCache()

cik = '320193'
cached_data = cache.get(f'submissions_{cik}')

if cached_data:
    print("Using cached data")
    result = cached_data
else:
    print("Fetching from API")
    tool = EDGARCompanySubmissionsTool()
    result = tool.execute({'cik': cik})
    cache.set(f'submissions_{cik}', result)
```

### 2. Error Handling

```python
import time
from enhanced_edgar_tool import EDGARCompanySearchTool

def robust_search(query, max_retries=3):
    """Search with retry logic"""
    tool = EDGARCompanySearchTool()
    
    for attempt in range(max_retries):
        try:
            result = tool.execute({'query': query})
            return result
        
        except ValueError as e:
            if "Rate limit" in str(e):
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} retries")

# Usage
result = robust_search('AAPL')
```

### 3. Batch Processing

```python
import time
from enhanced_edgar_tool import EDGARCompanyConceptTool

def batch_get_revenue(ciks, delay=0.15):
    """Get revenue for multiple companies with rate limiting"""
    tool = EDGARCompanyConceptTool()
    results = {}
    
    for i, cik in enumerate(ciks):
        print(f"Processing {i+1}/{len(ciks)}: CIK {cik}")
        
        try:
            result = tool.execute({
                'cik': cik,
                'concept': 'Revenues'
            })
            results[cik] = result
        except Exception as e:
            print(f"  Error: {e}")
            results[cik] = None
        
        # Rate limiting
        if i < len(ciks) - 1:
            time.sleep(delay)
    
    return results

# Usage
ciks = ['320193', '789019', '1318605']
revenues = batch_get_revenue(ciks)
```

### 4. Data Validation

```python
def validate_financial_data(data):
    """Validate financial data quality"""
    warnings = []
    
    # Check for None values
    if data.get('value') is None:
        warnings.append("Missing value")
    
    # Check for negative revenue (red flag)
    if data.get('concept') == 'Revenue' and data.get('value', 0) < 0:
        warnings.append("Negative revenue - possible error")
    
    # Check for extreme values
    if data.get('value', 0) > 1e15:  # $1 quadrillion
        warnings.append("Unusually large value")
    
    return warnings

# Usage
warnings = validate_financial_data({'concept': 'Revenue', 'value': 1000000})
if warnings:
    print(f"⚠️ Data quality issues: {', '.join(warnings)}")
```

---

## Troubleshooting

### Common Errors

#### 1. HTTP 403 Forbidden

**Error:**
```
ValueError: Access forbidden. Ensure User-Agent header is properly set.
```

**Solution:**
```python
# Verify User-Agent is set
from enhanced_edgar_tool import EDGARBaseTool

tool = EDGARBaseTool()
print(tool.headers['User-Agent'])  # Must include email
```

#### 2. Rate Limit Exceeded

**Error:**
```
ValueError: Rate limit exceeded. SEC allows max 10 requests/second.
```

**Solution:**
- Built-in rate limiting should prevent this
- If occurs, implement exponential backoff
- Check for parallel requests (not allowed)

#### 3. Company Not Found

**Error:**
```
ValueError: Resource not found
```

**Causes:**
- Invalid CIK
- Company no longer trades publicly
- Typo in ticker/name

**Solution:**
```python
# Use search tool first
search_tool = EDGARCompanySearchTool()
result = search_tool.execute({'query': 'AAPL'})

if result['results_count'] == 0:
    print("Company not found")
else:
    cik = result['companies'][0]['cik']
```

#### 4. Concept Not Found

**Error:**
```
ValueError: Resource not found: .../Revenues.json
```

**Cause:** XBRL concept name varies (Revenue vs Revenues vs RevenueFromContractWithCustomer...)

**Solution:**
```python
# Try multiple concept names
concept_names = ['Revenues', 'Revenue', 'RevenueFromContractWithCustomerExcludingAssessedTax']

for concept in concept_names:
    try:
        result = tool.execute({'cik': cik, 'concept': concept})
        print(f"✓ Found: {concept}")
        break
    except ValueError:
        continue
else:
    print("❌ Revenue concept not found")
```

#### 5. Large Response Timeout

**Error:**
```
urllib.error.URLError: <urlopen error timed out>
```

**Solution:**
```python
# Increase timeout
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=60) as response:  # 60s timeout
    data = json.loads(response.read().decode('utf-8'))
```

### Getting Help

**For SEC EDGAR API issues:**
- SEC API Documentation: https://www.sec.gov/edgar/sec-api-documentation
- SEC Support: webmaster@sec.gov

**For toolkit issues:**
- Check documentation
- Review sample code
- Verify Python version (3.7+)
- Check internet connection

---

## Legal Notice

### Copyright

**Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.**

This software and documentation are protected by copyright law. Unauthorized reproduction or distribution of this software, or any portion of it, may result in severe civil and criminal penalties.

### License

This software is provided "as is" without warranty of any kind, express or implied. The author assumes no responsibility for errors or omissions in this software or documentation.

### Data Source

All data accessed through this toolkit is publicly available from the U.S. Securities and Exchange Commission (SEC) EDGAR database. The SEC makes this data available free of charge to the public.

### Disclaimer

**This toolkit is for informational and research purposes only.**

- ❌ NOT investment advice
- ❌ NOT legal advice
- ❌ NOT accounting advice
- ❌ NOT financial advice

**Always consult with qualified professionals before making investment or business decisions.**

### Compliance

Users of this toolkit must:
- ✅ Comply with SEC fair access guidelines
- ✅ Include proper User-Agent header with contact information
- ✅ Respect rate limits (10 requests/second maximum)
- ✅ Use data responsibly and legally
- ✅ Not attempt to overwhelm or disrupt SEC systems

### Attribution

If using this toolkit in research or publications:

**Suggested Citation:**
```
Sinha, A. (2025). Enhanced EDGAR MCP Tools (Version 1.0.0) [Computer software].
Email: ajsinha@gmail.com
```

### Contact

**Ashutosh Sinha**  
Email: ajsinha@gmail.com

For bug reports, feature requests, or questions about the toolkit.

---

**Last Updated:** November 2025  
**Version:** 1.0.0  
**Document Version:** 1.0

---

*End of Documentation*
