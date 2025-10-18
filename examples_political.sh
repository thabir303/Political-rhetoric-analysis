#!/bin/bash

# Example Usage Script for Political Storage System

echo "=========================================="
echo "Political Article Storage System Examples"
echo "=========================================="
echo ""

# Example 1: Scrape all newspapers for BNP
echo "Example 1: Scraping BNP articles from all newspapers"
echo "Command: python political_scraper.py --party bnp --start-date 2024-10-01 --end-date 2024-10-14"
echo ""
# python political_scraper.py --party bnp --start-date 2024-10-01 --end-date 2024-10-14

# Example 2: Scrape specific newspaper for specific figure
echo "Example 2: Scraping Prothom Alo for Tareq Rahman"
echo "Command: python political_scraper.py --newspaper 'Prothom Alo' --figure 'Tareq Rahman' --start-date 2024-10-01 --end-date 2024-10-14"
echo ""
# python political_scraper.py --newspaper "Prothom Alo" --figure "Tareq Rahman" --start-date 2024-10-01 --end-date 2024-10-14

# Example 3: View storage statistics
echo "Example 3: Viewing storage statistics"
echo "Command: python political_scraper.py --stats-only"
echo ""
# python political_scraper.py --stats-only

# Example 4: Analyze BNP articles
echo "Example 4: Analyzing BNP articles"
echo "Command: python political_analyzer.py --party bnp --limit 10"
echo ""
# python political_analyzer.py --party bnp --limit 10

# Example 5: Generate BNP report
echo "Example 5: Generating comprehensive BNP report"
echo "Command: python political_analyzer.py --party bnp --report --limit 50 > reports/bnp_report.json"
echo ""
# mkdir -p reports
# python political_analyzer.py --party bnp --report --limit 50 > reports/bnp_report.json

# Example 6: Analyze specific figure
echo "Example 6: Analyzing Tareq Rahman articles"
echo "Command: python political_analyzer.py --figure 'Tareq Rahman' --report --limit 30 > reports/tareq_rahman_report.json"
echo ""
# python political_analyzer.py --figure "Tareq Rahman" --report --limit 30 > reports/tareq_rahman_report.json

# Example 7: Scrape all parties for last week
echo "Example 7: Scraping all parties for last 7 days"
START_DATE=$(date -d "7 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)
echo "Command: python political_scraper.py --start-date $START_DATE --end-date $END_DATE"
echo ""
# python political_scraper.py --start-date $START_DATE --end-date $END_DATE

# Example 8: Generate reports for all parties
echo "Example 8: Generating reports for all parties"
echo "Commands:"
echo "  python political_analyzer.py --party bnp --report > reports/bnp_report.json"
echo "  python political_analyzer.py --party ji --report > reports/ji_report.json"
echo "  python political_analyzer.py --party ncp --report > reports/ncp_report.json"
echo "  python political_analyzer.py --party ab_party --report > reports/ab_party_report.json"
echo "  python political_analyzer.py --party gop --report > reports/gop_report.json"
echo "  python political_analyzer.py --party gono_songhati --report > reports/gono_songhati_report.json"
echo "  python political_analyzer.py --party interim_government --report > reports/interim_govt_report.json"
echo ""

echo "=========================================="
echo "To run any example, uncomment the relevant line in this script"
echo "or copy the command and run it directly"
echo "=========================================="
