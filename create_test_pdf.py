from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_test_pdf():
    c = canvas.Canvas("docs/test_banking_policy.pdf", pagesize=A4)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "LOAN APPROVAL POLICY - RETAIL BANKING")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 760, "1. PURPOSE")
    c.drawString(50, 740, "This policy defines the criteria for approving retail loan applications.")
    
    c.drawString(50, 700, "2. ELIGIBILITY CRITERIA")
    c.drawString(50, 680, "Applicants must meet the following requirements:")
    c.drawString(70, 660, "- Minimum age of 21 years")
    c.drawString(70, 640, "- Minimum monthly income of Rs 25000")
    c.drawString(70, 620, "- Credit score of 700 or above")
    c.drawString(70, 600, "- Minimum 2 years of employment history")
    
    c.drawString(50, 560, "3. LOAN LIMITS")
    c.drawString(50, 540, "Personal loans: Maximum Rs 10 lakhs")
    c.drawString(50, 520, "Home loans: Maximum Rs 50 lakhs")
    c.drawString(50, 500, "Vehicle loans: Maximum Rs 15 lakhs")
    
    c.drawString(50, 460, "4. DOCUMENTATION REQUIRED")
    c.drawString(50, 440, "All applicants must submit:")
    c.drawString(70, 420, "- Government issued photo ID")
    c.drawString(70, 400, "- Last 6 months bank statements")
    c.drawString(70, 380, "- Last 3 months salary slips")
    c.drawString(70, 360, "- Address proof not older than 3 months")
    
    c.drawString(50, 320, "5. APPROVAL PROCESS")
    c.drawString(50, 300, "Applications under Rs 5 lakhs: Branch manager approval")
    c.drawString(50, 280, "Applications above Rs 5 lakhs: Regional credit committee approval")
    c.drawString(50, 260, "Processing time: 3-5 working days for standard applications")
    
    c.drawString(50, 220, "6. REJECTION CRITERIA")
    c.drawString(50, 200, "Applications will be rejected if:")
    c.drawString(70, 180, "- Credit score below 700")
    c.drawString(70, 160, "- Existing loan defaults on record")
    c.drawString(70, 140, "- Incomplete documentation")
    c.drawString(70, 120, "- Debt to income ratio exceeds 50 percent")
    
    c.save()
    print("✅ Test PDF created: docs/test_banking_policy.pdf")

create_test_pdf()
