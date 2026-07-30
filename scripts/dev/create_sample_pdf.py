"""Create a sample company policy PDF for testing"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch

def create_sample_pdf():
    """Create a multi-page company policy PDF with real content"""

    filename = "samples/company_policy.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("<b>Company Employee Handbook - 2024</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*inch))

    # Introduction
    intro = Paragraph("""
    <b>Welcome to TechCorp Solutions</b><br/><br/>
    This employee handbook provides important information about our company policies,
    procedures, and expectations. Please read it carefully and keep it for future reference.
    All employees are expected to understand and comply with these policies.
    """, styles['Normal'])
    story.append(intro)
    story.append(Spacer(1, 0.3*inch))

    # Vacation Policy
    story.append(Paragraph("<b>1. Vacation and Time Off Policy</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    vacation = Paragraph("""
    <b>Paid Time Off (PTO):</b> Full-time employees accrue 15 days of paid vacation per year,
    starting from their first day of employment. PTO accrues at a rate of 1.25 days per month.
    Employees may carry over up to 5 unused vacation days to the following year. Any days
    beyond this limit will be forfeited unless approved by management.<br/><br/>

    <b>Sick Leave:</b> Employees receive 10 days of sick leave annually. Sick leave does not
    roll over to the next year. Medical documentation may be required for absences exceeding
    3 consecutive days.<br/><br/>

    <b>Holidays:</b> The company observes 10 federal holidays including New Year's Day,
    Memorial Day, Independence Day, Labor Day, Thanksgiving, and Christmas. A complete list
    is posted on the company intranet.
    """, styles['Normal'])
    story.append(vacation)
    story.append(PageBreak())

    # Work Schedule
    story.append(Paragraph("<b>2. Work Schedule and Remote Work</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    schedule = Paragraph("""
    <b>Standard Hours:</b> Our standard work week is Monday through Friday, 9:00 AM to 5:00 PM,
    with a one-hour lunch break. Total work week is 40 hours. Employees are expected to be
    punctual and maintain regular attendance.<br/><br/>

    <b>Remote Work Policy:</b> Employees may work remotely up to 2 days per week with manager
    approval. Remote work arrangements must be documented and approved in writing. Employees
    working remotely are expected to maintain the same productivity levels and be available
    during core business hours (10:00 AM - 3:00 PM).<br/><br/>

    <b>Flexible Hours:</b> With manager approval, employees may request flexible start and
    end times to accommodate personal needs, provided they complete their required 40 hours
    per week and attend all required meetings.
    """, styles['Normal'])
    story.append(schedule)
    story.append(PageBreak())

    # Benefits
    story.append(Paragraph("<b>3. Employee Benefits</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    benefits = Paragraph("""
    <b>Health Insurance:</b> The company provides comprehensive health insurance coverage
    including medical, dental, and vision. The company pays 80% of the premium for employee
    coverage and 60% for family coverage. Enrollment begins on the first day of the month
    following 30 days of employment.<br/><br/>

    <b>401(k) Retirement Plan:</b> Employees are eligible to participate in the company's
    401(k) plan after 90 days of employment. The company matches 50% of employee contributions
    up to 6% of salary. Employees are immediately vested in their own contributions and vest
    in company matching contributions over 4 years.<br/><br/>

    <b>Professional Development:</b> The company provides $2,000 annually per employee for
    professional development, including conferences, training courses, and certifications
    relevant to their role. Employees must submit requests for approval before registering.
    """, styles['Normal'])
    story.append(benefits)
    story.append(PageBreak())

    # Code of Conduct
    story.append(Paragraph("<b>4. Code of Conduct</b>", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))

    conduct = Paragraph("""
    <b>Professional Behavior:</b> All employees are expected to maintain professional behavior
    at all times. This includes treating colleagues, clients, and partners with respect,
    maintaining confidentiality, and representing the company positively.<br/><br/>

    <b>Harassment Policy:</b> The company maintains a zero-tolerance policy for harassment
    of any kind. This includes sexual harassment, discrimination based on protected
    characteristics, bullying, or any behavior that creates a hostile work environment.
    Violations will result in immediate disciplinary action up to and including termination.<br/><br/>

    <b>Confidentiality:</b> Employees must protect confidential company information, including
    trade secrets, client data, and proprietary processes. This obligation continues even
    after employment ends. Violations may result in legal action.
    """, styles['Normal'])
    story.append(conduct)

    # Build PDF
    doc.build(story)
    print(f"✅ Created {filename}")
    print(f"   4 pages with company policy content")
    print(f"   Topics: Vacation, Work Schedule, Benefits, Code of Conduct")

if __name__ == "__main__":
    create_sample_pdf()
