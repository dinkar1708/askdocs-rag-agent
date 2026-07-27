#!/usr/bin/env python3
"""
Script to generate test files for RAG system testing.
"""

import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import pandas as pd
from datetime import datetime
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def create_plain_text_pdf():
    """Create a simple text-based PDF (employee handbook)"""
    filename = os.path.join(SCRIPT_DIR, "plain-text.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1  # Center
    )

    story.append(Paragraph("Employee Handbook 2024", title_style))
    story.append(Spacer(1, 0.5*inch))

    # Introduction
    story.append(Paragraph("Introduction", styles['Heading1']))
    story.append(Paragraph(
        "Welcome to TechCorp Solutions! This handbook provides essential information about our company policies, "
        "procedures, and benefits. Please read this document carefully and keep it for future reference.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Company Overview
    story.append(Paragraph("Company Overview", styles['Heading1']))
    story.append(Paragraph(
        "TechCorp Solutions was founded in 2010 with a mission to deliver innovative software solutions to businesses "
        "worldwide. We specialize in cloud computing, artificial intelligence, and enterprise software development. "
        "Our team consists of over 500 talented professionals across 15 countries.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Working Hours
    story.append(PageBreak())
    story.append(Paragraph("Working Hours and Attendance", styles['Heading1']))
    story.append(Paragraph(
        "Standard working hours are Monday through Friday, 9:00 AM to 5:00 PM. We offer flexible working arrangements "
        "including remote work options. Employees are expected to maintain regular attendance and notify their supervisor "
        "in case of absence. Core hours when all team members should be available are 10:00 AM to 3:00 PM.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Leave Policy
    story.append(Paragraph("Leave Policy", styles['Heading1']))
    story.append(Paragraph(
        "Full-time employees are entitled to 20 days of paid time off (PTO) per year. This includes vacation days, "
        "sick leave, and personal days. PTO accrues at a rate of 1.67 days per month. Employees must request time off "
        "at least two weeks in advance for planned absences. Unused PTO can be carried over up to 5 days to the next year.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Benefits
    story.append(PageBreak())
    story.append(Paragraph("Employee Benefits", styles['Heading1']))
    story.append(Paragraph(
        "TechCorp offers comprehensive benefits including:",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))

    benefits = [
        "Health Insurance: Medical, dental, and vision coverage with company paying 80% of premiums",
        "Retirement Plan: 401(k) with 5% company match",
        "Life Insurance: Company-paid life insurance equal to 2x annual salary",
        "Professional Development: $2,000 annual budget for training and conferences",
        "Gym Membership: Subsidized membership to local fitness centers",
        "Commuter Benefits: Pre-tax transportation benefits up to $300/month"
    ]

    for benefit in benefits:
        story.append(Paragraph(f"• {benefit}", styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # Code of Conduct
    story.append(PageBreak())
    story.append(Paragraph("Code of Conduct", styles['Heading1']))
    story.append(Paragraph(
        "All employees are expected to maintain professional behavior and treat colleagues with respect. Harassment, "
        "discrimination, or any form of misconduct will not be tolerated. We are committed to maintaining a safe and "
        "inclusive workplace for everyone. Any violations should be reported to Human Resources immediately.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Remote Work Policy
    story.append(Paragraph("Remote Work Policy", styles['Heading1']))
    story.append(Paragraph(
        "Employees may work remotely up to 3 days per week with manager approval. Remote workers must maintain "
        "the same productivity standards as in-office employees. A reliable internet connection and appropriate "
        "workspace are required. Equipment such as laptops and monitors will be provided by the company. "
        "Employees must be available during core hours and attend mandatory in-person meetings.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Performance Reviews
    story.append(PageBreak())
    story.append(Paragraph("Performance Reviews", styles['Heading1']))
    story.append(Paragraph(
        "Performance reviews are conducted annually in December. Reviews assess job performance, goal achievement, "
        "and professional development. Employees receive feedback from their direct manager and have the opportunity "
        "to discuss career goals. Salary adjustments and promotions are determined based on performance reviews and "
        "are effective January 1st of the following year.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Termination Policy
    story.append(Paragraph("Termination Policy", styles['Heading1']))
    story.append(Paragraph(
        "Employment at TechCorp is at-will, meaning either party can terminate the relationship at any time. "
        "Two weeks' notice is expected from resigning employees. Final paychecks will include payment for unused PTO. "
        "Company property must be returned, and access credentials will be revoked on the last working day. "
        "Exit interviews are conducted to gather feedback and ensure smooth transitions.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Contact Information
    story.append(PageBreak())
    story.append(Paragraph("Contact Information", styles['Heading1']))
    story.append(Paragraph(
        "For questions about this handbook or company policies, please contact:",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Human Resources Department", styles['BodyText']))
    story.append(Paragraph("Email: hr@techcorp.com", styles['BodyText']))
    story.append(Paragraph("Phone: (555) 123-4567", styles['BodyText']))
    story.append(Paragraph("Office Hours: Monday-Friday, 9:00 AM - 5:00 PM", styles['BodyText']))

    doc.build(story)
    print(f"Created: {filename}")
    return filename


def create_financial_report_pdf():
    """Create a PDF with financial tables"""
    filename = os.path.join(SCRIPT_DIR, "financial-report-with-tables.pdf")
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=1
    )

    story.append(Paragraph("TechCorp Solutions Inc.", title_style))
    story.append(Paragraph("Quarterly Financial Report - Q2 2024", styles['Heading2']))
    story.append(Spacer(1, 0.3*inch))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    story.append(Paragraph(
        "TechCorp Solutions reported strong financial performance in Q2 2024 with revenue of $125.5 million, "
        "representing a 18% increase year-over-year. Net income reached $23.4 million with an operating margin "
        "of 22.5%. The company continues to invest in research and development while maintaining healthy cash reserves.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.3*inch))

    # Income Statement
    story.append(Paragraph("Consolidated Statement of Income", styles['Heading1']))
    story.append(Paragraph("(In thousands, except per share data)", styles['Italic']))
    story.append(Spacer(1, 0.2*inch))

    income_data = [
        ['', 'Q2 2024', 'Q2 2023', 'Change (%)'],
        ['Revenue', '$125,500', '$106,400', '18.0%'],
        ['Cost of Revenue', '$45,200', '$39,800', '13.6%'],
        ['Gross Profit', '$80,300', '$66,600', '20.6%'],
        ['Operating Expenses:', '', '', ''],
        ['  Research & Development', '$28,500', '$24,200', '17.8%'],
        ['  Sales & Marketing', '$18,200', '$15,800', '15.2%'],
        ['  General & Administrative', '$5,400', '$4,900', '10.2%'],
        ['Total Operating Expenses', '$52,100', '$44,900', '16.0%'],
        ['Operating Income', '$28,200', '$21,700', '30.0%'],
        ['Interest Income', '$1,200', '$800', '50.0%'],
        ['Income Before Taxes', '$29,400', '$22,500', '30.7%'],
        ['Income Tax Expense', '$6,000', '$4,700', '27.7%'],
        ['Net Income', '$23,400', '$17,800', '31.5%'],
        ['', '', '', ''],
        ['Earnings Per Share:', '', '', ''],
        ['  Basic', '$2.34', '$1.78', '31.5%'],
        ['  Diluted', '$2.31', '$1.76', '31.3%'],
    ]

    income_table = Table(income_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1*inch])
    income_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 4), (0, 7), 'Helvetica-Bold'),
        ('FONTNAME', (0, 15), (0, -1), 'Helvetica-Bold'),
    ]))

    story.append(income_table)
    story.append(Spacer(1, 0.4*inch))

    # Balance Sheet
    story.append(PageBreak())
    story.append(Paragraph("Consolidated Balance Sheet", styles['Heading1']))
    story.append(Paragraph("(In thousands)", styles['Italic']))
    story.append(Spacer(1, 0.2*inch))

    balance_data = [
        ['Assets', 'June 30, 2024', 'March 31, 2024'],
        ['Current Assets:', '', ''],
        ['  Cash and Cash Equivalents', '$145,200', '$132,800'],
        ['  Short-term Investments', '$67,500', '$62,300'],
        ['  Accounts Receivable', '$42,800', '$38,600'],
        ['  Inventory', '$12,400', '$11,200'],
        ['  Prepaid Expenses', '$8,100', '$7,500'],
        ['Total Current Assets', '$276,000', '$252,400'],
        ['Property and Equipment, net', '$45,600', '$43,200'],
        ['Intangible Assets', '$32,800', '$34,100'],
        ['Goodwill', '$56,200', '$56,200'],
        ['Other Long-term Assets', '$18,400', '$17,300'],
        ['Total Assets', '$429,000', '$403,200'],
        ['', '', ''],
        ['Liabilities and Equity', '', ''],
        ['Current Liabilities:', '', ''],
        ['  Accounts Payable', '$28,400', '$26,100'],
        ['  Accrued Expenses', '$35,200', '$32,800'],
        ['  Deferred Revenue', '$45,600', '$41,200'],
        ['Total Current Liabilities', '$109,200', '$100,100'],
        ['Long-term Debt', '$50,000', '$50,000'],
        ['Other Long-term Liabilities', '$12,800', '$11,900'],
        ['Total Liabilities', '$172,000', '$162,000'],
        ['', '', ''],
        ['Stockholders Equity:', '', ''],
        ['  Common Stock', '$100', '$100'],
        ['  Additional Paid-in Capital', '$185,600', '$180,200'],
        ['  Retained Earnings', '$71,300', '$60,900'],
        ['Total Stockholders Equity', '$257,000', '$241,200'],
        ['Total Liabilities and Equity', '$429,000', '$403,200'],
    ]

    balance_table = Table(balance_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    balance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (0, 12), 'Helvetica-Bold'),
        ('FONTNAME', (0, 14), (0, 14), 'Helvetica-Bold'),
    ]))

    story.append(balance_table)
    story.append(Spacer(1, 0.4*inch))

    # Cash Flow Statement
    story.append(PageBreak())
    story.append(Paragraph("Consolidated Statement of Cash Flows", styles['Heading1']))
    story.append(Paragraph("(In thousands)", styles['Italic']))
    story.append(Spacer(1, 0.2*inch))

    cashflow_data = [
        ['', 'Q2 2024', 'Q2 2023'],
        ['Operating Activities:', '', ''],
        ['  Net Income', '$23,400', '$17,800'],
        ['  Adjustments:', '', ''],
        ['    Depreciation and Amortization', '$5,600', '$4,800'],
        ['    Stock-based Compensation', '$4,200', '$3,500'],
        ['    Changes in Operating Assets and Liabilities', '$3,800', '$2,900'],
        ['Net Cash from Operating Activities', '$37,000', '$29,000'],
        ['', '', ''],
        ['Investing Activities:', '', ''],
        ['  Purchase of Property and Equipment', '($7,200)', '($5,400)'],
        ['  Purchase of Investments', '($15,400)', '($12,300)'],
        ['  Sale of Investments', '$10,200', '$8,600'],
        ['Net Cash from Investing Activities', '($12,400)', '($9,100)'],
        ['', '', ''],
        ['Financing Activities:', '', ''],
        ['  Proceeds from Stock Issuance', '$1,200', '$900'],
        ['  Repurchase of Common Stock', '($12,400)', '($8,200)'],
        ['  Payment of Dividends', '($1,000)', '($800)'],
        ['Net Cash from Financing Activities', '($12,200)', '($8,100)'],
        ['', '', ''],
        ['Net Increase in Cash', '$12,400', '$11,800'],
        ['Cash at Beginning of Period', '$132,800', '$98,400'],
        ['Cash at End of Period', '$145,200', '$110,200'],
    ]

    cashflow_table = Table(cashflow_data, colWidths=[4*inch, 1.5*inch, 1.5*inch])
    cashflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
    ]))

    story.append(cashflow_table)

    doc.build(story)
    print(f"Created: {filename}")
    return filename


def create_product_catalog_excel():
    """Create an Excel file with product catalog"""
    filename = os.path.join(SCRIPT_DIR, "product-catalog.xlsx")

    products = [
        ("Wireless Mouse", "WM-001", 29.99, "Electronics", 150),
        ("USB-C Cable 6ft", "CB-002", 12.99, "Accessories", 300),
        ("Mechanical Keyboard", "KB-003", 89.99, "Electronics", 75),
        ("Laptop Stand", "LS-004", 45.50, "Accessories", 120),
        ("HD Webcam", "WC-005", 79.99, "Electronics", 60),
        ("Desk Lamp LED", "DL-006", 34.99, "Office Supplies", 200),
        ("Ergonomic Chair", "CH-007", 299.99, "Furniture", 45),
        ("Monitor 27 inch", "MN-008", 349.99, "Electronics", 30),
        ("Noise Cancelling Headphones", "HP-009", 199.99, "Electronics", 85),
        ("Wireless Charger", "WC-010", 24.99, "Accessories", 180),
        ("External SSD 1TB", "SD-011", 129.99, "Storage", 90),
        ("Portable Speaker", "SP-012", 59.99, "Electronics", 110),
        ("Screen Protector", "PR-013", 9.99, "Accessories", 400),
        ("Phone Case", "PC-014", 19.99, "Accessories", 250),
        ("Tablet Stand", "TS-015", 22.99, "Accessories", 140),
        ("Document Scanner", "SC-016", 159.99, "Electronics", 50),
        ("Wireless Keyboard", "KB-017", 54.99, "Electronics", 95),
        ("Desk Organizer", "DO-018", 18.99, "Office Supplies", 175),
        ("Cable Management Box", "CM-019", 14.99, "Office Supplies", 220),
        ("Monitor Arm Mount", "MA-020", 79.99, "Accessories", 65),
        ("Bluetooth Adapter", "BT-021", 16.99, "Electronics", 190),
        ("Graphics Tablet", "GT-022", 249.99, "Electronics", 40),
        ("Surge Protector", "SP-023", 27.99, "Electronics", 160),
        ("Laptop Sleeve 15 inch", "LS-024", 21.99, "Accessories", 210),
        ("Webcam Cover", "WC-025", 5.99, "Accessories", 500),
        ("USB Hub 7-Port", "UH-026", 32.99, "Electronics", 125),
        ("Mousepad XL", "MP-027", 19.99, "Accessories", 280),
        ("Cable Clips 20-Pack", "CC-028", 7.99, "Office Supplies", 450),
        ("Wireless Presenter", "WP-029", 39.99, "Electronics", 70),
        ("Laptop Cooling Pad", "CP-030", 29.99, "Accessories", 105),
    ]

    df = pd.DataFrame(products, columns=['Product Name', 'SKU', 'Price', 'Category', 'Stock Level'])

    # Create Excel writer
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)

        # Add a summary sheet
        summary_data = {
            'Category': df['Category'].unique(),
            'Product Count': [len(df[df['Category'] == cat]) for cat in df['Category'].unique()],
            'Total Value': [df[df['Category'] == cat]['Price'].sum() for cat in df['Category'].unique()],
            'Avg Price': [df[df['Category'] == cat]['Price'].mean() for cat in df['Category'].unique()],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Category Summary', index=False)

        # Add inventory sheet
        inventory_df = df[['SKU', 'Product Name', 'Stock Level']].copy()
        inventory_df['Reorder Needed'] = inventory_df['Stock Level'] < 100
        inventory_df.to_excel(writer, sheet_name='Inventory Status', index=False)

    print(f"Created: {filename}")
    return filename


def create_technical_manual_pdf():
    """Create a PDF with diagrams (using simple geometric shapes as diagrams)"""
    filename = os.path.join(SCRIPT_DIR, "technical-manual-with-diagrams.pdf")

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Page 1 - Title Page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-100, "Technical Manual")
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, height-140, "CloudServer Pro X500")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-180, "Installation and Configuration Guide")
    c.drawCentredString(width/2, height-200, "Version 2.5")
    c.drawCentredString(width/2, 50, "TechCorp Solutions - 2024")

    # Page 2 - System Architecture
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "System Architecture")

    c.setFont("Helvetica", 11)
    c.drawString(50, height-80, "The CloudServer Pro X500 consists of the following components:")

    # Draw a simple architecture diagram
    # Load Balancer
    c.setFillColorRGB(0.2, 0.4, 0.8)
    c.rect(250, height-180, 100, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(300, height-165, "Load Balancer")

    # Application Servers
    c.setFillColorRGB(0.3, 0.6, 0.3)
    c.rect(150, height-280, 90, 40, fill=1)
    c.rect(260, height-280, 90, 40, fill=1)
    c.rect(370, height-280, 90, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(195, height-265, "App Server 1")
    c.drawCentredString(305, height-265, "App Server 2")
    c.drawCentredString(415, height-265, "App Server 3")

    # Database
    c.setFillColorRGB(0.8, 0.4, 0.2)
    c.rect(250, height-380, 100, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(300, height-365, "Database")

    # Draw connecting lines
    c.setStrokeColorRGB(0, 0, 0)
    c.line(300, height-180, 195, height-240)
    c.line(300, height-180, 305, height-240)
    c.line(300, height-180, 415, height-240)
    c.line(195, height-280, 270, height-340)
    c.line(305, height-280, 300, height-340)
    c.line(415, height-280, 330, height-340)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(50, height-420, "Figure 1: High-level system architecture showing load balancer, application servers, and database.")

    # Specifications
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-460, "Hardware Specifications:")
    c.setFont("Helvetica", 11)
    specs = [
        "• CPU: Dual Intel Xeon Gold 6248R (48 cores total)",
        "• RAM: 256 GB DDR4 ECC",
        "• Storage: 4x 2TB NVMe SSD in RAID 10",
        "• Network: Dual 10Gb Ethernet ports",
        "• Power: Redundant 1200W power supplies",
    ]
    y = height - 485
    for spec in specs:
        c.drawString(70, y, spec)
        y -= 20

    # Page 3 - Installation Steps
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "Installation Process")

    c.setFont("Helvetica", 11)
    y = height - 90

    steps = [
        ("Step 1: Physical Installation", [
            "Rack mount the server using the included rails",
            "Connect power cables to both PSUs",
            "Connect network cables to both NICs",
            "Connect KVM or management console"
        ]),
        ("Step 2: BIOS Configuration", [
            "Power on the server and enter BIOS (F2 during boot)",
            "Enable virtualization support (VT-x, VT-d)",
            "Configure RAID controller for RAID 10",
            "Set boot order to SSD first"
        ]),
        ("Step 3: Operating System Installation", [
            "Boot from installation media",
            "Select custom installation",
            "Configure network settings (static IP recommended)",
            "Complete OS installation and initial updates"
        ]),
    ]

    for step_title, step_items in steps:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, step_title)
        y -= 20
        c.setFont("Helvetica", 10)
        for item in step_items:
            c.drawString(70, y, f"• {item}")
            y -= 18
        y -= 10

    # Page 4 - Network Configuration Diagram
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "Network Configuration")

    c.setFont("Helvetica", 11)
    c.drawString(50, height-80, "Recommended network topology for production deployment:")

    # Draw network diagram
    # Internet
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.circle(300, height-140, 30, fill=1)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(300, height-145, "Internet")

    # Firewall
    c.setFillColorRGB(0.8, 0.2, 0.2)
    c.rect(250, height-220, 100, 35, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(300, height-207, "Firewall")

    # DMZ
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setDash(3, 3)
    c.rect(100, height-340, 400, 80, fill=0)
    c.setDash()
    c.setFillColorRGB(0, 0, 0)
    c.drawString(110, height-270, "DMZ")

    # Servers in DMZ
    c.setFillColorRGB(0.2, 0.6, 0.8)
    c.rect(150, height-320, 70, 40, fill=1)
    c.rect(380, height-320, 70, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(185, height-305, "Web Server")
    c.drawCentredString(415, height-305, "App Server")

    # Internal Network
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setDash(3, 3)
    c.rect(100, height-470, 400, 80, fill=0)
    c.setDash()
    c.setFillColorRGB(0, 0, 0)
    c.drawString(110, height-400, "Internal Network")

    # Database in internal network
    c.setFillColorRGB(0.8, 0.4, 0.2)
    c.rect(250, height-450, 100, 40, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(300, height-435, "Database")

    # Connection lines
    c.setStrokeColorRGB(0, 0, 0)
    c.line(300, height-170, 300, height-220)
    c.line(300, height-255, 185, height-280)
    c.line(300, height-255, 415, height-280)
    c.line(185, height-320, 185, height-360)
    c.line(415, height-320, 415, height-360)
    c.line(185, height-360, 270, height-410)
    c.line(415, height-360, 330, height-410)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 10)
    c.drawString(50, height-500, "Figure 2: Network topology with DMZ and internal network separation")

    # Configuration details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height-540, "Network Settings:")
    c.setFont("Helvetica", 10)
    configs = [
        "DMZ Subnet: 192.168.10.0/24",
        "Internal Subnet: 10.0.1.0/24",
        "Firewall Rules: Allow HTTP/HTTPS from Internet to DMZ",
        "                Block direct Internet access to Internal Network",
        "                Allow DMZ to Internal on specific ports (3306, 5432)",
    ]
    y = height - 560
    for config in configs:
        c.drawString(70, y, config)
        y -= 18

    # Page 5 - Troubleshooting
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "Troubleshooting Guide")

    c.setFont("Helvetica", 11)
    y = height - 90

    issues = [
        ("Server won't boot", [
            "Check power connections to both PSUs",
            "Verify RAM is properly seated",
            "Check BIOS error codes on front panel",
            "Reset CMOS if configuration is corrupted"
        ]),
        ("Network connectivity issues", [
            "Verify cable connections are secure",
            "Check link lights on NIC ports",
            "Confirm IP configuration matches network",
            "Test with different cable or switch port",
            "Review firewall rules for blocking"
        ]),
        ("Performance degradation", [
            "Monitor CPU and memory utilization",
            "Check disk I/O statistics",
            "Review application logs for errors",
            "Verify RAID array is healthy",
            "Check for thermal throttling"
        ]),
        ("Database connection failures", [
            "Confirm database service is running",
            "Verify firewall allows traffic on database port",
            "Check database user permissions",
            "Review database logs for errors",
            "Test connection from application server"
        ]),
    ]

    for issue_title, issue_steps in issues:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, issue_title)
        y -= 20
        c.setFont("Helvetica", 10)
        for step in issue_steps:
            c.drawString(70, y, f"• {step}")
            y -= 18
        y -= 15

    c.save()
    print(f"Created: {filename}")
    return filename


def create_ground_truth_json():
    """Create ground truth test queries and answers"""
    filename = os.path.join(SCRIPT_DIR, "ground_truth.json")

    ground_truth = {
        "plain-text.pdf": [
            {
                "query": "How many days of PTO do full-time employees get per year?",
                "expected_answer": "Full-time employees are entitled to 20 days of paid time off (PTO) per year.",
                "category": "benefits"
            },
            {
                "query": "What are the standard working hours?",
                "expected_answer": "Standard working hours are Monday through Friday, 9:00 AM to 5:00 PM.",
                "category": "policy"
            },
            {
                "query": "How much does the company match for 401(k)?",
                "expected_answer": "The company provides a 401(k) with 5% company match.",
                "category": "benefits"
            },
            {
                "query": "How many days per week can employees work remotely?",
                "expected_answer": "Employees may work remotely up to 3 days per week with manager approval.",
                "category": "policy"
            },
            {
                "query": "What is the professional development budget?",
                "expected_answer": "Employees receive a $2,000 annual budget for training and conferences.",
                "category": "benefits"
            }
        ],
        "financial-report-with-tables.pdf": [
            {
                "query": "What was the total revenue in Q2 2024?",
                "expected_answer": "The total revenue in Q2 2024 was $125,500 thousand or $125.5 million.",
                "category": "financial_metrics"
            },
            {
                "query": "What was the net income for Q2 2024?",
                "expected_answer": "The net income for Q2 2024 was $23,400 thousand or $23.4 million.",
                "category": "financial_metrics"
            },
            {
                "query": "How much did revenue increase year-over-year?",
                "expected_answer": "Revenue increased by 18.0% year-over-year from Q2 2023 to Q2 2024.",
                "category": "financial_analysis"
            },
            {
                "query": "What was the total cash at the end of Q2 2024?",
                "expected_answer": "Cash and cash equivalents at June 30, 2024 was $145,200 thousand or $145.2 million.",
                "category": "financial_metrics"
            },
            {
                "query": "What were the operating expenses in Q2 2024?",
                "expected_answer": "Total operating expenses in Q2 2024 were $52,100 thousand, consisting of R&D ($28,500), Sales & Marketing ($18,200), and G&A ($5,400).",
                "category": "financial_metrics"
            }
        ],
        "product-catalog.xlsx": [
            {
                "query": "What is the price of the Mechanical Keyboard?",
                "expected_answer": "The Mechanical Keyboard (SKU: KB-003) costs $89.99.",
                "category": "product_info"
            },
            {
                "query": "How many Wireless Mouse units are in stock?",
                "expected_answer": "There are 150 units of Wireless Mouse in stock.",
                "category": "inventory"
            },
            {
                "query": "What products are in the Furniture category?",
                "expected_answer": "The Ergonomic Chair (CH-007) is in the Furniture category.",
                "category": "product_info"
            },
            {
                "query": "What is the most expensive product?",
                "expected_answer": "The most expensive product is the Monitor 27 inch at $349.99.",
                "category": "product_info"
            },
            {
                "query": "Which products have stock level below 100?",
                "expected_answer": "Products with stock below 100 include: Mechanical Keyboard (75), HD Webcam (60), Ergonomic Chair (45), Monitor 27 inch (30), Noise Cancelling Headphones (85), External SSD 1TB (90), Document Scanner (50), Wireless Keyboard (95), Monitor Arm Mount (65), Graphics Tablet (40), and Wireless Presenter (70).",
                "category": "inventory"
            }
        ],
        "technical-manual-with-diagrams.pdf": [
            {
                "query": "What are the RAM specifications for CloudServer Pro X500?",
                "expected_answer": "The CloudServer Pro X500 has 256 GB DDR4 ECC RAM.",
                "category": "specifications"
            },
            {
                "query": "How many cores does the CPU have?",
                "expected_answer": "The server has Dual Intel Xeon Gold 6248R processors with 48 cores total.",
                "category": "specifications"
            },
            {
                "query": "What is the recommended DMZ subnet?",
                "expected_answer": "The recommended DMZ subnet is 192.168.10.0/24.",
                "category": "configuration"
            },
            {
                "query": "What should I do if the server won't boot?",
                "expected_answer": "If the server won't boot, check power connections to both PSUs, verify RAM is properly seated, check BIOS error codes on front panel, and reset CMOS if configuration is corrupted.",
                "category": "troubleshooting"
            },
            {
                "query": "What storage configuration does the server use?",
                "expected_answer": "The server uses 4x 2TB NVMe SSD in RAID 10 configuration.",
                "category": "specifications"
            }
        ]
    }

    with open(filename, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Created: {filename}")
    return filename


if __name__ == "__main__":
    print("Generating test files for RAG system...")
    print("=" * 60)

    files_created = []

    files_created.append(create_plain_text_pdf())
    files_created.append(create_financial_report_pdf())
    files_created.append(create_product_catalog_excel())
    files_created.append(create_technical_manual_pdf())
    files_created.append(create_ground_truth_json())

    print("=" * 60)
    print(f"\nSuccessfully created {len(files_created)} test files!")
    print("\nFiles created:")
    for f in files_created:
        print(f"  - {f}")
