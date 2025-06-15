from typing import Optional

from fastapi import Header, HTTPException

from services.supabase_client import decode_jwt_token


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extracts and verifies the current user from the authorization header. The function
    expects a Bearer token scheme for authorization and decodes the provided JWT token
    to extract user details. If the token is invalid, missing, or improperly formatted,
    an HTTPException is raised.

    :param authorization: The 'Authorization' header containing the Bearer token.
                          Defaults to None if not provided.
    :type authorization: Optional[str]
    :return: A dictionary containing user details, including 'id', 'email', and
             optional 'metadata'.
    :rtype: dict
    :raises HTTPException: Raised with a 401 status code if the authorization header
                           is missing, the authentication scheme is invalid, the
                           token decoding fails, or the token payload is invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )

        decoded_token = decode_jwt_token(token)

        if not decoded_token.get('sub'):
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )

        return {
            "id": decoded_token.get('sub'),
            "email": decoded_token.get('email'),
            "metadata": decoded_token.get('user_metadata', {})
        }

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )
