#!/usr/bin/env python
"""Convert PFX certificate to PEM format for Flask"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import sys

try:
    # Read the PFX file
    with open('cert.pfx', 'rb') as f:
        pfx_data = f.read()
    
    # Load the PFX with password
    from cryptography.hazmat.primitives.serialization import pkcs12
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
        pfx_data,
        b'temppass',
        backend=default_backend()
    )
    
    # Write private key to key.pem
    with open('key.pem', 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate to cert.pem
    with open('cert.pem', 'wb') as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))
    
    print("✅ Certificate converted successfully!")
    print("   Created: cert.pem and key.pem")
    
except ImportError:
    print("❌ Error: cryptography package not installed")
    print("   Run: pip install cryptography")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error converting certificate: {e}")
    sys.exit(1)
