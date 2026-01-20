"""
Quick test script to verify SendGrid SMTP connection with Port 2525
Run this to test if emails can be sent successfully
"""
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.sendgrid.net"
SMTP_PORT = 2525
SMTP_USER = "apikey"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM", "igwedejethro@gmail.com")

def test_email_connection():
    """Test SMTP connection and send a test email"""
    
    if not EMAIL_PASSWORD:
        print("❌ EMAIL_PASSWORD not found in .env file")
        return False
    
    print(f"🔄 Testing connection to {SMTP_SERVER}:{SMTP_PORT}...")
    
    try:
        # Create test message
        message = EmailMessage()
        message["From"] = f"Luxenext <{MAIL_FROM}>"
        message["To"] = MAIL_FROM  # Send to yourself for testing
        message["Subject"] = "Test Email - Port 2525"
        message.set_content("""
        <h2>Email Test Successful! ✅</h2>
        <p>Your SendGrid SMTP configuration is working correctly with Port 2525.</p>
        <p>This confirms that:</p>
        <ul>
            <li>SMTP Server: smtp.sendgrid.net</li>
            <li>Port: 2525</li>
            <li>Authentication: Working</li>
        </ul>
        """, subtype="html")
        
        # Connect and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            print("✅ Connected to SMTP server")
            server.starttls()
            print("✅ TLS encryption enabled")
            server.login(SMTP_USER, EMAIL_PASSWORD)
            print("✅ Authentication successful")
            server.send_message(message)
            print(f"✅ Test email sent to {MAIL_FROM}")
            
        print("\n🎉 SUCCESS! Email configuration is working perfectly.")
        print(f"📧 Check your inbox at {MAIL_FROM}")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_email_connection()
