"""
Authentication Service
Handles Audible authentication and token management for web interface
"""

import os
import json
import mysql.connector
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from audible import Authenticator, Client
from utils.crypto_utils_simple import get_crypto_instance
from utils.db.connection import get_db_connection


class AuthService:
    def __init__(self):
        self.crypto = get_crypto_instance()
    
    async def authenticate_user(self, user_id: int, username: str, password: str, 
                              marketplace: str, otp_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Authenticate user with Audible and store tokens
        
        Returns:
            {
                'success': bool,
                'message': str,
                'requires_otp': bool,
                'tokens_stored': bool
            }
        """
        try:
            # Create the authenticator
            auth_kwargs = {
                'username': username,
                'password': password,
                'locale': marketplace
            }
            
            # If OTP code is provided, create callbacks that return it
            # The audible library may ask for either OTP or CVF codes
            if otp_code:
                def otp_callback():
                    return otp_code
                def cvf_callback():
                    return otp_code
                auth_kwargs['otp_callback'] = otp_callback
                auth_kwargs['cvf_callback'] = cvf_callback
            
            auth = Authenticator.from_login(**auth_kwargs)
            
            # Test the authentication
            client = Client(auth=auth)
            
            # Store tokens in database
            success = await self._store_tokens(user_id, auth, marketplace)
            
            if success:
                return {
                    'success': True,
                    'message': 'Authentication successful',
                    'requires_otp': False,
                    'tokens_stored': True
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to store authentication tokens',
                    'requires_otp': False,
                    'tokens_stored': False
                }
                
        except Exception as e:
            error_msg = str(e)
            
            # Check if OTP/CVF is required - common patterns that indicate 2FA needed
            otp_indicators = [
                "OTP",
                "CVF",  # Customer Verification Form
                "captcha",
                "EOF when reading a line",  # This is the key one - happens when Audible expects OTP input
                "two-factor",
                "verification code",
                "authentication code"
            ]
            
            if any(indicator in error_msg for indicator in otp_indicators):
                return {
                    'success': False,
                    'message': 'Two-factor authentication required',
                    'requires_otp': True,
                    'tokens_stored': False
                }
            else:
                return {
                    'success': False,
                    'message': f'Authentication failed: {error_msg}',
                    'requires_otp': False,
                    'tokens_stored': False
                }
    
    async def _store_tokens(self, user_id: int, auth: Authenticator, marketplace: str) -> bool:
        """Store encrypted authentication tokens in database"""
        try:
            # Extract complete authentication data
            auth_data = {
                'website_cookies': self._make_json_safe(auth.website_cookies),
                'adp_token': auth.adp_token,
                'access_token': auth.access_token,
                'refresh_token': auth.refresh_token,
                'device_private_key': auth.device_private_key,
                'store_authentication_cookie': self._make_json_safe(auth.store_authentication_cookie),
                'device_info': self._make_json_safe(auth.device_info),
                'customer_info': self._make_json_safe(auth.customer_info),
                'expires': auth.expires,
                'locale_code': marketplace,
                'with_username': getattr(auth, 'with_username', False),
                'activation_bytes': getattr(auth, 'activation_bytes', None)
            }
            
            # Encrypt the authentication data
            auth_json = json.dumps(auth_data)
            encrypted_data = self.crypto.encrypt_for_user(user_id, auth_json)
            
            # Store in database
            with get_db_connection() as db:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO user_audible_accounts 
                    (user_id, encrypted_auth_data, marketplace, tokens_expires_at, sync_status)
                    VALUES (%s, %s, %s, %s, 'pending')
                    ON DUPLICATE KEY UPDATE
                    encrypted_auth_data = VALUES(encrypted_auth_data),
                    tokens_expires_at = VALUES(tokens_expires_at),
                    sync_status = 'pending',
                    updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    encrypted_data,
                    marketplace,
                    self._format_expires_date(auth_data.get('expires'))
                ))
                cursor.close()
            
            return True
            
        except Exception as e:
            print(f"Failed to store tokens: {e}")
            return False
    
    async def get_audible_client(self, user_id: int) -> Optional[Client]:
        """Get authenticated Audible client for user"""
        try:
            with get_db_connection() as db:
                cursor = db.cursor()
                cursor.execute("""
                    SELECT encrypted_auth_data FROM user_audible_accounts 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                cursor.close()
                
                if not result:
                    return None
                
                # Decrypt and recreate authenticator
                encrypted_data = result[0]
                decrypted_json = self.crypto.decrypt_for_user(user_id, encrypted_data)
                auth_data = json.loads(decrypted_json)
                
                auth = Authenticator.from_dict(auth_data)
                
                # Check if tokens need refresh
                expires_timestamp = auth_data.get('expires')
                if expires_timestamp and datetime.now().timestamp() > expires_timestamp:
                    try:
                        auth.refresh_access_token()
                    except Exception:
                        pass  # Continue with existing tokens
                
                return Client(auth=auth)
                
        except Exception as e:
            print(f"Failed to get Audible client: {e}")
            return None
    
    async def test_api_access(self, user_id: int) -> Dict[str, Any]:
        """Test API access for user"""
        client = await self.get_audible_client(user_id)
        
        if not client:
            return {
                'success': False,
                'message': 'No authentication tokens found'
            }
        
        try:
            library_test = client.get(
                "1.0/library",
                num_results=1,
                response_groups="product_desc"
            )
            
            if library_test:
                total_size = library_test.get('total_size', 0)
                return {
                    'success': True,
                    'message': f'API access confirmed! Library has {total_size} books'
                }
            else:
                return {
                    'success': False,
                    'message': 'API access test failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'API access test failed: {str(e)}'
            }
    
    def _make_json_safe(self, obj):
        """Convert object to JSON-safe format"""
        if obj is None:
            return None
        
        if isinstance(obj, (str, int, float, bool, list, dict)):
            return obj
        
        if hasattr(obj, '__dict__'):
            try:
                return obj.__dict__
            except:
                pass
        
        if hasattr(obj, 'to_dict'):
            try:
                return obj.to_dict()
            except:
                pass
        
        return str(obj)
    
    def _format_expires_date(self, expires):
        """Format expiration date to ISO string"""
        if expires is None:
            return None
        
        if isinstance(expires, str):
            return expires
        
        if hasattr(expires, 'isoformat'):
            return expires.isoformat()
        
        if isinstance(expires, (int, float)):
            try:
                dt = datetime.fromtimestamp(expires)
                return dt.isoformat()
            except (ValueError, OSError):
                return None
        
        return str(expires) 