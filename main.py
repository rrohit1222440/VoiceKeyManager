import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import random
import os
import sqlite3
import speech_recognition as sr
import sounddevice as sd
import numpy as np
import io
import scipy.io.wavfile

GRID_SIZE = 3
IMAGE_PATH = "saved_user_image.png"
secret_coords = []
auth_coords = []
puzzle_images = []

#VOICE LOGIN#
def listen_for_voice_password():
    recognizer = sr.Recognizer()
    voice_password = "unlock my vault"

    try:
        fs = 16000
        duration = 4
        print("🎙️ Listening... Speak your voice password.")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        buffer = io.BytesIO()
        scipy.io.wavfile.write(buffer, fs, audio)
        buffer.seek(0)

        with sr.AudioFile(buffer) as source:
            recorded_audio = recognizer.record(source)
            text = recognizer.recognize_google(recorded_audio)
            print("You said:", text)

            if text.lower() == voice_password.lower():
                messagebox.showinfo("Voice", "Voice authentication successful!")
                show_vault_manager()
            else:
                messagebox.showerror("Voice", "Incorrect voice password.")

    except Exception as e:
        messagebox.showerror("Voice Error", str(e))


#IMAGE PUZZLE#
def open_signup_window():
    global secret_coords
    secret_coords.clear()
    path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
    if not path:
        return
    img = Image.open(path)
    img.save(IMAGE_PATH)
    setup_puzzle(signup_mode=True)

def open_login_window():
    global auth_coords
    auth_coords.clear()
    if not os.path.exists(IMAGE_PATH):
        messagebox.showerror("Error", "No saved image found. Please sign up first.")
        return
    setup_puzzle(signup_mode=False)

def setup_puzzle(signup_mode):
    win = tk.Toplevel()
    win.title("Image Puzzle")

    img = Image.open(IMAGE_PATH)
    img = img.resize((300, 300))
    piece_size = img.width // GRID_SIZE

    pieces = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            box = (col * piece_size, row * piece_size, (col+1)*piece_size, (row+1)*piece_size)
            piece = img.crop(box)
            tk_piece = ImageTk.PhotoImage(piece)
            pieces.append(tk_piece)
            puzzle_images.append(tk_piece)

    shuffled = pieces[:]
    random.shuffle(shuffled)
    coords_clicked = []

    def on_click(r, c, idx):
        coords_clicked.append((r, c))
        if len(coords_clicked) == 3:
            if signup_mode:
                global secret_coords
                secret_coords = coords_clicked[:]
                messagebox.showinfo("Saved", "Puzzle sequence saved!")
                win.destroy()
            else:
                if coords_clicked == secret_coords:
                    messagebox.showinfo("Login", "Puzzle authentication successful!")
                    win.destroy()
                    show_vault_manager()
                else:
                    messagebox.showerror("Login", "Incorrect puzzle sequence.")
                    coords_clicked.clear()

    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            idx = i * GRID_SIZE + j
            btn = tk.Button(win, image=shuffled[idx], command=lambda r=i, c=j, i=idx: on_click(r, c, i))
            btn.grid(row=i, column=j)


#PASSWORD MANAGER#
def show_vault_manager():
    manager = tk.Toplevel()
    manager.title("VaultVoice")

    tk.Label(manager, text="VaultVoice", font=("Arial", 18, "bold")).pack(pady=10)
    tk.Label(manager, text="Your password manager is unlocked.").pack(pady=5)

    tk.Label(manager, text="Website").pack()
    global website_entry
    website_entry = tk.Entry(manager)
    website_entry.pack()

    tk.Label(manager, text="Username").pack()
    global username_entry
    username_entry = tk.Entry(manager)
    username_entry.pack()

    tk.Label(manager, text="Password").pack()
    global password_entry
    password_entry = tk.Entry(manager, show="*")
    password_entry.pack()

    tk.Button(manager, text="Add Password", command=add_password).pack(pady=5)
    tk.Button(manager, text="View Vault", command=show_passwords_window).pack()


def add_password():
    website = website_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if not website or not username or not password:
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    conn = sqlite3.connect("vault.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS vault (website TEXT, username TEXT, password TEXT)")
    c.execute("INSERT INTO vault VALUES (?, ?, ?)", (website, username, password))
    conn.commit()
    conn.close()

    messagebox.showinfo("Saved", f"Saved: {website} | {username} | {password}")
    show_passwords_window()


def show_passwords_window():
    conn = sqlite3.connect("vault.db")
    c = conn.cursor()
    c.execute("SELECT website, username, password FROM vault")
    rows = c.fetchall()
    conn.close()

    vault = tk.Toplevel()
    vault.title("🔐 Vault Contents")

    tk.Label(vault, text="Your Saved Passwords", font=("Arial", 14, "bold")).pack(pady=10)

    for website, username, password in rows:
        masked_pw = "*" * len(password)
        entry = f"{website} | {username} | {masked_pw}"
        tk.Label(vault, text=entry, font=("Courier", 10)).pack(anchor="w", padx=20)


#UI LAUNCHER#
def launch_gui():
    root = tk.Tk()
    root.title("VaultVoice Login")

    tk.Label(root, text="Choose login method:", font=("Arial", 14)).pack(pady=10)
    tk.Button(root, text="Voice Recognition", command=listen_for_voice_password, width=30).pack(pady=5)
    tk.Button(root, text="Image Puzzle", command=open_login_window, width=30).pack(pady=5)
    tk.Label(root, text="--- OR ---").pack(pady=5)
    tk.Button(root, text="Sign Up with Image Puzzle", command=open_signup_window, width=30).pack(pady=5)

    root.mainloop()

launch_gui()