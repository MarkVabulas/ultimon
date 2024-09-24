from OpenSSL import crypto

import socket
import json

def get_certificate_san(x509cert : crypto.X509):
    san = ''
    ext_count = x509cert.get_extension_count()
    for i in range(0, ext_count):
        ext = x509cert.get_extension(i)
        if 'subjectAltName' in str(ext.get_short_name()):
            san = ext.__str__()

    return san

def cert_gen(KEY_FILE = "private.key", CERT_FILE = "selfsigned.crt"):

    san_list = [
        f'DNS:{socket.gethostname()}',
    ]
    for ip in [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]]:
        if ip: 
            san_list.append(f'IP:{ip}')
    san_list.append('DNS:localhost')
    san_list.append('IP:127.0.0.1')
    san_list.append('IP:0:0:0:0:0:0:0:1')
    sans = ', '.join(san_list).encode()
    print('using addresses: ' + json.dumps(sans.decode('utf-8')))

    #can look at generated file using openssl:
    #openssl x509 -inform pem -in selfsigned.crt -noout -text
    # create a key pair
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)
    # create a self-signed cert
    x509 = crypto.X509()
    x509.get_subject().C = 'US'
    x509.get_subject().ST = 'None'
    x509.get_subject().L = 'None'
    x509.get_subject().O = 'UltimateSensorMonitor'
    x509.get_subject().OU = 'Server'
    x509.get_subject().CN = socket.gethostname()
    x509.get_subject().emailAddress = 'example@example.com'
    x509.set_version(2)
    x509.add_extensions([
        crypto.X509Extension(b'subjectAltName', False, sans),
        crypto.X509Extension(b'basicConstraints', True, b'CA:false')
    ])
    x509.set_serial_number(1)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(10*365*24*60*60) # seems like 10 years should be good enough
    x509.set_issuer(x509.get_subject())
    x509.set_pubkey(pkey)
    x509.sign(pkey, 'SHA256')
    with open(CERT_FILE, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, x509))
    with open(KEY_FILE, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
