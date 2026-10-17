import io
import os
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, PngImagePlugin
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def make_key(password, salt):
    # Slow on purpose, so guessing passwords is hard
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000, 32)


def run_cipher(data, key, nonce):
    c = Cipher(algorithms.AES(key), modes.CTR(nonce)).encryptor()
    return c.update(data) + c.finalize()


def encrypt(img, password):
    pixels = np.array(img.convert("RGB"))
    salt = os.urandom(16)
    nonce = os.urandom(16)
    enc = run_cipher(pixels.tobytes(), make_key(password, salt), nonce)
    out = Image.fromarray(np.frombuffer(enc, dtype=np.uint8).reshape(pixels.shape))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("salt", salt.hex())
    meta.add_text("nonce", nonce.hex())
    buf = io.BytesIO()
    out.save(buf, format="PNG", pnginfo=meta)
    return out, buf.getvalue()


def decrypt(img, password):
    salt = bytes.fromhex(img.info["salt"])
    nonce = bytes.fromhex(img.info["nonce"])
    pixels = np.array(img.convert("RGB"))
    dec = run_cipher(pixels.tobytes(), make_key(password, salt), nonce)
    out = Image.fromarray(np.frombuffer(dec, dtype=np.uint8).reshape(pixels.shape))
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return out, buf.getvalue()


st.title("Image Encryption Tool")
st.write("Hide any photo behind a password using AES-256 encryption.")

mode = st.radio("What do you want to do?", ["Encrypt", "Decrypt"])
file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
password = st.text_input("Password", type="password")

if st.button("Go"):
    if file is None or password == "":
        st.warning("Please upload an image and type a password.")
    else:
        img = Image.open(file)
        if mode == "Encrypt":
            out, data = encrypt(img, password)
            st.image(out, caption="Encrypted image")
            st.download_button("Download encrypted image", data, "encrypted.png", "image/png")
        else:
            if "salt" not in img.info or "nonce" not in img.info:
                st.error("This is not an image made by this tool. Upload the encrypted.png file.")
            else:
                out, data = decrypt(img, password)
                st.image(out, caption="Decrypted image (if the password is wrong, this will look like noise)")
                st.download_button("Download decrypted image", data, "decrypted.png", "image/png")