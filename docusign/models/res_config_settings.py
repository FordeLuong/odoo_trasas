from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Production Environment
    docusign_prod_base_uri = fields.Char(
        string='Production Base URI',
        help='DocuSign production API base URL (e.g., https://na3.docusign.net)'
    )
    docusign_prod_account_id = fields.Char(
        string='Production Account ID',
        help='DocuSign production account ID'
    )
    docusign_prod_user_guid = fields.Char(
        string='Production API User GUID',
        help='DocuSign API User GUID (UUID format). Required for JWT authentication. Find in DocuSign Admin > Users > API Username > Actions > Edit'
    )
    docusign_prod_integration_key = fields.Char(
        string='Production Integration Key',
        help='DocuSign production integration key (Client ID)'
    )
    docusign_prod_secret_key = fields.Char(
        string='Production Secret Key',
        help='DocuSign production secret key (Client Secret)'
    )
    docusign_prod_private_key = fields.Text(
        string='Production RSA Private Key',
        help='RSA private key for JWT authentication (PEM format). Required for automatic token generation.'
    )

    # Demo Environment
    docusign_demo_base_uri = fields.Char(
        string='Demo Base URI',
        help='DocuSign demo/sandbox API base URL (e.g., https://demo.docusign.net)',
        default='https://demo.docusign.net'
    )
    docusign_demo_account_id = fields.Char(
        string='Demo Account ID',
        help='DocuSign demo/sandbox account ID'
    )
    docusign_demo_user_guid = fields.Char(
        string='Demo API User GUID',
        help='DocuSign API User GUID (UUID format). Required for JWT authentication. Find in DocuSign Admin > Users > API Username > Actions > Edit'
    )
    docusign_demo_integration_key = fields.Char(
        string='Demo Integration Key',
        help='DocuSign demo/sandbox integration key (Client ID)'
    )
    docusign_demo_secret_key = fields.Char(
        string='Demo Secret Key',
        help='DocuSign demo/sandbox secret key (Client Secret)'
    )
    docusign_demo_private_key = fields.Text(
        string='Demo RSA Private Key',
        help='RSA private key for JWT authentication (PEM format). Required for automatic token generation.'
    )

    # Demo test email
    docusign_demo_test_email = fields.Char(
        string='Demo/Sandbox Test Email',
        help='When environment is Demo/Sandbox, all DocuSign recipient emails are replaced with this address.'
    )
    
    # Webhook Configuration
    docusign_webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
        help='Use this URL in DocuSign Connect configuration. Copy and paste into DocuSign Admin > Connect > Add Configuration'
    )
    docusign_webhook_hmac_key = fields.Char(
        string='Webhook HMAC Key',
        help='Shared secret for HMAC signature verification. Generate a strong random key (32+ characters) and enter the same value in DocuSign Connect configuration.'
    )
    
    # Environment selector
    docusign_environment = fields.Selection([
        ('demo', 'Demo/Sandbox'),
        ('production', 'Production')
    ], string='Active Environment', default='demo',
       help='Select which DocuSign environment to use')

    @api.depends()
    def _compute_webhook_url(self):
        """Compute the webhook URL based on current Odoo base URL"""
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
            record.docusign_webhook_url = f"{base_url}/docusign/webhook"

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        res.update(
            docusign_prod_base_uri=params.get_param('docusign.prod_base_uri', default=''),
            docusign_prod_account_id=params.get_param('docusign.prod_account_id', default=''),
            docusign_prod_user_guid=params.get_param('docusign.prod_user_guid', default=''),
            docusign_prod_integration_key=params.get_param('docusign.prod_integration_key', default=''),
            docusign_prod_secret_key=params.get_param('docusign.prod_secret_key', default=''),
            docusign_prod_private_key=params.get_param('docusign.prod_private_key', default=''),
            docusign_demo_base_uri=params.get_param('docusign.demo_base_uri', default='https://demo.docusign.net'),
            docusign_demo_account_id=params.get_param('docusign.demo_account_id', default=''),
            docusign_demo_user_guid=params.get_param('docusign.demo_user_guid', default=''),
            docusign_demo_integration_key=params.get_param('docusign.demo_integration_key', default=''),
            docusign_demo_secret_key=params.get_param('docusign.demo_secret_key', default=''),
            docusign_demo_private_key=params.get_param('docusign.demo_private_key', default=''),
            docusign_demo_test_email=params.get_param('docusign.demo_test_email', default=''),
            docusign_webhook_hmac_key=params.get_param('docusign.webhook_hmac_key', default=''),
            docusign_environment=params.get_param('docusign.environment', default='demo'),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        
        params.set_param('docusign.prod_base_uri', self.docusign_prod_base_uri or '')
        params.set_param('docusign.prod_account_id', self.docusign_prod_account_id or '')
        params.set_param('docusign.prod_user_guid', self.docusign_prod_user_guid or '')
        params.set_param('docusign.prod_integration_key', self.docusign_prod_integration_key or '')
        params.set_param('docusign.prod_secret_key', self.docusign_prod_secret_key or '')
        params.set_param('docusign.prod_private_key', self.docusign_prod_private_key or '')
        params.set_param('docusign.demo_base_uri', self.docusign_demo_base_uri or 'https://demo.docusign.net')
        params.set_param('docusign.demo_account_id', self.docusign_demo_account_id or '')
        params.set_param('docusign.demo_user_guid', self.docusign_demo_user_guid or '')
        params.set_param('docusign.demo_integration_key', self.docusign_demo_integration_key or '')
        params.set_param('docusign.demo_secret_key', self.docusign_demo_secret_key or '')
        params.set_param('docusign.demo_private_key', self.docusign_demo_private_key or '')
        params.set_param('docusign.demo_test_email', self.docusign_demo_test_email or '')
        params.set_param('docusign.webhook_hmac_key', self.docusign_webhook_hmac_key or '')
        params.set_param('docusign.environment', self.docusign_environment or 'demo')
