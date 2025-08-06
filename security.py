import bcrypt
import pyotp
from twilio.rest import Client

def hash_password(password):
    # Hash the password with a salt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def send_otp(email):
    # Generate OTP using pyotp
    totp = pyotp.TOTP('base32secret3232')
    otp = totp.now()
    
    # Send OTP via email (use Twilio/SendGrid for real implementation)
    client = Client()
    client.messages.create(
        to=email,
        from_="your_twilio_number",
        body=f"Your OTP is: {otp}"
    )
    return otp

def verify_otp(input_otp, otp):
    return input_otp == otp
