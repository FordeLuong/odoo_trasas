{
    'name': "Cabal Docusign Connector",
    'summary': """The Odoo-DocuSign Connector integrates Odoo with DocuSign for seamless e-signature management. Send, track, and retrieve 
    signed documents effortlessly while automating status updates via webhooks.""",
    'description': """
        Odoo is a fully integrated suite of business modules that encompass the traditional ERP functionality.
        DocuSign is the Global Standard for eSignature, is the leader in eSignature transaction management.
        Global enterprises, Business departments, individual professionals, and consumers are standardizing on
        DocuSign, with more than 60,000 new users joining the DocuSign Global Network
        every day. DocuSign is used to accelerate transaction times to increase speed to results, reduce costs,
        and delight customers across nearly every industry—from financial services, insurance, technology,
        healthcare, manufacturing, communications, property management and consumer goods, to higher education
        and others. Odoo integration with Docusign enhances operation of organization with legitimate
        documentation.
        
        Version 17.0.1.0 adds:
        - Real-time webhook support for envelope events (sent, delivered, completed, declined, voided)
        - Automatic document storage in ir.attachment (replaces file system storage)
        - Complete audit trail via mail.thread (chatter) integration
        - Improved user-friendly error messages
        - Automatic token refresh with expiration handling
        - HMAC signature verification for webhook security
        
        Version 17.0.1.2 adds:
        - Interactive dashboard with real-time statistics
        - Envelope status tracking (new, sent, completed)
        - Recipient signature monitoring
        - Completion rate and average time metrics
        - Filterable by date range and responsible user
        - Quick action buttons to view records by status
    """,
    'author': "Techloyce",
    'website': "http://www.techloyce.com",
    'category': 'Sale',
    'version': '17.0.1.5',
    'depends': ['base', 'contacts', 'sale_management', 'purchase', 'account', 'mail'],
    'external_dependencies': {
        'python': ['jwt', 'cryptography'],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'price': 499,
    'currency': 'USD',
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/dashboard_data.xml',
        'views/inherited_views.xml',
        'views/connector_view.xml',
        'views/docusign_dashboard_views.xml',
        'views/user_view.xml',
        'views/res_config_settings_views.xml',
        'wizards/wizard.xml',
        'views/template.xml',
    ],
    'installable': 'True',
    'application': 'True',
    'license': 'OPL-1',
}