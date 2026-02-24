# DocuSign Webhook Setup Guide

## Overview
DocuSign Connect webhooks provide real-time notifications when envelope events occur, eliminating the need for manual status checks and enabling instant updates in Odoo.

## Prerequisites
- Odoo DocuSign Connector v17.0.1.0 or later installed
- DocuSign account with admin access
- Public HTTPS URL for your Odoo instance (webhooks require HTTPS)

## Step 1: Configure Webhook in Odoo

1. **Access Settings**
   - Login to Odoo as Administrator
   - Go to: **Settings → Administration → DocuSign Settings**

2. **Copy Webhook URL**
   - Find the "Webhook Configuration" block
   - Copy the **Webhook URL** (e.g., `https://yourdomain.com/docusign/webhook`)
   - ⚠️ **Important**: URL must be publicly accessible via HTTPS

3. **Generate HMAC Key**
   - Generate a strong random key (minimum 32 characters)
   - Recommended method:
     ```python
     import secrets
     hmac_key = secrets.token_urlsafe(32)
     print(hmac_key)  # Example: xK7v9p2L8mQ4nR6tY1wZ3fH5jB8cD0eG...
     ```
   - Or use: https://www.random.org/passwords/ (length=32, special chars allowed)
   - Enter the key in **Webhook HMAC Key** field (password protected)

4. **Save Settings**
   - Click **Save** button
   - Keep this browser tab open (you'll need the HMAC key for Step 2)

## Step 2: Configure Connect in DocuSign

### For Production Environment:

1. **Access DocuSign Admin Console**
   - Go to: https://admin.docusign.com
   - Login with your DocuSign admin account

2. **Navigate to Connect Settings**
   - Click **Settings** (gear icon)
   - Select **Integrations** → **Connect**
   - Click **Add Configuration**

3. **Configure Connection**
   - **Configuration Name**: `Odoo Integration - Production`
   - **URL to Publish**: Paste the webhook URL from Step 1
   - **Enable HMAC**: ✅ Check the box
   - **HMAC Key**: Paste the same HMAC key from Step 1
   - **Message Format**: Select **JSON** (recommended) or **XML**
   - **Include HMAC Signature**: ✅ Checked
   - **Enable Mutual TLS**: ❌ Unchecked (unless you have custom certificates)

4. **Select Trigger Events**
   Check the following events:
   - ✅ **Envelope Sent**
   - ✅ **Envelope Delivered**
   - ✅ **Envelope Completed**
   - ✅ **Envelope Declined**
   - ✅ **Envelope Voided**
   - ❌ Other events (optional, but not currently processed by Odoo)

5. **Include Fields** (Optional)
   - **Include Documents**: ❌ Unchecked (documents downloaded separately)
   - **Include Certificate of Completion**: ❌ Unchecked
   - **Include Envelope Custom Fields**: ✅ Checked (recommended)
   - **Include Recipient Events**: ✅ Checked

6. **Retry Configuration**
   - **Enable Retry**: ✅ Checked
   - **Retry Times**: 3-5 (recommended)
   - **Minutes Between Retries**: 5-15 minutes

7. **Save Configuration**
   - Click **Save** or **Save and Test**
   - If "Test" button available, click it to send test webhook

### For Demo/Sandbox Environment:

Repeat steps above but use:
- **Admin Console**: https://admindemo.docusign.com
- **Configuration Name**: `Odoo Integration - Demo`
- Same webhook URL and HMAC key

## Step 3: Test Webhook

### Method 1: Send Test Envelope

1. **Create Test Record in Odoo**
   - Go to: **DocuSign → DocuSign Records**
   - Click **Create**
   - Add a recipient with valid email
   - Attach a PDF document
   - Click **Send Docs**

2. **Check Webhook Reception**
   - Monitor Odoo logs:
     ```bash
     tail -f /var/log/odoo/odoo-server.log | grep "DocuSign webhook"
     ```
   - Expected log entry:
     ```
     INFO odoo.addons.odoo_docusign.controllers.webhook_controller: DocuSign webhook received
     INFO odoo.addons.odoo_docusign.controllers.webhook_controller: Processing webhook for envelope XXXXX with status: sent
     ```

3. **Verify Status Update**
   - Open the DocuSign record in Odoo
   - Click **Chatter** (bottom of form)
   - Look for messages like:
     - "Document sent to John Doe"
     - "Document delivered to John Doe"
     - "Document completed by John Doe"

### Method 2: Check DocuSign Logs

1. **Access Connect Logs**
   - Go to: DocuSign Admin Console → Connect
   - Click on your configuration
   - Click **View Logs**

2. **Check Recent Deliveries**
   - Look for successful HTTP 200 responses
   - Failed deliveries show error details
   - Click on individual log entries to see request/response

## Troubleshooting

### Webhook Not Receiving Events

**Check 1: URL Accessibility**
```bash
# Test from external server (not Odoo server)
curl -X POST https://yourdomain.com/docusign/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```
Expected: HTTP 200 response (even with test data)

**Check 2: HTTPS Certificate**
- Webhooks require valid SSL certificate
- Self-signed certificates not supported
- Use Let's Encrypt or commercial certificate

**Check 3: Firewall/Proxy**
- Ensure port 443 (HTTPS) is open
- Check nginx/Apache config for /docusign/webhook route
- Verify no IP restrictions blocking DocuSign IPs

**Check 4: Odoo Configuration**
```bash
# Check if controller route is registered
sudo docker exec odoo2 bash -c "grep -r 'docusign/webhook' /opt/odoo/custom-addons/"
```

### Webhook Receiving but Status Not Updating

**Check 1: HMAC Verification**
- Ensure HMAC key in Odoo matches DocuSign exactly
- Check logs for "HMAC signature verification failed"
- If verification fails, webhook is rejected silently

**Check 2: Envelope ID Matching**
- Webhook updates only occur if envelope_id exists in Odoo
- Check logs: "No connector line found for envelope XXXXX"
- If missing, envelope was sent from DocuSign UI (not Odoo)

**Check 3: Database Permissions**
- Webhook runs with `sudo()` to bypass security
- Check for errors in logs related to write permissions

### Signature Verification Errors

If you see "Invalid signature" errors:

1. **Regenerate HMAC Key**
   - Delete old key in Odoo
   - Generate new key (32+ chars)
   - Update both Odoo and DocuSign with new key

2. **Check Clock Skew**
   - DocuSign webhooks include timestamp
   - Odoo checks timestamp is within 5 minutes (default)
   - Sync server time:
     ```bash
     sudo ntpdate -s time.nist.gov
     ```

3. **Verify Payload Encoding**
   - HMAC computed on raw POST body
   - Check Content-Type is application/json
   - Ensure no charset issues

## Advanced Configuration

### Webhook Timeout Settings

Default: 5 minutes timestamp tolerance

To change, add system parameter:
```sql
INSERT INTO ir_config_parameter (key, value)
VALUES ('docusign.webhook_timestamp_tolerance', '300');  -- seconds
```

### Disable HMAC Verification (Development Only)

⚠️ **Not recommended for production!**

To disable HMAC verification (allows webhooks without key):
- Leave `docusign.webhook_hmac_key` empty in settings
- Webhook controller will log warning but accept requests
- Use only for local development/testing

### Custom Event Handling

To add custom logic for specific events:

1. Edit: `controllers/webhook_controller.py`
2. Modify: `_update_envelope_status()` method
3. Add custom actions for specific statuses:
   ```python
   if status == 'completed' and line.partner_id.email:
       # Send custom thank you email
       template = env.ref('module.thank_you_template')
       template.send_mail(line.record_id.id)
   ```

## Security Best Practices

1. **HMAC Key Strength**
   - Minimum 32 characters
   - Use cryptographically secure random generator
   - Never commit to git or share publicly

2. **HTTPS Only**
   - Never use HTTP for webhooks (data in plain text)
   - Use valid SSL certificate (Let's Encrypt free)
   - Renew certificates before expiry

3. **Access Control**
   - Webhook endpoint is public (/docusign/webhook)
   - Security relies on HMAC signature
   - Monitor logs for suspicious activity

4. **Logging**
   - All webhook events logged with INFO level
   - Failed verification logged with WARNING level
   - Errors logged with ERROR level
   - Review logs regularly for anomalies

## Monitoring

### Recommended Monitoring

1. **Webhook Success Rate**
   - Check DocuSign Connect logs daily
   - Alert if success rate drops below 95%

2. **Envelope Status Sync**
   - Spot-check: manual status vs webhook status
   - Should match within 1-2 minutes

3. **Odoo Log Monitoring**
   - Set up alerts for:
     - "HMAC signature verification failed"
     - "DocuSign webhook: Unexpected error"
     - Multiple failures for same envelope

### Log Analysis

```bash
# Count webhook events by status (last 24 hours)
grep "Processing webhook for envelope" /var/log/odoo/odoo-server.log | \
  grep $(date +%Y-%m-%d) | \
  awk '{print $NF}' | \
  sort | uniq -c

# Find failed HMAC verifications
grep "HMAC signature verification failed" /var/log/odoo/odoo-server.log

# Find unmatched envelopes
grep "No connector line found for envelope" /var/log/odoo/odoo-server.log
```

## Support

If you encounter issues not covered in this guide:

1. **Check Odoo Logs**: Most issues show clear error messages
2. **Check DocuSign Logs**: Connect logs show delivery status
3. **Verify Configuration**: Double-check URL, HMAC key, events
4. **Contact Support**: Provide logs and configuration details

---

Last Updated: January 2026
Module Version: 17.0.1.0
