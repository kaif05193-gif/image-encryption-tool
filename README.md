# Image Encryption Tool

A web app that encrypts and decrypts images using AES-256, built with Python and Streamlit.

**Live app:** https://image-encryption-tool-ciyimpfzxzg2unysxeplqg.streamlit.app/

## What it does

- Turns any photo into a random-looking noise image using a password
- Restores the exact original image with the same password
- A wrong password gives only noise

## How it works

1. The password is turned into a 256-bit key using PBKDF2-SHA256 with a random salt.
2. The image pixels (RGB values) are encrypted with AES-256 in CTR mode.
3. The encrypted pixels are saved as a lossless PNG. The salt and nonce are stored inside the PNG, so only one file and the password are needed to decrypt.

## Security analysis

Tested on a sample photo:

| Test | Original | Encrypted |
|---|---|---|
| Entropy (ideal = 8) | 6.2068 | 7.9999 |
| Horizontal correlation | 0.9900 | -0.0001 |
| Vertical correlation | 0.9914 | 0.0001 |
| Diagonal correlation | 0.9838 | 0.0001 |

The encrypted image is almost perfectly random, and neighbouring pixels show no relationship.

## Technologies

Python, Streamlit, Pillow, NumPy, cryptography

## Run it on your computer

    pip install -r requirements.txt
    python -m streamlit run app.py

## Limitations

- CTR mode does not detect tampering or a wrong password; a wrong password simply produces noise.
- Sending the encrypted PNG through apps that recompress or strip image data (for example some chat apps) can break decryption. Send it as a file or by email.

## Author

Kaif, project
