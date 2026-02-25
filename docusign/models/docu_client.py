from odoo.exceptions import ValidationError
from odoo import _
import logging
import requests
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from docusign_esign import Signer, Tabs, SignHere

_logger = logging.getLogger(__name__)

headers = {'Accept': 'application/json',
           'Content-Type': 'application/json'
           }
baseUrl = 'https://demo.docusign.net/restapi/v2.1/accounts/'


def _mask_email_for_environment(config, email):
    """
    When running in demo/sandbox, route all DocuSign recipient emails to the configured
    test inbox to avoid sending to real users.
    """
    if config.get('environment') == 'demo':
        test_email = config.get('test_email')
        if test_email:
            _logger.info("[DocuSign API] Using sandbox test email override: %s (original: %s)", test_email, email)
            return test_email
        _logger.warning("[DocuSign API] Demo environment active but no test email configured; using actual email %s", email)
    return email


def _get_docusign_config(env):
    """
    Retrieve DocuSign configuration from system parameters based on selected environment.
    Returns dict with base_uri, account_id, integration_key, secret_key.
    Falls back to user-based authentication if settings not configured.
    """
    _logger.debug("Fetching DocuSign configuration from system parameters")
    IrConfigParameter = env['ir.config_parameter'].sudo()
    
    # Get selected environment (production or demo)
    environment = IrConfigParameter.get_param('docusign.environment', 'demo')
    _logger.debug("DocuSign environment: %s", environment)
    
    # Read environment-specific parameters
    prefix = 'prod' if environment == 'production' else 'demo'
    base_uri = IrConfigParameter.get_param(f'docusign.{prefix}_base_uri')
    account_id = IrConfigParameter.get_param(f'docusign.{prefix}_account_id')
    user_guid = IrConfigParameter.get_param(f'docusign.{prefix}_user_guid')
    integration_key = IrConfigParameter.get_param(f'docusign.{prefix}_integration_key')
    secret_key = IrConfigParameter.get_param(f'docusign.{prefix}_secret_key')
    test_email = IrConfigParameter.get_param('docusign.demo_test_email') if environment == 'demo' else None
    
    if not base_uri or not account_id:
        _logger.warning("DocuSign settings not configured. Please configure in Settings -> DocuSign Settings")
        raise ValidationError(_("DocuSign is not configured. Please configure credentials in Settings -> DocuSign Settings"))
    
    _logger.debug("DocuSign config loaded: base_uri=%s, account_id=%s, has_user_guid=%s, has_integration_key=%s", 
                  base_uri, account_id[:10] + '...' if account_id else None, bool(user_guid), bool(integration_key))
    
    return {
        'base_uri': base_uri,
        'account_id': account_id,
        'user_guid': user_guid,
        'integration_key': integration_key,
        'secret_key': secret_key,
        'environment': environment,
        'test_email': test_email
    }


def _get_cached_access_token(env, user):
    """
    Get access token with request-level caching and automatic JWT generation fallback.
    
    Tries to use user's OAuth token first, but falls back to JWT authentication
    if OAuth token is not available or expired and cannot be refreshed.
    
    Args:
        env: Odoo environment
        user: res.users record
        
    Returns:
        str: Valid access token
    """
    # Check if JWT is configured - if so, use it directly (more reliable)
    IrConfigParameter = env['ir.config_parameter'].sudo()
    config = _get_docusign_config(env)
    prefix = 'demo' if config['environment'] == 'demo' else 'prod'
    private_key_pem = IrConfigParameter.get_param(f'docusign.{prefix}_private_key')
    
    if private_key_pem:
        # JWT is configured - use it directly (no OAuth needed)
        _logger.info("Using JWT authentication for user %s", user.login)
        return _generate_jwt_access_token(env)
    
    # Fall back to OAuth (user-based authentication) only if JWT not configured
    if hasattr(user, 'get_valid_access_token') and user.access_token:
        try:
            return user.get_valid_access_token()
        except Exception as e:
            _logger.error("OAuth token refresh failed for user %s: %s. JWT not configured. Please configure JWT or refresh OAuth.", user.login, str(e))
            raise
    
    # No authentication method available
    _logger.error("No authentication configured for user %s. Please configure JWT (recommended) or OAuth.", user.login)
    raise ValidationError(_("DocuSign authentication not configured. Please contact administrator."))


def _generate_jwt_access_token(env):
    """
    Generate DocuSign access token using JWT authentication.
    This method doesn't require user interaction - it uses a private key
    to generate tokens automatically.
    
    Returns:
        str: Valid JWT access token
    """
    try:
        # Import JWT library (should be available in Python 3)
        try:
            import jwt
        except ImportError:
            _logger.error("PyJWT library not installed. Install with: pip install PyJWT cryptography")
            raise ValidationError(_("JWT authentication requires PyJWT library. Please contact administrator."))
        
        config = _get_docusign_config(env)
        
        # Check if JWT is configured
        if not config.get('integration_key') or not config.get('secret_key'):
            _logger.error("JWT not configured. Please set integration_key and secret_key in DocuSign Settings")
            raise ValidationError(_("DocuSign JWT authentication not configured. Please configure in Settings → DocuSign Settings"))
        
        # Get or create cached token
        IrConfigParameter = env['ir.config_parameter'].sudo()
        cached_token = IrConfigParameter.get_param('docusign.jwt_cached_token')
        cached_expiry = IrConfigParameter.get_param('docusign.jwt_cached_expiry')
        
        # Check if cached token is still valid
        if cached_token and cached_expiry:
            try:
                expiry_dt = datetime.fromisoformat(cached_expiry)
                if expiry_dt > datetime.now() + timedelta(minutes=5):
                    _logger.debug("Using cached JWT token (expires at %s)", cached_expiry)
                    return cached_token
            except:
                pass
        
        # Generate new JWT token
        _logger.info("Generating new JWT token for DocuSign")
        
        # Get RSA private key from config
        IrConfigParameter = env['ir.config_parameter'].sudo()
        prefix = 'demo' if config['environment'] == 'demo' else 'prod'
        private_key_pem = IrConfigParameter.get_param(f'docusign.{prefix}_private_key')
        
        if not private_key_pem:
            _logger.warning("No RSA private key configured for JWT. Using client_secret as fallback (not recommended for production)")
            # Fallback to HS256 with client_secret (not recommended)
            payload = {
                'iss': config['integration_key'],
                'sub': config['user_guid'] or config['account_id'],  # Prefer user_guid, fallback to account_id
                'aud': 'account-d.docusign.com' if config['environment'] == 'demo' else 'account.docusign.com',
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600,
                'scope': 'signature impersonation'
            }
            token = jwt.encode(payload, config['secret_key'], algorithm='HS256')
        else:
            # Use RS256 with RSA private key (recommended)
            now = int(time.time())
            payload = {
                'iss': config['integration_key'],  # Integration key (Client ID)
                'sub': config['user_guid'] or config['account_id'],       # Prefer user_guid, fallback to account_id
                'aud': 'account-d.docusign.com' if config['environment'] == 'demo' else 'account.docusign.com',
                'iat': now,                        # Issued at
                'exp': now + 3600,                 # Expires in 1 hour
                'scope': 'signature impersonation'
            }
            
            # Load private key and sign JWT
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.backends import default_backend
                
                # Parse PEM key
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(),
                    password=None,
                    backend=default_backend()
                )
                token = jwt.encode(payload, private_key, algorithm='RS256')
            except ImportError:
                _logger.error("cryptography library not installed. Install with: pip install cryptography")
                raise ValidationError(_("JWT authentication requires cryptography library. Please contact administrator."))
            except Exception as e:
                _logger.error("Failed to load RSA private key: %s", str(e))
                raise ValidationError(_("Invalid RSA private key configured. Please check DocuSign Settings."))
        
        # Exchange JWT for access token
        oauth_base = 'https://account-d.docusign.com' if config['environment'] == 'demo' else 'https://account.docusign.com'
        url = f"{oauth_base}/oauth/token"
        
        data = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': token
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            
            # Cache the token
            expiry_time = datetime.now() + timedelta(seconds=expires_in)
            IrConfigParameter.set_param('docusign.jwt_cached_token', access_token)
            IrConfigParameter.set_param('docusign.jwt_cached_expiry', expiry_time.isoformat())
            
            _logger.info("Successfully generated JWT access token (expires at %s)", expiry_time)
            return access_token
        else:
            _logger.error("JWT token exchange failed: status=%s, response=%s", response.status_code, response.text)
            raise ValidationError(_("Failed to generate JWT token: {}").format(response.text))
            
    except Exception as e:
        _logger.exception("Error generating JWT access token")
        raise ValidationError(_("JWT authentication failed: {}. Please re-authenticate or check DocuSign settings.").format(str(e)))
    
    return token


def send_docusign_envelope_multiple_signers(env, user, file_name, file_contents, signers_list, custom_fields=None):
    """
    Send a DocuSign envelope with multiple signers in sequential order.
    
    Args:
        env: Odoo environment
        user: res.users record with valid DocuSign token
        file_name: Name of the document file
        file_contents: Base64-encoded file content
        signers_list: List of DocuSign SDK Signer objects with optional 'partner' attribute
        custom_fields: Optional dict with customFields structure for DocuSign envelope
    
    Returns:
        str: Envelope ID
    """
    _logger.info("[DocuSign API] send_docusign_envelope_multiple_signers() called: file=%s, signers=%d",
                file_name, len(signers_list))
    try:
        # Get configuration from settings
        config = _get_docusign_config(env)
        _logger.info("[DocuSign API] Config loaded: environment=%s, account_id=%s",
                    config['environment'], config['account_id'][:10] + '...' if config['account_id'] else 'None')
        
        # Get cached access token (auto-refreshes if expired)
        access_token = _get_cached_access_token(env, user)
        _logger.info("[DocuSign API] Access token obtained: %s...", access_token[:20] if access_token else 'None')
        
        # Build signers array from SDK objects
        signers_array = []
        for idx, signer_obj in enumerate(signers_list):
            masked_email = _mask_email_for_environment(config, signer_obj.email)
            # Get language code from partner (first 2 characters, e.g., 'es' from 'es_419')
            language_code = 'es'  # Default to Spanish
            partner = getattr(signer_obj, 'partner', None)
            if partner and partner.lang:
                language_code = partner.lang[:2] if len(partner.lang) >= 2 else 'es'
                _logger.info("[DocuSign API] Signer %d language code: %s (from partner lang: %s)",
                            idx + 1, language_code, partner.lang)
            
            # Convert SDK Signer object to dict for JSON serialization
            signer_data = {
                "name": signer_obj.name,
                "email": masked_email,
                "recipientId": signer_obj.recipient_id,
                "routingOrder": signer_obj.routing_order,
                "deliveryMethod": signer_obj.delivery_method
            }

            # Enable embedded signing when a client_user_id is provided on the signer
            client_user_id = getattr(signer_obj, 'client_user_id', None)
            if client_user_id:
                signer_data["clientUserId"] = str(client_user_id)

            # Check if this signer should use WhatsApp delivery
            if signer_obj.delivery_method.lower() == 'whatsapp':
                signer_data["deliveryMethod"] = "WhatsApp"
                signer_data["phoneNumber"] = {
                    "countryCode": signer_obj.phone_number.country_code,
                    "number": signer_obj.phone_number.number
                }
                _logger.info("[DocuSign API] Signer %d (WhatsApp): %s (%s -> %s, +%s %s)",
                            idx + 1, signer_obj.name, signer_obj.email, signer_data["email"],
                            signer_obj.phone_number.country_code, signer_obj.phone_number.number)
            else:
                # Default to email delivery
                _logger.info("[DocuSign API] Signer %d (Email): %s (%s -> %s)",
                            idx + 1, signer_obj.name, signer_obj.email, signer_data["email"])
            
            # Add language code
            if language_code:
                signer_data["recipientLanguage"] = {
                    "languageCode": language_code
                }
            
            # Add signature tabs using anchor strings (e.g., /sn1/, /sn2/ in PDF)
            # PDF template must contain anchor strings like /sn1/, /sn2/, etc.
            anchor_string = f"/sn{idx + 1}/"
            signer_data["tabs"] = {
                "signHereTabs": [
                    {
                        "anchorString": anchor_string,
                        "anchorYOffset": "0",
                        "anchorUnits": "pixels",
                        "documentId": "1",
                        "pageNumber": "1"
                    }
                ]
            }
            
            signers_array.append(signer_data)
            _logger.info("[DocuSign API] Added signer %d: %s, routing_order=%s",
                        idx + 1, signer_obj.name, signer_data['routingOrder'])
        
        # Add company stamp image tab if configured (on first page, for last signer)
        company_stamp_base64 = env['ir.config_parameter'].sudo().get_param(
            'contract_management.docusign_company_stamp_base64'
        )
        if company_stamp_base64 and signers_array:
            # Add stamp tab to last signer's existing tabs
            if "tabs" not in signers_array[-1]:
                signers_array[-1]["tabs"] = {}
            signers_array[-1]["tabs"]["imageTabs"] = [
                {
                    "anchorString": "/st2/",
                    "anchorYOffset": "0",
                    "anchorUnits": "pixels",
                    "documentId": "1",
                    "pageNumber": "1",
                    "stampType": "stamp"
                }
            ]
            _logger.info("[DocuSign API] Company stamp tab added to last signer")
        
        envelope_data = {
            "emailSubject": "ACCION REQUERIDA: Firmar su contrato con Cabal Internet ahora",
            "documents": [
                {
                    "documentBase64": file_contents.decode("utf-8"),
                    "name": file_name,
                    "fileExtension": "pdf",
                    "documentId": "1"
                }
            ],
            "recipients": {
                "signers": signers_array
            },
            "status": "sent"
        }
        
        # Add custom fields if provided
        if custom_fields:
            envelope_data['customFields'] = custom_fields
            _logger.info("[DocuSign API] Custom fields added to envelope: %s", 
                        json.dumps(custom_fields))
        
        baseUrl = config['base_uri'] + '/restapi/v2.1/accounts/' + config['account_id']
        url = baseUrl + '/envelopes'
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Sending POST to %s environment: %s", config['environment'], url)
        _logger.info("[DocuSign API] Envelope payload: recipients=%d, documents=%d, status=%s",
                    len(envelope_data['recipients']['signers']),
                    len(envelope_data['documents']),
                    envelope_data['status'])
        
        response = requests.request('POST', url, headers=headers, data=json.dumps(envelope_data))
        _logger.info("[DocuSign API] Response received: status=%s", response.status_code)
        
        # Accept any 2xx status code as success (200, 201, 202, 204, etc.)
        if not (200 <= response.status_code < 300):
            _logger.error("[DocuSign API] ERROR: status=%s, response=%s", response.status_code, response.text)
            raise ValidationError((str(response.text)))
        
        # Parse response body if present (204 may have no content)
        data = response.json() if response.content else {}
        envelope_id = data.get('envelopeId')
        _logger.info("[DocuSign API] SUCCESS: envelope_id=%s created with %d signers", envelope_id, len(signers_list))
        return envelope_id
    except ValidationError:
        # Re-raise ValidationErrors as-is (already user-friendly)
        raise
    except Exception as e:
        _logger.exception("Failed to send multi-signer DocuSign envelope for file %s", file_name)
        raise ValidationError(_("An unexpected error occurred while sending the document to DocuSign. Please contact support."))


def create_recipient_view(env, user, envelope_id, signer_name, signer_email, client_user_id, return_url, ping_url=None):
    """
    Generate an embedded signing URL for a recipient on an existing envelope.

    Args:
        env: Odoo environment
        user: res.users record used for authentication
        envelope_id: DocuSign envelope ID
        signer_name: Recipient full name
        signer_email: Recipient email
        client_user_id: Stable identifier to mark recipient as embedded (string)
        return_url: URL DocuSign will redirect to after signing
        ping_url: Optional heartbeat URL for DocuSign to ping during session

    Returns:
        str: Recipient View URL to redirect the browser to
    """
    config = _get_docusign_config(env)
    access_token = _get_cached_access_token(env, user)

    payload = {
        "returnUrl": return_url,
        "authenticationMethod": "email",
        "email": _mask_email_for_environment(config, signer_email),
        "userName": signer_name,
        "clientUserId": str(client_user_id),
    }

    if ping_url:
        payload["pingUrl"] = ping_url
        payload["pingFrequency"] = 600

    url = f"{config['base_uri']}/restapi/v2.1/accounts/{config['account_id']}/envelopes/{envelope_id}/views/recipient"
    headers_local = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    _logger.info("[DocuSign API] Creating recipient view for envelope %s (client_user_id=%s)", envelope_id, client_user_id)
    response = requests.post(url, headers=headers_local, data=json.dumps(payload))

    if response.status_code not in (200, 201):
        _logger.error("[DocuSign API] Recipient view failed: status=%s body=%s", response.status_code, response.text)
        raise ValidationError(_("DocuSign recipient view failed (%s): %s") % (response.status_code, response.text))

    data = response.json()
    signing_url = data.get('url')
    if not signing_url:
        _logger.error("[DocuSign API] Recipient view missing URL: %s", response.text)
        raise ValidationError(_("DocuSign did not return a signing URL."))

    _logger.info("[DocuSign API] Recipient view raw URL: %s", signing_url)

    parsed = urlparse(signing_url)
    needs_normalization = (
        (not parsed.scheme or parsed.scheme.lower() not in ('http', 'https'))
        or not parsed.netloc
    )
    _logger.info(
        "[DocuSign API] Recipient view parse: scheme=%s netloc=%s path=%s needs_normalization=%s",
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        needs_normalization,
    )
    if needs_normalization:
        base_uri = (config.get('base_uri') or '').rstrip('/')
        if base_uri:
            base_parts = urlparse(base_uri)
            base_root = f"{base_parts.scheme}://{base_parts.netloc}" if base_parts.scheme and base_parts.netloc else base_uri
            signing_url = urljoin(base_root + '/', signing_url.lstrip('/'))
            _logger.info("[DocuSign API] Normalized signing URL to %s", signing_url)
        else:
            _logger.warning("[DocuSign API] Missing base_uri while normalizing signing URL %s", signing_url)

    _logger.info("[DocuSign API] Recipient view created successfully for envelope %s", envelope_id)
    return signing_url


def send_docusign_file(env, user, file_name, file_contents, receiver_name, receiver_email, partner=None):
    _logger.info("[DocuSign API] send_docusign_file() called: file=%s, recipient=%s (%s)", 
                file_name, receiver_name, receiver_email)
    try:
        # Get configuration from settings
        config = _get_docusign_config(env)
        _logger.info("[DocuSign API] Config loaded: environment=%s, account_id=%s", 
                    config['environment'], config['account_id'][:10] + '...' if config['account_id'] else 'None')
        
        # Get cached access token (auto-refreshes if expired)
        access_token = _get_cached_access_token(env, user)
        _logger.info("[DocuSign API] Access token obtained: %s...", access_token[:20] if access_token else 'None')

        # Mask recipient email when in sandbox/demo
        masked_email = _mask_email_for_environment(config, receiver_email)
        
        # Extract language code from partner (first 2 characters, e.g., 'es' from 'es_419')
        language_code = 'es'  # Default to Spanish
        if partner and partner.lang:
            language_code = partner.lang[:2] if len(partner.lang) >= 2 else 'es'
            _logger.info("[DocuSign API] Using language code: %s (from partner lang: %s)", 
                        language_code, partner.lang)
        
        # Build signer data with language
        signer_data = {
            "email": masked_email,
            "name": receiver_name,
            "recipientId": "1",
            "routingOrder": "1",
        }
        
        # Add language code to signer
        if language_code:
            signer_data["recipientLanguage"] = {
                "languageCode": language_code
            }
        
        # Add signature tabs using anchor string (PDF must contain /sn1/)
        signer_data["tabs"] = {
            "signHereTabs": [
                {
                    "anchorString": "/sn1/",
                    "anchorYOffset": "0",
                    "anchorUnits": "pixels",
                    "documentId": "1",
                    "pageNumber": "1"
                }
            ]
        }
        
        # Add company stamp image tab if configured
        company_stamp_base64 = env['ir.config_parameter'].sudo().get_param(
            'contract_management.docusign_company_stamp_base64'
        )
        if company_stamp_base64:
            signer_data["tabs"]["imageTabs"] = [
                {
                    "documentId": "1",
                    "pageNumber": "1",
                    "xPosition": "400",
                    "yPosition": "700",
                    "imageBase64": company_stamp_base64,
                    "tabLabel": "CompanyStamp"
                }
            ]
            _logger.info("[DocuSign API] Company stamp tab added to signer")
        
        envelope_data = {
            "emailSubject": "Please sign this document set",
            "documents": [
                {
                    "documentBase64": file_contents.decode("utf-8"),
                    "name": file_name,
                    "fileExtension": "pdf",
                    "documentId": "1"
                }
            ],
            "recipients": {
                "signers": [signer_data]
            },
            "status": "sent"
        }
        
        baseUrl = config['base_uri'] + '/restapi/v2.1/accounts/' + config['account_id']
        url = baseUrl + '/envelopes'
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Sending POST to %s environment: %s", config['environment'], url)
        _logger.info("[DocuSign API] Envelope payload: recipients=%d, documents=%d, status=%s", 
                    len(envelope_data['recipients']['signers']), 
                    len(envelope_data['documents']), 
                    envelope_data['status'])
        
        response = requests.request('POST', url, headers=headers, data=json.dumps(envelope_data))
        _logger.info("[DocuSign API] Response received: status=%s", response.status_code)
        
        # Accept any 2xx status code as success (200, 201, 202, 204, etc.)
        if not (200 <= response.status_code < 300):
            _logger.error("[DocuSign API] ERROR: status=%s, response=%s", response.status_code, response.text)
            raise ValidationError((str(response.text)))
        
        # Parse response body if present (204 may have no content)
        data = response.json() if response.content else {}
        envelope_id = data.get('envelopeId')
        _logger.info("[DocuSign API] SUCCESS: envelope_id=%s created", envelope_id)
        return envelope_id
    except ValidationError:
        # Re-raise ValidationErrors as-is (already user-friendly)
        raise
    except Exception as e:
        _logger.exception("Failed to send DocuSign envelope for file %s", file_name)
        raise ValidationError(_("An unexpected error occurred while sending the document to DocuSign. Please contact support."))


def replace_envelope_document(env, user, envelope_id, document_id, file_name, file_contents, resend_envelope=False):
    """
    Replace a document inside an existing DocuSign envelope (sent but unsigned).

    Args:
        env: Odoo environment
        user: res.users record with valid DocuSign token
        envelope_id: Target DocuSign envelope ID
        document_id: Document ID inside the envelope to replace
        file_name: New document name
        file_contents: Base64-encoded document content (string)
        resend_envelope: If True, DocuSign will resend notifications after replacement

    Returns:
        bool: True if replacement succeeds
    """
    _logger.info("[DocuSign API] replace_envelope_document() called: envelope=%s, document_id=%s, resend=%s",
                 envelope_id, document_id, resend_envelope)
    try:
        config = _get_docusign_config(env)
        access_token = _get_cached_access_token(env, user)

        file_extension = 'pdf'
        if file_name and '.' in file_name:
            file_extension = file_name.rsplit('.', 1)[1]

        base_url = f"{config['base_uri']}/restapi/v2.1/accounts/{config['account_id']}"
        url = f"{base_url}/envelopes/{envelope_id}/documents"
        if resend_envelope:
            url += "?resend_envelope=true"

        payload = {
            "documents": [
                {
                    "documentId": str(document_id),
                    "name": file_name,
                    "fileExtension": file_extension,
                    "documentBase64": file_contents if isinstance(file_contents, str) else file_contents.decode('utf-8'),
                }
            ]
        }

        headers['Authorization'] = f"Bearer {access_token}"
        _logger.info("[DocuSign API] PUT (replace document) to %s", url)

        response = requests.put(url, headers=headers, data=json.dumps(payload))
        _logger.info("[DocuSign API] replace document response: status=%s", response.status_code)

        # Accept any 2xx status code as success (200, 201, 202, 204, etc.)
        if not (200 <= response.status_code < 300):
            _logger.error("[DocuSign API] Failed to replace document: %s - %s", response.status_code, response.text)
            raise ValidationError(_(f"Failed to replace document in envelope: {response.text}"))

        _logger.info("[DocuSign API] Document %s replaced successfully in envelope %s", document_id, envelope_id)
        return True
    except ValidationError:
        raise
    except Exception as e:
        _logger.exception("Failed to replace document %s in envelope %s", document_id, envelope_id)
        raise ValidationError(_(f"An unexpected error occurred while replacing the document: {str(e)}"))


def get_envelope_details(env, user, envelopeId):
    """
    Get full envelope details including custom fields from DocuSign.
    
    Returns:
        dict with envelope data including customFields
    """
    _logger.info("[DocuSign API] get_envelope_details() called for envelope: %s", envelopeId)
    try:
        # Get configuration from settings
        config = _get_docusign_config(env)
        
        # Get cached access token (auto-refreshes if expired)
        access_token = _get_cached_access_token(env, user)
        
        url = config['base_uri'] + '/restapi/v2.1/accounts/' + config['account_id'] + '/envelopes/' + envelopeId
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Sending GET to %s environment: %s", config['environment'], url)
        
        response = requests.get(url, headers=headers)
        _logger.info("[DocuSign API] Response received: status=%s", response.status_code)
        
        if response.status_code != 200:
            _logger.error("[DocuSign API] ERROR: status=%s, response=%s", response.status_code, response.text)
            raise ValidationError(_("Failed to retrieve envelope details from DocuSign. Please try again."))
        
        envelope_data = response.json()
        _logger.info("[DocuSign API] Envelope details retrieved: status=%s, has_custom_fields=%s", 
                    envelope_data.get('status'), 'customFields' in envelope_data)
        
        return envelope_data
        
    except ValidationError:
        raise
    except Exception as e:
        _logger.exception("[DocuSign API] EXCEPTION in get_envelope_details for envelope %s", envelopeId)
        raise ValidationError(_("Failed to retrieve envelope details. Error: %s") % str(e))


def get_status(env, user, envelopeId):
    _logger.info("[DocuSign API] get_status() called for envelope: %s", envelopeId)
    try:
        # Get configuration from settings
        config = _get_docusign_config(env)
        
        # Get cached access token (auto-refreshes if expired)
        access_token = _get_cached_access_token(env, user)
        
        url = config['base_uri'] + '/restapi/v2.1/accounts/' + config['account_id'] + '/envelopes/' + envelopeId + "/recipients"
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Sending GET to %s environment: %s", config['environment'], url)
        
        response = requests.get(url, headers=headers)
        _logger.info("[DocuSign API] Response received: status=%s", response.status_code)
        
        if response.status_code != 200:
            _logger.error("[DocuSign API] ERROR: status=%s, response=%s", response.status_code, response.text)
            raise ValidationError(_("Failed to retrieve document status from DocuSign. Please try again."))
        
        data = response.json()
        signers = data.get('signers', [])
        
        if not signers:
            _logger.warning("[DocuSign API] No signers found in envelope %s", envelopeId)
            return 'unknown'
        
        # Return all signers' statuses as a dict keyed by email
        signer_statuses = {}
        for signer in signers:
            email = signer.get('email', '').lower()
            status = signer.get('status', 'unknown')
            signer_statuses[email] = status
            _logger.info("[DocuSign API] Signer %s status: %s", email, status)
        
        _logger.info("[DocuSign API] Status result for envelope %s: %d signers, statuses=%s", 
                    envelopeId, len(signers), signer_statuses)
        
        # For backward compatibility, return first signer's status if only requesting single status
        # Or return dict if multiple signers
        if len(signers) == 1:
            return signers[0].get('status', 'unknown')
        else:
            return signer_statuses
    except ValidationError:
        # Re-raise ValidationErrors as-is (already user-friendly)
        raise
    except Exception as e:
        _logger.exception("Failed to get status for envelope %s", envelopeId)
        raise ValidationError(_("An unexpected error occurred while checking document status. Please contact support."))


def download_documents(env, user, envelopeId):
    """
    Download signed documents from DocuSign envelope.
    
    Returns document content as bytes to be stored in ir.attachment.
    No longer writes to file system.
    
    Args:
        env: Odoo environment
        user: res.users record with valid DocuSign token
        envelopeId: DocuSign envelope ID
        
    Returns:
        tuple: (doc_status, document_data_dict)
            doc_status: 'completed' or other status string
            document_data_dict: {
                'filename': str,
                'content': bytes,
                'mimetype': str
            } or None if not completed
    """
    _logger.info("[DocuSign API] download_documents() called for envelope: %s", envelopeId)
    try:
        doc_status = get_status(env, user, envelopeId)
        _logger.info("[DocuSign API] Current status: %s", doc_status)
        
        # Check if all signers are completed (doc_status can be a dict or string)
        all_completed = False
        if isinstance(doc_status, dict):
            # If it's a dict, check that all values are 'completed'
            all_completed = all(status == 'completed' for status in doc_status.values())
            _logger.info("[DocuSign API] All signers completed: %s", all_completed)
        elif doc_status == 'completed':
            all_completed = True
        
        if not all_completed:
            _logger.warning("[DocuSign API] Download skipped: envelope %s status=%s (not all completed)", 
                          envelopeId, doc_status)
            return doc_status, None

        # Get configuration from settings
        config = _get_docusign_config(env)
        
        # Get cached access token (auto-refreshes if expired)
        access_token = _get_cached_access_token(env, user)
        
        baseUrl = config['base_uri'] + '/restapi/v2/accounts/' + config['account_id']
        envelopeUri = "/envelopes/" + envelopeId
        url = baseUrl + envelopeUri + '/documents'
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Fetching document list from %s environment: %s", config['environment'], url)
        
        response = requests.get(url, headers=headers)
        _logger.info("[DocuSign API] Document list response: status=%s", response.status_code)
        
        if response.status_code != 200:
            _logger.error("[DocuSign API] ERROR (list documents): status=%s, response=%s", 
                        response.status_code, response.text)
            raise ValidationError(_("Failed to retrieve document list from DocuSign. Please try again or contact support."))
        
        data = response.json()
        envelope = data.get('envelopeDocuments')
        envelope = envelope[0] if len(envelope) > 1 else False
        _logger.info("[DocuSign API] Documents found: %d", len(data.get('envelopeDocuments', [])))

        if not envelope:
            _logger.error("[DocuSign API] No documents in envelope %s", envelopeId)
            raise ValidationError(_("No documents found in envelope"))

        # Download document content
        document_uri = envelope.get("uri")
        url = baseUrl + document_uri
        headers['Authorization'] = 'Bearer ' + access_token
        _logger.info("[DocuSign API] Downloading document content: %s", url)
        
        response = requests.get(url, headers=headers)
        _logger.info("[DocuSign API] Document download response: status=%s, size=%d bytes", 
                    response.status_code, len(response.content))
        
        if response.status_code != 200:
            _logger.error("[DocuSign API] ERROR (download content): status=%s, response=%s", 
                        response.status_code, response.text)
            raise ValidationError(_("Failed to download document from DocuSign. Please try again or contact support."))

        content = response.content
        filename = envelope.get("name", "signed_document.pdf")
        
        # Determine mimetype
        mimetype = 'application/pdf'
        if filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.endswith('.docx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename.endswith('.doc'):
            mimetype = 'application/msword'
        
        _logger.info("[DocuSign API] SUCCESS: Downloaded %s (%d bytes) from envelope %s", 
                    filename, len(content), envelopeId)
        
        return doc_status, {
            'filename': filename,
            'content': content,
            'mimetype': mimetype
        }
    except ValidationError:
        # Re-raise ValidationErrors as-is (already user-friendly)
        raise
    except Exception as e:
        _logger.exception("Failed to download documents for envelope %s", envelopeId)
        raise ValidationError(_("An unexpected error occurred while downloading the document. Please contact support."))