import asyncio
from email_utilis import send_email_smtp, get_base_template

async def send_test_email():
    print("Testing LuxeNext Branded Email...")
    
    body = """
        <h2 style="color: #D4AF37; margin-top: 0;">Branding Test</h2>
        <p>This is a test email to verify the new <b>LuxeNext</b> branding.</p>
        <p>You should see:</p>
        <ul>
            <li>Sender: LuxeNext</li>
            <li>Dark Mode Theme</li>
            <li>Gold Accents</li>
        </ul>
        <div style="text-align: center; margin: 30px 0;">
            <a href="#" style="padding: 12px 30px; background: #D4AF37; color: #000; 
                text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                Call to Action
            </a>
        </div>
    """
    
    html_content = get_base_template(body)
    
    # We need to fetch the TO email from env or just use a hardcoded one for testing
    import os
    from dotenv import load_dotenv
    load_dotenv()
    to_email = os.getenv("MAIL_FROM")

    if not to_email:
        print("❌ Error: MAIL_FROM not set in .env")
        return

    try:
        await send_email_smtp(to_email, "LuxeNext Branding Test", html_content)
        print(f"✅ Success! Branded email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    asyncio.run(send_test_email())
