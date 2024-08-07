import subprocess
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import time
import re

def check_tshark():
    try:
        subprocess.run(['tshark', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def add_tshark_to_path():
    wireshark_path = r"C:\Program Files\Wireshark"
    if not os.path.exists(wireshark_path):
        return False

    current_path = os.environ.get("PATH", "")
    if wireshark_path not in current_path:
        os.environ["PATH"] = f"{wireshark_path};{current_path}"
        subprocess.run(['setx', 'PATH', os.environ["PATH"]], shell=True)
        return True

    return False

def get_interfaces():
    result = subprocess.run(['tshark', '-D'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    interfaces = result.stdout.split('\n')
    parsed_interfaces = []

    for iface in interfaces:
        match = re.search(r'\((.*?)\)$', iface)
        if match:
            parsed_interfaces.append(match.group(1))
    
    return [iface for iface in parsed_interfaces if iface]

def start_recording(interface, output_dir, filename):
    timestamp = time.strftime("%d-%m-%Y-%H-%M")
    full_filename = os.path.join(output_dir, f"{filename}_{timestamp}.pcap")
    process = subprocess.Popen(['tshark', '-i', interface.split('.')[0], '-w', full_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process, full_filename

def stop_recording(process):
    process.terminate()
    process.wait()

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        output_dir_var.set(directory)

def start_recording_thread():
    interface = interface_var.get()
    output_dir = output_dir_var.get()
    filename = filename_var.get()
    if not interface or not output_dir or not filename:
        messagebox.showerror("Error", "Please select an interface, output directory, and filename.")
        return

    start_button.config(state='disabled', bg='green')
    stop_button.config(state='normal')

    def run():
        global tshark_process, full_filename
        try:
            tshark_process, full_filename = start_recording(interface, output_dir, filename)
        except Exception as e:
            print(f"Error starting recording: {e}")
            messagebox.showerror("Error", f"Failed to start recording: {e}")
            start_button.config(state='normal', bg='SystemButtonFace')
            stop_button.config(state='disabled')

    threading.Thread(target=run).start()

def stop_recording_thread():
    if tshark_process:
        stop_button.config(state='disabled')
        start_button.config(state='normal', bg='SystemButtonFace')
        def run():
            try:
                stop_recording(tshark_process)
                messagebox.showinfo("Recording Stopped", f"Recording saved to: {full_filename}")
            except Exception as e:
                print(f"Error stopping recording: {e}")
                messagebox.showerror("Error", f"Failed to stop recording: {e}")

        threading.Thread(target=run).start()

if __name__ == "__main__":
    if not check_tshark():
        if not add_tshark_to_path():
            messagebox.showerror("Error", "TSHARK is not installed. Please reinstall Wireshark and ensure TSHARK is installed.")
            sys.exit(1)
        else:
            messagebox.showinfo("Path Added", "Wireshark path added to system environment variables. Please restart the script.")
            sys.exit(0)
    
    interfaces = get_interfaces()
    if not interfaces:
        messagebox.showerror("Error", "No network interfaces found. Exiting...")
        sys.exit(1)

    tshark_process = None
    full_filename = ""

    root = tk.Tk()
    root.title("Tshark Network Recorder")

    tk.Label(root, text="Select Network Interface:").pack(pady=5)
    
    interface_var = tk.StringVar()
    combo = ttk.Combobox(root, textvariable=interface_var, values=interfaces)
    combo.pack(pady=5)

    tk.Label(root, text="Select Output Directory:").pack(pady=5)
    
    output_dir_var = tk.StringVar()
    output_dir_entry = tk.Entry(root, textvariable=output_dir_var, width=50)
    output_dir_entry.pack(pady=5)
    tk.Button(root, text="Browse...", command=browse_directory).pack(pady=5)

    tk.Label(root, text="Enter Filename Prefix:").pack(pady=5)
    
    filename_var = tk.StringVar()
    filename_entry = tk.Entry(root, textvariable=filename_var, width=50)
    filename_entry.pack(pady=5)

    start_button = tk.Button(root, text="Start Recording", command=start_recording_thread)
    start_button.pack(pady=5)

    stop_button = tk.Button(root, text="Stop Recording", command=stop_recording_thread, state='disabled')
    stop_button.pack(pady=5)

    root.mainloop()

