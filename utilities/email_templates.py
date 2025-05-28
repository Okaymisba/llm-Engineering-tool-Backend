def create_login_opt_msg(username, otp):
    return f"""Hello {username},

Thank you for registering with MSW LLM!

To complete your registration, please use the One-Time Password (OTP) below. This code is valid for the next 5 minutes and can only be used once.

🔐 Your OTP: **{otp}**

If you did not initiate this request, please ignore this email.

Need help? Contact our support team at [support@yourcompany.com].

Best regards,  
The OpenRouter Team  
www.yourcompany.com
"""

successful_transaction = """Hi {user_name or email},

Thank you for your payment of ${amount}. We’re happy to let you know that your account has been successfully credited.

🧮 New Balance: ${new_credit_balance}

You can now use your credits to access our API services as usual.

If you have any questions or need help, feel free to reply to this email.

Thanks again for choosing OpenRouter!

Best regards,  
The OpenRouter Team
"""

transaction_failure = """Hi ${user_name or email},

Unfortunately, your recent payment attempt for ${amount} was not successful.

Possible reasons may include:
- Card declined
- Insufficient funds
- Invalid card details
- Authentication failure (e.g., 3D Secure)

Please try again using the link below:
[Retry Payment](https://yourdomain.com/retry-checkout?session={{session_id}})

If the issue persists or you need assistance, feel free to contact our support team.

We’re here to help!

Sincerely,  
The OpenRouter Support Team
"""