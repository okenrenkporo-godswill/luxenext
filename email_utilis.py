import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from models import Order



SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM")


async def send_verification_email(email_to: str, link: str, subject: str):
    html_content = f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{subject}</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color:#f9f9f9; padding:40px; color:#333;">
        <div style="max-width:600px; margin:auto; background:white; border-radius:10px; padding:30px; box-shadow:0 4px 8px rgba(0,0,0,0.05); text-align:center;">
            <h2 style="color:#007bff;">Verify Your LuxeNext Account</h2>
            <p style="font-size:16px;">Thank you for signing up! Click the button below to verify your email:</p>
            <a href="{link}" target="_blank" 
                style="display:inline-block; margin-top:20px; padding:12px 24px; background:#007bff; color:#fff; text-decoration:none; border-radius:5px; font-weight:bold;">
                ✅ Verify My Account
            </a>
            <p style="margin-top:30px; font-size:14px; color:#666;">If the button doesn’t work, copy and paste this link into your browser:</p>
            <p><a href="{link}" style="color:#007bff;">{link}</a></p>
            <p style="margin-top:20px; color:#999;">This link expires in 10 minutes.</p>
        </div>
    </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=email_to,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 Verification email sent to {email_to} ({response.status_code})")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise

    

def send_order_email(email_to: str, subject: str, order: dict):
    """
    Send an order confirmation or status update email
    """

    # ✅ Format order items into HTML rows
    items_html = ""
    for item in order.get("items", []):
        product_name = item.get("name", "Unknown Product")
        items_html += f"""
        <tr>
            <td>{product_name}</td>
            <td style="text-align:center;">{item.get("quantity", 0)}</td>
            <td style="text-align:right;">${item.get("price", 0):.2f}</td>
        </tr>
        """

    # ✅ Format address (if available)
    address_html = ""
    if order.get("address"):
        addr = order["address"]
        address_html = f"""
        <p><b>Shipping Address:</b><br/>
        {addr.get("street", "")}<br/>
        {addr.get("city", "")}, {addr.get("state", "")}<br/>
        {addr.get("country", "")} - {addr.get("postal_code", "")}
        </p>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>{subject}</h2>
        <p>Hello,</p>
        <p>Thank you for shopping with us. Here are the details of your order:</p>
        
        <p><b>Order Reference:</b> {order.get("order_reference")}</p>
        <p><b>Status:</b> {order.get("status", "").capitalize()}</p>

        <table style="width:100%; border-collapse: collapse; margin-top:15px;" border="1" cellpadding="8">
            <thead style="background:#f2f2f2;">
                <tr>
                    <th>Product</th>
                    <th>Qty</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <p style="margin-top:15px;"><b>Total Amount:</b> ${order.get("total_amount", 0):.2f}</p>
        <p><b>Payment Status:</b> {order.get("payment_status", "").capitalize()}</p>

        {address_html}

        <p style="margin-top:20px;">We’ll notify you once your order status changes.</p>
        <p>Best regards,<br/>Your E-commerce Team</p>
    </body>
    </html>
    """

    message = Mail(
        from_email=MAIL_FROM,
        to_emails=email_to,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 Email sent to {email_to}, Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise



# 🔹 Payment Confirmed Email
async def send_payment_received(email_to: str, order_ref: str, amount: float):
    subject = f"Payment Confirmed for Order #{order_ref}"
    link = f"https://luxenext-f.vercel.app//orders/{order_ref}"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>💰 Payment Confirmed</h2>
        <p>Your payment of <b>₦{amount:.2f}</b> for order <b>{order_ref}</b> has been confirmed.</p>
        <p>We are now processing your order and will notify you once it ships.</p>
        <p>
            <a href="{link}" style="padding:10px 15px; background:#2196F3; color:#fff; text-decoration:none; border-radius:5px;">
                Track My Order
            </a>
        </p>
        <p style="margin-top:20px;">Thank you for shopping with us! 🛒</p>
    </body>
    </html>
    """
    
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=email_to,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 Payment email sent to {email_to}, Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send payment email: {e}")
        raise


async def send_payment_rejected(email_to: str, order_ref: str, reason: str):
    subject = f"Payment Rejected - Order {order_ref}"
    html_content = f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>❌ Payment Rejected</h2>
        <p>Your payment for order <b>{order_ref}</b> could not be confirmed.</p>
        <p><b>Reason:</b> {reason}</p>
        <p>Please retry payment or contact support.</p>
    </body>
    </html>
    """
    message = Mail(from_email=MAIL_FROM, to_emails=email_to, subject=subject, html_content=html_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"❌ Failed to send rejection email: {e}")
        raise

async def send_payment_received(email_to: str, order_ref: str, amount: float):
    subject = f"Payment Confirmed - Order {order_ref}"
    html_content = f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>💰 Payment Successful</h2>
        <p>Your payment of <b>₦{amount:.2f}</b> for order <b>{order_ref}</b> has been confirmed.</p>
        <p>Your order is now <b>processing</b>. We’ll notify you when it ships.</p>
        <p style="margin-top:20px;">Thank you for shopping with BuyPoint!</p>
    </body>
    </html>
    """
    message = Mail(from_email=MAIL_FROM, to_emails=email_to, subject=subject, html_content=html_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"❌ Failed to send payment email: {e}")
        raise


async def send_shipping_update(email_to: str, order_ref: str, status: str, tracking_link: str = None):
    subject = f"Order Update - {order_ref}"
    tracking_html = f'<p>Track here: <a href="{tracking_link}">📦 Track Order</a></p>' if tracking_link else ""
    html_content = f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>🚚 Order Update</h2>
        <p>Your order <b>{order_ref}</b> status has been updated to: <b>{status.capitalize()}</b></p>
        {tracking_html}
        <p>We’ll notify you of the next update.</p>
    </body>
    </html>
    """
    message = Mail(from_email=MAIL_FROM, to_emails=email_to, subject=subject, html_content=html_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        print(f"❌ Failed to send shipping email: {e}")
        raise


async def send_reset_email(email_to: str, link: str):
    subject = "🔑 Reset Your Password"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>You requested to reset your password. Click the button below to reset it:</p>
        <p>
            <a href="{link}" style="padding:10px 20px; background:#FF5722; color:#fff; 
            text-decoration:none; border-radius:5px;">Reset Password</a>
        </p>
        <p>If you didn’t request this, please ignore this email.</p>
        <p>This link will expire in 15 minutes.</p>
    </body>
    </html>
    """
    message = Mail(from_email=MAIL_FROM, to_emails=email_to, subject=subject, html_content=html_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"📧 Password reset email sent to {email_to}, Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        raise
