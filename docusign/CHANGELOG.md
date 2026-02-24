# Odoo DocuSign Connector - Changelog

## Version 17.0.1.0 (January 2026)

### 🎉 Major Features

#### Webhook Support
- **Real-time notifications**: Receive instant updates when envelope events occur (sent, delivered, completed, declined, voided)
- **HMAC signature verification**: Secure webhook endpoint with HMAC-SHA256 signature validation
- **Automatic status updates**: Envelope and recipient statuses update automatically without manual refresh
- **Configure in Settings**: New webhook configuration section with auto-generated webhook URL

**Setup Instructions:**
1. Go to: Settings → Administration → DocuSign Settings
2. Copy the generated Webhook URL
3. Generate a strong HMAC key (32+ characters) and enter it
4. Login to DocuSign Admin Console (admin.docusign.com or admindemo.docusign.com)
5. Navigate to: Settings → Connect → Add Configuration
6. Paste the webhook URL and HMAC key
7. Select events: Envelope Sent, Delivered, Completed, Declined, Voided
8. Save configuration

#### Document Storage with ir.attachment
- **No more file system storage**: Signed documents now stored in Odoo's ir.attachment system
- **Better security**: Attachments respect Odoo's access control rules
- **Automatic backup**: Documents backed up with regular Odoo database backups
- **Proper linking**: Attachments linked to docusign.connector.lines for easy access
- **Mimetype detection**: Automatic detection of PDF/DOCX/DOC file types

#### Complete Audit Trail
- **Chatter integration**: All DocuSign events logged in chatter (mail.thread)
- **Field tracking**: Status changes automatically tracked (state, partner_id, envelope_id, etc.)
- **Event logging**: Every send, sign, complete, decline, and void action logged with timestamp
- **User attribution**: All actions show which user triggered them
- **Searchable history**: Full audit trail searchable and exportable

#### Improved Error Messages
- **User-friendly errors**: No more raw API errors shown to users
- **Contextual help**: Error messages explain what went wrong and how to fix it
- **Example**: Instead of "Error calling webservice, status is: 401", now shows:
  - "You need to authenticate credentials for logged-in user!"
  - "Email address is missing for recipient: John Doe. Please update the contact information."
  - "Only PDF files are supported. Please convert document.docx to PDF format."
- **Support contact**: Errors suggest contacting support for unexpected issues

#### Token Management
- **Auto-refresh**: Access tokens automatically refresh when expiring (within 5 minutes)
- **Expiration tracking**: Token expiry stored in database (token_expires_at field)
- **No interruptions**: Users never experience auth failures mid-operation
- **Centralized settings**: OAuth credentials managed in Settings → DocuSign Settings

### 🔧 Technical Improvements

#### Controllers
- New: `webhook_controller.py` - Handles DocuSign Connect webhooks
- HMAC verification with configurable key
- JSON payload parsing and validation
- Idempotent envelope status updates

#### Models
- Added `mail.thread` and `mail.activity.mixin` inheritance to:
  - `docusign.connector`
  - `docusign.connector.lines`
- Added `tracking=True` to key fields:
  - state, responsible_id, docs_policy (connector)
  - partner_id, status, envelope_id, send_status, sign_status (lines)
- Updated `download_documents()` to return dict with filename, content, mimetype
- Removed file system path dependencies

#### Settings
- New fields:
  - `docusign_webhook_url` (computed, read-only)
  - `docusign_webhook_hmac_key` (password field)
- Removed field:
  - `docusign_file_path` (deprecated)
- Updated view with webhook configuration block and setup instructions

#### Error Handling
- All `try-except` blocks updated with:
  - User-friendly ValidationError messages
  - Comprehensive logging with context
  - Proper exception re-raising
- Removed raw API error exposure

### 📦 Dependencies
- Added: `mail` (for mail.thread and chatter)
- Existing: `base`, `contacts`, `sale_management`, `purchase`, `account`

### 🔄 Migration Notes

**From 17.0.0.9 to 17.0.1.0:**

1. **Database updates will auto-apply** when module upgrades
   - New columns: None (all fields already exist or are computed)
   - Model changes: mail.thread inheritance added (auto-creates mail tracking tables)

2. **Settings migration**:
   - Existing DocuSign credentials remain intact
   - New webhook fields start empty (configure manually)
   - Old `docusign_file_path` ignored (deprecated, not deleted)

3. **File storage migration**:
   - Old files in `/mnt/docusign/files/` remain on disk (not deleted)
   - New downloads go to ir.attachment automatically
   - To migrate old files: manually create ir.attachment records pointing to existing files

4. **No breaking changes**:
   - All existing functionality remains compatible
   - Webhook is optional (module works without it)
   - ir.attachment storage transparent to users

### ⚠️ Known Issues
- None at release

### 🔮 Future Enhancements
- Bulk document download button
- Envelope templates support
- Custom email subject/body for envelopes
- Integration with Odoo's document management system
- Support for multiple signers per envelope (DocuSign tabs)
- Webhook event log/history view

---

## Version 17.0.0.9 (January 2026)

### Features
- Centralized settings page (res.config.settings)
- Automatic token refresh with expiration handling
- Removed httplib2 dependency (replaced with requests)
- Comprehensive logging throughout codebase
- User-specific OAuth fields cleaned up

---

## Earlier Versions
See git history for details on versions 17.0.0.1 - 17.0.0.8
