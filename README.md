# Fat32_virtual_disk
This project simulates a FAT32-like virtual disk using Python. It provides a simple command-line interface to manage files within a virtual disk image (.img file), including:

 Creating and formatting a virtual disk

 Writing, reading, updating, and deleting files

 Viewing disk usage stats

 Cloning the disk

 Copying and pasting file content via clipboard

 Deleting the disk file

⚠️ Note: This is a simplified emulation and not a fully bootable or OS-mountable FAT32 system.

 How to Run
1. Install Required Package
You only need pyperclip for clipboard support:

bash:
pip install pyperclip
2. Run the Program
bash:
python your_script_name.py
3. Use the Menu
You'll see an interactive menu like:
=== Virtual FAT32 Disk Menu ===
1. Create New Virtual Disk
2. Format Disk
3. Write File
4. Read File
...
Just type the option number to perform actions on your virtual FAT32 disk.

 Files & Storage Structure
The disk is saved as a binary file (.img) on your system.

Each file in the virtual disk:

Has a 40-byte entry: 32 bytes name, 4 bytes cluster, 4 bytes size

Is stored in 1 cluster (512 bytes)

The FAT table manages free/used clusters.

Features
Single-cluster file writing

In-memory FAT table

Simple root directory support

Disk statistics

Clipboard support (copy/paste text files)

Persistent storage via .img files

 Limitations
Only handles root directory, no subfolders

Files limited to 512 bytes

Not mountable by OS (not a real FAT32 partition)
