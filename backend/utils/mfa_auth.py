import pyotp


def pyotp_verify(code: str, secret: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(str(code).strip(), valid_window=1)
