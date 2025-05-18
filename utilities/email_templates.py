from email_service import generate_OTP

def create_login_opt_msg(username, otp):
    return f"""Hello {username},

Thank you for registering with MSW LLM!

To complete your registration, please use the One-Time Password (OTP) below. This code is valid for the next 5 minutes and can only be used once.

🔐 Your OTP: **{otp}**

If you did not initiate this request, please ignore this email.

Need help? Contact our support team at [support@yourcompany.com].

Best regards,  
[Your Company Name] Team  
www.yourcompany.com
"""