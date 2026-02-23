# SSL Certificate Setup for Local Network HTTPS

## Overview

The Crusade Admin PWA requires HTTPS to enable Service Workers and offline functionality. For local network deployment, we use self-signed SSL certificates.

## Server Setup

The Flask server is configured to use adhoc SSL certificates, which are automatically generated when the server starts.

### Prerequisites

Install required packages:
```bash
pip install -r requirements.txt
```

This includes:
- `pyopenssl>=23.0.0` - For adhoc SSL support
- `Flask>=2.2.3` - Web framework
- `Flask-Login>=0.6.3` - Authentication system

### Starting the Server

```bash
cd CareBot/CareBot
python server_app.py
```

The server will start on `https://0.0.0.0:5000` with an automatically generated self-signed certificate.

## Client Device Setup

When accessing the server from mobile devices or browsers, you'll need to accept the self-signed certificate.

### Android Devices

1. Open Chrome or your default browser
2. Navigate to `https://192.168.1.100:5000` (replace with your server IP)
3. You'll see a "Your connection is not private" warning
4. Tap **Advanced**
5. Tap **Proceed to 192.168.1.100 (unsafe)**
6. The certificate will be remembered for this session

**For permanent installation:**
1. Download the certificate from the server
2. Go to **Settings** → **Security** → **Encryption & credentials** → **Install a certificate**
3. Select **CA certificate**
4. Browse and select the downloaded certificate
5. Enter your device PIN/password if prompted

### iOS Devices (iPhone/iPad)

1. Open Safari (other browsers may not support PWA on iOS)
2. Navigate to `https://192.168.1.100:5000`
3. You'll see a certificate warning
4. Tap **Show Details** → **visit this website**
5. Confirm by tapping **Visit Website** again

**For permanent installation:**
1. Download the certificate profile
2. Go to **Settings** → **General** → **VPN & Device Management**
3. Under "Downloaded Profile", tap the certificate
4. Tap **Install** (enter passcode if prompted)
5. Tap **Install** again to confirm
6. Go to **Settings** → **General** → **About** → **Certificate Trust Settings**
7. Enable the certificate under "Enable Full Trust for Root Certificates"

### Windows Devices

**Chrome/Edge:**
1. Navigate to `https://192.168.1.100:5000`
2. Click **Advanced**
3. Click **Proceed to 192.168.1.100 (unsafe)**

**Permanent installation:**
1. In the browser, click the **Not Secure** warning in address bar
2. Click **Certificate** → **Details** → **Copy to File**
3. Save as .cer file
4. Double-click the .cer file
5. Click **Install Certificate**
6. Select **Local Machine** → **Next**
7. Select **Place all certificates in the following store**
8. Click **Browse** → select **Trusted Root Certification Authorities**
9. Click **OK** → **Next** → **Finish**

### macOS Devices

**Safari/Chrome:**
1. Navigate to `https://192.168.1.100:5000`
2. Click **Show Details** → **visit this website**

**Permanent installation:**
1. Download the certificate
2. Double-click to open in Keychain Access
3. Select **System** keychain
4. Find the certificate (search for "192.168.1.100")
5. Double-click the certificate
6. Expand **Trust** section
7. Set **When using this certificate** to **Always Trust**
8. Close window and enter your password to save

## Production Deployment

For production use, replace adhoc certificates with proper certificates:

### Option 1: Let's Encrypt (requires domain)

```bash
certbot certonly --standalone -d your-domain.com
```

Update `server_app.py`:
```python
app.run(
    host='0.0.0.0', 
    port=5000, 
    ssl_context=(
        '/etc/letsencrypt/live/your-domain.com/fullchain.pem',
        '/etc/letsencrypt/live/your-domain.com/privkey.pem'
    )
)
```

### Option 2: Self-Signed for Local Network (OpenSSL)

If you have OpenSSL installed:

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
    -out cert.pem -keyout key.pem -days 365 \
    -subj "/CN=192.168.1.100"
```

Update `server_app.py`:
```python
app.run(
    host='0.0.0.0', 
    port=5000, 
    ssl_context=('cert.pem', 'key.pem')
)
```

### Option 3: Windows Self-Signed Certificate

Already done! The `cert.pfx` is in the CareBot folder. To use it:

1. Install `cryptography` package (if on x86/x64 system)
2. Run the conversion script (already created)
3. Update server_app.py to use `ssl_context=('cert.pem', 'key.pem')`

## Troubleshooting

### "ERR_CERT_AUTHORITY_INVALID"

This is normal for self-signed certificates. Follow the device-specific steps above to trust the certificate.

### "ERR_SSL_VERSION_OR_CIPHER_MISMATCH"

Update pyOpenSSL:
```bash
pip install --upgrade pyopenssl
```

### Service Worker not registering

- Ensure you're using HTTPS (not HTTP)
- Check browser console for errors
- Verify the certificate is trusted
- Try clearing browser cache and reloading

### PWA not installable

- Must use HTTPS
- Must have valid manifest.json
- Must have registered Service Worker
- On iOS, must use Safari

## Security Notes

⚠️ **Self-signed certificates are only secure for local network use**

- Do not expose the server to the public internet with self-signed certificates
- Users will see security warnings until they manually trust the certificate
- For production, use proper CA-signed certificates (Let's Encrypt is free!)

## Configuration

The server IP is hardcoded in several places. To change it:

1. `server_app.py` - Update print statements
2. `mobile_app/crusade_mobile.py` - Update `self.sync_url`
3. Certificate - Regenerate with new IP in CN field

## Testing HTTPS

```bash
# From command line
curl -k https://192.168.1.100:5000/api/ping

# Expected response:
# {"status":"ok","timestamp":"2026-02-23T13:26:00.123456"}
```

From browser:
1. Open `https://192.168.1.100:5000`
2. Accept certificate warning
3. Should see the admin login page
