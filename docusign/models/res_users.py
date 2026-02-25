from odoo.exceptions import ValidationError
import logging
from odoo import models, fields, api, exceptions, _
try:
    from docusign_esign import ApiClient
    api_client = ApiClient()
except Exception:
    api_client = None
    _logger = logging.getLogger(__name__)
    _logger.warning('Package docusign-esign not found. Install python package docusign-esign to enable DocuSign features.')
_logger = logging.getLogger(__name__)
import base64, json

# Odoo 19+ runs on Python 3 only; avoid six dependency
integer_types = (int,)
text_type = str

def iteritems(d):
    return d.items()
import requests
PRIMITIVE_TYPES = (float, bool, bytes, str, int)

SCOPES = [
    "signature"
]

ADMIN_SCOPES = [
    "signature", "organization_read", "group_read", "permission_read", "user_read", "user_write",
    "account_read", "domain_read", "identity_provider_read", "impersonation"
]

platform_type = {
    'dev': 'account-d.docusign.com',
    'prod': 'account.docusign.com'
}
envelope_events = ["Completed", "Declined", "Delivered", "Sent", "Voided"]


class ResUserCustom(models.Model):
    _inherit = 'res.users'

    record_name = fields.Char(string="Record Name", compute='ds_get_name', store=False)

    @api.depends('name')
    def ds_get_name(self):
        for rec in self:
            if rec.name:
                rec.record_name =  'DS-Account: ' + rec.name
            else:
                rec.record_name = 'DS-Account'
    # name = fields.Char(string="App Name",)
    code = fields.Char('Code')
    client_id = fields.Char('Integration Key')
    client_secret = fields.Char('Secret Key')
    account_type = fields.Selection([('dev', 'Developer'), ('prod', 'Production')],
                                    default='dev', string='Account Type')


    @api.onchange('account_type')
    def _check_account_type(self):
        for rec in self:
            if not rec.account_type:
                raise ValidationError(_("Account type can't be empty!"))

    login_url = fields.Char('Login URL', compute= '_compute_url')
    redirect_url = fields.Char('Redirect URL', compute='_get_current_url')
    access_token = fields.Char('Access Token')
    refresh_token = fields.Char('Refresh Token')
    token_expires_at = fields.Datetime('Token Expires At')
    # Deprecated: base_uri and account_id moved to centralized settings (Settings -> DocuSign Settings)
    # base_uri = fields.Char('Base URI')
    # account_id = fields.Char('Account ID')

    @api.depends('client_id')
    @api.depends_context('uid')
    def _get_current_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        for rec in self:
            rec.redirect_url = (base_url.rstrip('/') + '/docusign') if base_url else '/docusign'@api.depends('account_type', 'client_id', 'redirect_url')
    def _compute_url(self):
        url_scopes = "+".join(SCOPES)
        for rec in self:
            account_type = rec.account_type if rec.account_type else 'dev'
            if not api_client:
                rec.login_url = False
                continue
            api_client.set_oauth_host_name(oauth_host_name=platform_type[account_type])
            rec.login_url = api_client.get_authorization_uri(rec.client_id, SCOPES, rec.redirect_url, 'code')

    def get_code(self):
        for rec in self:
            if rec.redirect_url and rec.client_id and rec.client_secret:
                return {
                    'name': 'login',
                    'view_id': False,
                    "type": "ir.actions.act_url",
                    'target': 'self',
                    'url': rec.login_url
                }
            else:
                raise ValidationError('Docusign Credentials are missing. Please ask system admin to add credentials')

    def generate_access_token(self, client_id, client_secret, code):
        url = "https://{0}/oauth/token".format(platform_type[self.account_type])
        integrator_and_secret_key = b"Basic " + base64.b64encode(str.encode("{}:{}".format(client_id, client_secret)))
        headers = {
            "Authorization": integrator_and_secret_key.decode("utf-8"),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        post_params = self.sanitize_for_serialization({
            "grant_type": "authorization_code",
            "code": code
        })
        response = api_client.rest_client.POST(url, headers=headers, post_params=post_params)
        return response

    def get_access_token(self):
        try:
            for rec in self:
                response = self.generate_access_token(rec.client_id, rec.client_secret, rec.code)
                if response.status == 200:
                    data = json.loads(response.data)
                    if 'access_token' in data:
                        from datetime import datetime, timedelta
                        expires_in = int(data['expires_in'])
                        expiry_time = datetime.now() + timedelta(seconds=expires_in)
                        self.write({
                            'access_token': data['access_token'],
                            'refresh_token': data['refresh_token'],
                            'token_expires_at': expiry_time
                        })
                        self.get_user_info()
                return self.action_of_button("Successfully generated the access token!")
        except Exception as e:
            raise ValidationError(_("Not a valid request for access token\nTry again in few seconds "
                                    "after re-trying login with above button."))

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        try:
            if not self.refresh_token:
                _logger.error("No refresh token available for user %s", self.login)
                raise ValidationError(_("No refresh token available. Please re-authenticate."))
            
            url = "https://{0}/oauth/token".format(platform_type[self.account_type])
            integrator_and_secret_key = b"Basic " + base64.b64encode(
                str.encode("{}:{}".format(self.client_id, self.client_secret))
            )
            headers = {
                "Authorization": integrator_and_secret_key.decode("utf-8"),
                "Content-Type": "application/x-www-form-urlencoded",
            }
            post_params = self.sanitize_for_serialization({
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            })
            
            response = api_client.rest_client.POST(url, headers=headers, post_params=post_params)
            
            if response.status == 200:
                data = json.loads(response.data)
                if 'access_token' in data:
                    from datetime import datetime, timedelta
                    expires_in = int(data['expires_in'])
                    expiry_time = datetime.now() + timedelta(seconds=expires_in)
                    self.write({
                        'access_token': data['access_token'],
                        'refresh_token': data.get('refresh_token', self.refresh_token),  # Some APIs don't return new refresh token
                        'token_expires_at': expiry_time
                    })
                    _logger.info("Successfully refreshed access token for user %s", self.login)
                    return data['access_token']
            else:
                _logger.error("Failed to refresh token: status=%s, response=%s", response.status, response.data)
                raise ValidationError(_("Failed to refresh access token. Please re-authenticate."))
        except Exception as e:
            _logger.exception("Error refreshing access token for user %s", self.login)
            raise ValidationError(_("Failed to refresh access token: {}").format(str(e)))
    
    def get_valid_access_token(self):
        """Get a valid access token, refreshing if necessary."""
        from datetime import datetime, timedelta
        
        if not self.access_token:
            raise ValidationError(_("No access token available. Please authenticate with DocuSign."))
        
        # Check if token will expire in the next 5 minutes
        if self.token_expires_at:
            buffer_time = datetime.now() + timedelta(minutes=5)
            if self.token_expires_at <= buffer_time:
                _logger.info("Access token expired or expiring soon for user %s, refreshing...", self.login)
                return self.refresh_access_token()
        
        return self.access_token

    def get_user_info(self):
        try:
            for rec in self:
                url = "https://{0}/oauth/userinfo".format(platform_type[self.account_type])
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + self.access_token
                }
                response = requests.request("GET", url, headers=headers)
                print(response)
                if response.status_code != 200:
                    raise ValidationError((str(response.text)))
                data = response.json()
                if 'accounts' in data:
                    # Note: account_id and base_uri are now managed centrally in Settings -> DocuSign Settings
                    # This OAuth user info is kept for future reference but not stored on user record
                    _logger.info("DocuSign OAuth user info retrieved: %s accounts found", len(data['accounts']))
                    for account in data['accounts']:
                        _logger.debug("DocuSign account available: account_id=%s, base_uri=%s", 
                                     account.get('account_id'), account.get('base_uri'))
        except Exception as e:
            raise ValidationError(_("Not a valid request for user info."))

    def sanitize_for_serialization(self, obj):
        PRIMITIVE_TYPES = (float, bool, bytes, str, int)
        if obj is None:
            return None
        elif isinstance(obj, PRIMITIVE_TYPES):
            return obj
        elif isinstance(obj, list):
            return [self.sanitize_for_serialization(sub_obj)
                    for sub_obj in obj]
        elif isinstance(obj, tuple):
            return tuple(self.sanitize_for_serialization(sub_obj)
                         for sub_obj in obj)

        if isinstance(obj, dict):
            obj_dict = obj
        else:
            obj_dict = {obj.attribute_map[attr]: getattr(obj, attr)
                        for attr, _ in iteritems(obj.swagger_types)
                        if getattr(obj, attr) is not None}

        return {key: self.sanitize_for_serialization(val)
                for key, val in iteritems(obj_dict)}

    def action_of_button(self, message):
        message_id = self.env['message.wizard'].sudo().create({'message': _(message)})
        return {
            'name': _('Successful'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }