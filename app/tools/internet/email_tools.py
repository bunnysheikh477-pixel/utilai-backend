import secrets
import time
import string


def generate_random_email(
    domain: str = "your-temp-domain.com",
    username_length: int = 10
) -> dict:
    """Generate a random temporary email address."""

    if not domain:
        return {
            "success": False,
            "error": "Email domain is required."
        }

    if username_length < 5 or username_length > 30:
        return {
            "success": False,
            "error": "Username length must be between 5 and 30."
        }

    characters = string.ascii_lowercase + string.digits

    username = "".join(
        secrets.choice(characters)
        for _ in range(username_length)
    )

    email = f"{username}@{domain}"

    return {
        "success": True,
        "email": email,
        "username": username,
        "domain": domain
    }


def generate_otp(length: int = 6, expiry_seconds: int = 300) -> dict:
    """Generate an OTP with an expiration time."""

    if length < 4 or length > 8:
        return {
            "success": False,
            "error": "OTP length must be between 4 and 8."
        }

    if expiry_seconds <= 0:
        return {
            "success": False,
            "error": "Expiry time must be greater than 0."
        }

    minimum = 10 ** (length - 1)
    maximum = (10 ** length) - 1

    otp = str(
        secrets.randbelow(maximum - minimum + 1) + minimum
    )

    expires_at = time.time() + expiry_seconds

    return {
        "success": True,
        "otp": otp,
        "expires_in": expiry_seconds,
        "expires_at": expires_at
    }


def verify_otp(
    generated_otp: str,
    user_otp: str,
    expires_at: float
) -> dict:
    """Verify OTP and check whether it has expired."""

    if not generated_otp or not user_otp:
        return {
            "success": False,
            "verified": False,
            "error": "OTP is required."
        }

    # Check expiration first
    if time.time() > expires_at:
        return {
            "success": True,
            "verified": False,
            "expired": True,
            "message": "OTP has expired. Please generate a new OTP."
        }

    # Verify OTP
    verified = secrets.compare_digest(
        str(generated_otp),
        str(user_otp)
    )

    return {
        "success": True,
        "verified": verified,
        "expired": False,
        "message": (
            "OTP verified successfully."
            if verified
            else "Invalid OTP."
        )
    }
EMAIL_TOOLS = {
    "generate-random-email": generate_random_email,
    "generate-otp": generate_otp,
    "verify-otp": verify_otp,
}