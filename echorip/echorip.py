import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import sys
import os
import threading
import re
from datetime import datetime
import glob

# Paths
base_output_dir = os.path.join(os.path.expanduser("~"), "Music", "EchoRip")
mp3_dir = os.path.join(base_output_dir, "MP3")
mp4_dir = os.path.join(base_output_dir, "MP4")
history_file = os.path.join(base_output_dir, "download_history.txt")

# Ensure folders exist
os.makedirs(mp3_dir, exist_ok=True)
os.makedirs(mp4_dir, exist_ok=True)

def update_progress(line):
    match = re.search(r"\[download\]\s+(\d{1,3}\.\d+)%", line)
    if match:
        percent = match.group(1)
        status_label.config(text=f"🎧 EchoRip: {percent}%")
        root.update()

def get_latest_file_size(directory, extension):
    files = glob.glob(os.path.join(directory, f"*.{extension}"))
    if not files:
        return "N/A"
    latest_file = max(files, key=os.path.getctime)
    size_mb = os.path.getsize(latest_file) / (1024 * 1024)
    return f"{size_mb:.2f} MB"

def write_history(url, mode, output_file):
    extension = "mp3" if mode == "mp3" else "mp4"
    directory = mp3_dir if mode == "mp3" else mp4_dir
    file_size = get_latest_file_size(directory, extension)
    entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mode.upper()} - {url} --> {output_file} ({file_size})\n"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(entry)
    load_history()

def load_history():
    history_display.config(state="normal")
    history_display.delete(1.0, tk.END)
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history_display.insert(tk.END, f.read())
    else:
        history_display.insert(tk.END, "No history yet.")
    history_display.config(state="disabled")

def run_download(url, mode):
    output_template = os.path.join(mp3_dir if mode == "mp3" else mp4_dir, "%(title)s.%(ext)s")

    if mode == "mp3":
        command = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--embed-thumbnail",
            "--embed-metadata",
            "--write-thumbnail",
            "-o", output_template,
            url
        ]
    else:
        command = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "--merge-output-format", "mp4",
            "--embed-thumbnail",
            "--embed-metadata",
            "--write-thumbnail",
            "-o", output_template,
            url
        ]

    try:
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            update_progress(line)

        process.wait()

        if process.returncode == 0:
            status_label.config(text=f"✅ EchoRip: {mode.upper()} Download complete!")
            write_history(url, mode, output_template)
            messagebox.showinfo("EchoRip", f"🎉 Your {mode.upper()} has been downloaded successfully!")
        else:
            status_label.config(text=f"❌ EchoRip: {mode.upper()} Download failed.")
            messagebox.showerror("EchoRip", "Something went wrong during download.")
    except Exception as e:
        status_label.config(text=f"❌ EchoRip: {mode.upper()} Failed")
        messagebox.showerror("EchoRip", str(e))

def start_download():
    url = url_entry.get().strip()
    mode = mode_var.get()
    if not url:
        messagebox.showwarning("Missing URL", "Please enter a YouTube URL.")
        return
    status_label.config(text=f"🎧 EchoRip: Starting {mode.upper()} download...")
    threading.Thread(target=run_download, args=(url, mode), daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("EchoRip - MP3 / MP4 Downloader with File Size")
root.geometry("540x510")
root.resizable(False, False)

tk.Label(root, text="Paste YouTube URL:", font=("Arial", 12)).pack(pady=(10, 5))
url_entry = tk.Entry(root, width=65, font=("Arial", 10))
url_entry.pack(pady=5)

mode_var = tk.StringVar(value="mp3")
mode_frame = tk.Frame(root)
tk.Label(mode_frame, text="Choose format:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
tk.Radiobutton(mode_frame, text="MP3", variable=mode_var, value="mp3", font=("Arial", 10)).pack(side=tk.LEFT)
tk.Radiobutton(mode_frame, text="MP4", variable=mode_var, value="mp4", font=("Arial", 10)).pack(side=tk.LEFT)
mode_frame.pack(pady=5)

download_btn = tk.Button(root, text="Download", command=start_download, font=("Arial", 11), bg="#4CAF50", fg="white")
download_btn.pack(pady=10)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

tk.Label(root, text="📜 Download History (includes file size)", font=("Arial", 11, "bold")).pack(pady=(10, 5))
history_display = scrolledtext.ScrolledText(root, width=65, height=12, state="disabled", font=("Courier", 9))
history_display.pack(padx=10, pady=(0, 10))

load_history()

root.mainloop()

