import os

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration
# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
MAIL_FROM = os.getenv("MAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_USER = os.getenv("SMTP_USER", "apikey" if "sendgrid" in SMTP_SERVER.lower() else MAIL_FROM)

# Branding
APP_NAME = "Luxenext"
BRAND_COLOR = "#D4AF37"  # Gold
BG_COLOR = "#1a1a1a"     # Dark Background
TEXT_COLOR = "#ffffff"   # White Text

import smtplib
import asyncio
from concurrent.futures import ThreadPoolExecutor

# ... imports ...

executor = ThreadPoolExecutor()

def send_sync_email(to_email: str, subject: str, html_content: str):
    if not EMAIL_PASSWORD:
        print("⚠️  [DEV MODE] Email skipped. Missing EMAIL_PASSWORD.")
        return

    message = EmailMessage()
    message["From"] = f"{APP_NAME} <{MAIL_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    try:
        print(f"🔄 Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
        # Use SMTP_SSL for port 465 (Implicit SSL)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.login(SMTP_USER, EMAIL_PASSWORD)
                server.send_message(message)
        else:
            # Use SMTP + starttls for port 587
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(SMTP_USER, EMAIL_PASSWORD)
                server.send_message(message)
        
        print(f"📧 Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        import traceback
        traceback.print_exc()
        # raise e  <-- suppressed to prevent background task crash on Render

async def send_email_smtp(to_email: str, subject: str, html_content: str):
    """
    Helper function to send email using Gmail SMTP (runs in thread to avoid blocking)
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, send_sync_email, to_email, subject, html_content)

def get_base_template(content: str) -> str:
    """
    Wraps content in a premium LuxeNext HTML template
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{APP_NAME}</title>
    </head>
    <body style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: {BG_COLOR}; color: {TEXT_COLOR}; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background: #2d2d2d; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            
            <!-- Header -->
            <div style="background-color: #000000; padding: 20px; text-align: center; border-bottom: 2px solid {BRAND_COLOR};">
                <h1 style="color: {BRAND_COLOR}; margin: 0; font-size: 24px; letter-spacing: 2px; text-transform: uppercase;">{APP_NAME}</h1>
            </div>

            <!-- Content -->
            <div style="padding: 40px 30px; line-height: 1.6;">
                {content}
            </div>

            <!-- Footer -->
            <div style="background-color: #1f1f1f; padding: 20px; text-align: center; font-size: 12px; color: #888;">
                <p style="margin: 0;">&copy; {os.getenv('YEAR', '2024')} {APP_NAME}. All rights reserved.</p>
                <p style="margin: 5px 0;">Elevating your lifestyle, one click at a time.</p>
            </div>
        </div>
    </body>
    </html>
    """

async def send_verification_email(email_to: str, code: str, subject: str):
    body = f"""
        <h2 style="color: {BRAND_COLOR}; margin-top: 0;">Verify Your Account</h2>
        <p>Welcome to <b>{APP_NAME}</b>. We are delighted to have you.</p>
        <p>Please use the verification code below to complete your registration:</p>

        <div style="background-color: #3d3d3d; color: {BRAND_COLOR}; 
            padding: 15px; letter-spacing: 8px; font-size: 32px; border-radius: 4px; 
            font-weight: bold; margin: 30px 0; text-align: center; border: 1px solid {BRAND_COLOR};">
            {code}
        </div>

        <p style="font-size: 14px; color: #aaa;">This code will expire in 2 minutes.</p>
    """
    
    html_content = get_base_template(body)

    try:
        await send_email_smtp(email_to, subject, html_content)
    except Exception as e:
        print(f"⚠️  [DEV MODE] Email failed. Verification Code for {email_to}: {code}")
        pass

async def send_order_email(email_to: str, subject: str, order: dict):
    # ✅ Format order items into HTML rows
    items_html = ""
    for item in order.get("items", []):
        product_name = item.get("name", "Unknown Product")
        items_html += f"""
        <tr style="border-bottom: 1px solid #444;">
            <td style="padding: 12px 0;">{product_name}</td>
            <td style="text-align:center; color: #ccc;">{item.get("quantity", 0)}</td>
            <td style="text-align:right; color: {BRAND_COLOR};">${item.get("price", 0):.2f}</td>
        </tr>
        """

    # ✅ Format address
    address_html = ""
    if order.get("address"):
        addr = order["address"]
        address_html = f"""
        <div style="background: #333; padding: 15px; border-radius: 4px; margin-top: 20px;">
            <p style="margin: 0; color: #aaa; font-size: 12px; text-transform: uppercase;">Shipping Address</p>
            <p style="margin: 5px 0 0 0;">
                {addr.get("street", "")}<br/>
                {addr.get("city", "")}, {addr.get("state", "")}<br/>
                {addr.get("country", "")} - {addr.get("postal_code", "")}
            </p>
        </div>
        """

    body = f"""
        <h2 style="color: {BRAND_COLOR}; margin-top: 0;">{subject}</h2>
        <p>Thank you for your order. Here are the details:</p>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid #444; padding-bottom: 10px;">
            <span>Order Ref: <b style="color: white;">{order.get("order_reference")}</b></span>
            <span>Status: <b style="color: {BRAND_COLOR};">{order.get("status", "").capitalize()}</b></span>
        </div>

        <table style="width:100%; border-collapse: collapse; margin-top:15px; color: #eee;">
            <thead>
                <tr style="border-bottom: 2px solid {BRAND_COLOR}; text-align: left;">
                    <th style="padding-bottom: 10px;">Product</th>
                    <th style="padding-bottom: 10px; text-align: center;">Qty</th>
                    <th style="padding-bottom: 10px; text-align: right;">Price</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div style="margin-top: 20px; text-align: right;">
            <p style="font-size: 18px; margin: 0;">Total: <b style="color: {BRAND_COLOR};">${order.get("total_amount", 0):.2f}</b></p>
        </div>

        {address_html}

        <p style="margin-top: 30px; text-align: center; color: #888;">We will notify you once your order ships.</p>
    """

    html_content = get_base_template(body)
    await send_email_smtp(email_to, subject, html_content)


async def send_payment_received(email_to: str, order_ref: str, amount: float):
    subject = f"Payment Confirmed - Order #{order_ref}"
    link = f"https://luxenext-f.vercel.app//orders/{order_ref}"
    
    body = f"""
        <h2 style="color: {BRAND_COLOR}; text-align: center;">Payment Successful</h2>
        <p style="text-align: center; font-size: 18px;">We have received your payment of <b style="color: {BRAND_COLOR};">₦{amount:.2f}</b>.</p>
        
        <p style="text-align: center;">Your order <b>{order_ref}</b> is now being processed.</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="padding: 12px 30px; background: {BRAND_COLOR}; color: #000; 
                text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                Track My Order
            </a>
        </div>
    """
    
    html_content = get_base_template(body)
    await send_email_smtp(email_to, subject, html_content)


async def send_payment_rejected(email_to: str, order_ref: str, reason: str):
    subject = f"Payment Issue - Order {order_ref}"
    body = f"""
        <h2 style="color: #ff4444; text-align: center;">Payment Rejected</h2>
        <p>We could not confirm your payment for order <b>{order_ref}</b>.</p>
        
        <div style="background: #330000; border: 1px solid #ff4444; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="margin: 0; color: #ffcccc;"><b>Reason:</b> {reason}</p>
        </div>

        <p>Please try again or contact our support team.</p>
    """
    html_content = get_base_template(body)
    await send_email_smtp(email_to, subject, html_content)


async def send_shipping_update(email_to: str, order_ref: str, status: str, tracking_link: str = None):
    subject = f"Order Update - {order_ref}"
    tracking_html = f'''
        <div style="text-align: center; margin: 30px 0;">
            <a href="{tracking_link}" style="padding: 12px 30px; background: {BRAND_COLOR}; color: #000; 
                text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                Track Package
            </a>
        </div>
    ''' if tracking_link else ""

    body = f"""
        <h2 style="color: {BRAND_COLOR};">Order Update</h2>
        <p>Your order <b>{order_ref}</b> status has been updated to:</p>
        
        <h3 style="text-align: center; font-size: 24px; color: white; margin: 20px 0;">{status.capitalize()}</h3>

        {tracking_html}
    """
    html_content = get_base_template(body)
    await send_email_smtp(email_to, subject, html_content)


async def send_reset_email(email_to: str, link: str):
    subject = "Reset Your Password"
    body = f"""
        <h2 style="color: {BRAND_COLOR};">Password Reset</h2>
        <p>You requested to reset your password. Click the button below to proceed:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{link}" style="padding: 12px 30px; background: {BRAND_COLOR}; color: #000; 
                text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                Reset Password
            </a>
        </div>

        <p style="font-size: 14px; color: #aaa;">If you didn't request this, please ignore this email.</p>
    """
    html_content = get_base_template(body)
    await send_email_smtp(email_to, subject, html_content)
