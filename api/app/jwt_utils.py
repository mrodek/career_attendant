"""
JWT utilities for validating Clerk tokens
"""

import logging
import json
import jwt
from jwt.algorithms import RSAAlgorithm
import httpx
from typing import Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)

# Cache JWKS keys to avoid repeated requests
_jwks_cache: Optional[Dict[str, Any]] = None

async def get_jwks_keys(force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Get JWKS keys from Clerk"""
    global _jwks_cache
    
    if _jwks_cache and not force_refresh:
        return _jwks_cache
    
    try:
        jwks_url = "https://apparent-javelin-61.clerk.accounts.dev/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS keys: {e}")
        return None

async def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate a Clerk JWT token and return the payload"""
    try:
        # Get JWKS from Clerk
        jwks = await get_jwks_keys()
        
        if not jwks:
            raise ValueError("Unable to fetch JWKS keys")
        
        # Get unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise ValueError("Token missing key ID")
        
        # Find the matching key
        jwk = next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)
        
        if not jwk:
            raise ValueError("Unable to find matching public key")
        
        # Convert JWK to RSA public key
        public_key = RSAAlgorithm.from_jwk(json.dumps(jwk))
        
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Clerk tokens have flexible audience
        )
        
        return payload
        
    except Exception as e:
        logger.error(f"JWT validation failed: {e}")
        raise
