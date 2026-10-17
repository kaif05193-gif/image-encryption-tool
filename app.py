import io
import os
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, PngImagePlugin
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

st.set_page_config(page_title="Image Encryption Tool", page_icon="🔐")

st.markdown("""
<style>
.hero {background: linear-gradient(135deg, #4f46e5, #9333ea, #ec4899); padding: 2.2rem 1.5rem; border-radius: 18px; text-align: center; margin-bottom: 1.2rem;}
.hero h1 {color: white !important; margin: 0; font-size: 2.3rem;}
.hero p {color: #f3e8ff !important; margin: 0.5rem 0 0 0; font-size: 1.05rem;}
.card {background: rgba(147, 51, 234, 0.10); border: 1px solid rgba(147, 51, 234, 0.25); border-radius: 14px; padding: 1rem; text-align: center; min-height: 170px;}
.card h4 {margin: 0 0 0.3rem 0;}
.card p {margin: 0; font-size: 0.9rem; opacity: 0.85;}
div.stButton > button {background: linear-gradient(135deg, #4f46e5, #9333ea); color: white; border: none; border-radius: 10px; padding: 0.6rem 1.4rem; font-weight: 600; width: 100%;}
div.stButton > button:hover {color: white; opacity: 0.9;}
.footer {text-align: center; opacity: 0.6; font-size: 0.85rem; margin-top: 2rem;}
</style>
""", unsafe_allow_html=True)


def make_key(password, salt):
    # Slow on purpose, so guessing passwords is hard
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000, 32)


def run_cipher(data, key, nonce):
    c = Cipher(algorithms.AES(key), modes.CTR(nonce)).encryptor()
    return c.update(data) + c.finalize()


def entropy(channel):
    counts = np.bincount(channel.flatten(), minlength=256)
    p = counts / counts.sum()
    p = p[p > 0]
    return -np.sum(p * np.log2(p))


def average_entropy(pixels):
    return np.mean([entropy(pixels[:, :, i]) for i in range(3)])


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


st.markdown('<div class="hero"><h1>🔐 Image Encryption Tool</h1><p>Hide any photo behind a password using AES-256 encryption</p></div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.markdown('<div class="card"><h4>🛡️ AES-256</h4><p>A strong, widely used encryption standard</p></div>', unsafe_allow_html=True)
c2.markdown('<div class="card"><h4>🔑 Password locked</h4><p>Only the right password restores your photo</p></div>', unsafe_allow_html=True)
c3.markdown('<div class="card"><h4>📱 Works anywhere</h4><p>Use it on your phone or laptop</p></div>', unsafe_allow_html=True)

st.write("")
mode = st.radio("What do you want to do?", ["🔒 Encrypt", "🔓 Decrypt"], horizontal=True)

if mode == "🔒 Encrypt":
    st.subheader("Encrypt a photo")
    file = st.file_uploader("Choose a photo", type=["png", "jpg", "jpeg"], key="enc_file")
    password = st.text_input("Choose a password", type="password", key="enc_pw")
    if st.button("Encrypt now", key="enc_btn"):
        if file is None or password == "":
            st.warning("Please choose a photo and type a password.")
        else:
            img = Image.open(file)
            out, data = encrypt(img, password)
            col1, col2 = st.columns(2)
            col1.image(img, caption="Original")
            col2.image(out, caption="Encrypted")
            m1, m2 = st.columns(2)
            m1.metric("Randomness of original (max 8)", f"{average_entropy(np.array(img.convert('RGB'))):.2f}")
            m2.metric("Randomness of encrypted (max 8)", f"{average_entropy(np.array(out)):.2f}")
            st.success("Done! Download your encrypted image and keep your password safe.")
            st.download_button("Download encrypted image", data, "encrypted.png", "image/png")
else:
    st.subheader("Decrypt a photo")
    file2 = st.file_uploader("Choose the encrypted PNG", type=["png"], key="dec_file")
    password2 = st.text_input("Enter the password", type="password", key="dec_pw")
    st.caption("A forgotten password cannot be recovered.")
    if st.button("Decrypt now", key="dec_btn"):
        if file2 is None or password2 == "":
            st.warning("Please choose the encrypted image and type the password.")
        else:
            img2 = Image.open(file2)
            if "salt" not in img2.info or "nonce" not in img2.info:
                st.error("This image was not made by this tool. Upload the encrypted.png file.")
            else:
                out2, data2 = decrypt(img2, password2)
                col1, col2 = st.columns(2)
                col1.image(img2, caption="Encrypted")
                col2.image(out2, caption="Result (noise means a wrong password)")
                st.download_button("Download decrypted image", data2, "decrypted.png", "image/png")

st.markdown('<div class="footer">BCA final-year project · Built with Python and Streamlit</div>', unsafe_allow_html=True)
