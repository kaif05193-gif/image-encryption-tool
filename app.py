import io
import os
import random
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, PngImagePlugin
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

st.set_page_config(page_title="Image Encryption Tool")

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600&display=swap');
.block-container {max-width: 820px; padding-top: 2rem;}
h1, h2, h3 {font-family: 'Fraunces', Georgia, serif !important; font-weight: 600 !important;}
.hero {background: #0E3B43; border-radius: 22px; padding: 2.2rem; display: flex; flex-wrap: wrap; align-items: center; gap: 1.6rem; margin-bottom: 2rem;}
.hero-text {flex: 1 1 280px;}
.hero h1 {color: #FFFFFF !important; font-size: 2.5rem; line-height: 1.15; margin: 0 0 0.9rem 0; padding: 0;}
.hero p {color: #CFE6E3; font-size: 1.05rem; line-height: 1.6; margin: 0;}
.hero-art {flex: 1 1 250px; max-width: 380px;}
.hero-art svg {width: 100%; height: auto; display: block;}
.steps {display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1.6rem; margin-bottom: 2rem;}
.steps div {border-top: 2px solid #9CCFC9; padding-top: 0.7rem; line-height: 1.5;}
.steps .num {font-family: 'Fraunces', Georgia, serif; font-size: 1.9rem; color: #C4800F; display: block; line-height: 1.1;}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


def flat(html):
    # Put HTML on one line so Markdown never mistakes indented lines for code
    return "".join(line.strip() for line in html.splitlines())


def hero_art():
    # A small picture: a photo, a lock, and the photo turned into coloured squares
    rng = random.Random(7)
    colors = ["#F2B84B", "#E4572E", "#2FA3A3", "#BFE3DF", "#FFFFFF", "#7FD1C7"]
    cells = ""
    for r in range(6):
        for c in range(7):
            x = 206 + c * 22
            y = 22 + r * 22
            color = rng.choice(colors)
            cells += f'<rect x="{x}" y="{y}" width="20" height="20" rx="3" fill="{color}"/>'
    photo = """
    <defs><clipPath id="frame"><rect x="10" y="22" width="150" height="130" rx="12"/></clipPath></defs>
    <g clip-path="url(#frame)">
      <rect x="10" y="22" width="150" height="130" fill="#BFE3DF"/>
      <circle cx="58" cy="62" r="17" fill="#F2B84B"/>
      <path d="M0 152 L0 112 Q45 78 95 110 T170 100 L170 152 Z" fill="#2FA3A3"/>
      <path d="M0 152 L0 130 Q60 108 120 132 T170 126 L170 152 Z" fill="#0E6B73"/>
    </g>
    """
    lock = """
    <path d="M176 80 v-6 a8 8 0 0 1 16 0 v6" fill="none" stroke="#F2B84B" stroke-width="3" stroke-linecap="round"/>
    <rect x="172" y="80" width="24" height="20" rx="4" fill="#F2B84B"/>
    """
    return flat('<svg viewBox="0 0 364 174" xmlns="http://www.w3.org/2000/svg">' + photo + lock + cells + "</svg>")


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


HERO = """
<div class="hero">
  <div class="hero-text">
    <h1>Lock your photos<br>with a password.</h1>
    <p>Pick a picture, choose a password, and get back a scrambled copy that looks like colourful static.
    Only your password can bring the photo back.</p>
  </div>
  <div class="hero-art">__ART__</div>
</div>
"""
st.markdown(flat(HERO.replace("__ART__", hero_art())), unsafe_allow_html=True)

STEPS = """
<div class="steps">
  <div><span class="num">1</span><b>Choose a photo</b><br>A PNG or JPG from your phone or computer.</div>
  <div><span class="num">2</span><b>Set a password</b><br>It becomes the key that locks the picture.</div>
  <div><span class="num">3</span><b>Download the result</b><br>Share it safely. Only the password opens it.</div>
</div>
"""
st.markdown(flat(STEPS), unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### Lock or unlock a photo")
    mode = st.radio("What would you like to do?", ["Lock a photo", "Unlock a photo"], horizontal=True)

    if mode == "Lock a photo":
        file = st.file_uploader("Photo", type=["png", "jpg", "jpeg"], key="enc_file")
        password = st.text_input(
            "Password",
            type="password",
            key="enc_pw",
            help="Keep it somewhere safe. A lost password can't be recovered.",
        )
        if st.button("Lock photo", type="primary", key="enc_btn"):
            if file is None or password == "":
                st.warning("Choose a photo and enter a password first.")
            else:
                img = Image.open(file)
                out, data = encrypt(img, password)
                col1, col2 = st.columns(2)
                col1.image(img, caption="Your photo")
                col2.image(out, caption="Locked copy")
                before = average_entropy(np.array(img.convert("RGB")))
                after = average_entropy(np.array(out))
                st.write(f"Randomness went from {before:.2f} to {after:.2f}. The highest possible value is 8.")
                st.download_button("Download locked image", data, "encrypted.png", "image/png", type="primary")
                st.caption("Keep this file and your password. When you share it, send it as a document or by email, because chat apps can damage it.")
    else:
        file2 = st.file_uploader("Locked image (PNG)", type=["png"], key="dec_file")
        password2 = st.text_input("Password", type="password", key="dec_pw")
        if st.button("Unlock photo", type="primary", key="dec_btn"):
            if file2 is None or password2 == "":
                st.warning("Choose the locked image and enter the password first.")
            else:
                img2 = Image.open(file2)
                if "salt" not in img2.info or "nonce" not in img2.info:
                    st.error("This file wasn't made by this tool. Upload the encrypted.png you downloaded earlier.")
                else:
                    out2, data2 = decrypt(img2, password2)
                    col1, col2 = st.columns(2)
                    col1.image(img2, caption="Locked image")
                    col2.image(out2, caption="Result")
                    st.write("If the result looks like static, the password is wrong.")
                    st.download_button("Download unlocked image", data2, "decrypted.png", "image/png", type="primary")

st.write("")
st.caption("Project, built with Python and Streamlit.")
