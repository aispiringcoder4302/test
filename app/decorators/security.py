from fastapi import Request, HTTPException
from functools import wraps
import hashlib
import hmac

def validate_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode("latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def signature_required(func):
    async def decorated_function(request: Request, *args, **kwargs):
        secret = request.app.state.config.get("APP_SECRET")
        if not secret:
            raise HTTPException(status_code=500, detail="App secret not configured.")
        # Your signature verification logic here
        return await func(request, *args, **kwargs)
    return decorated_function

