import os
import pyperclip





class FAT32VirtualDisk:
    def __init__(self, filename='low_level_disk.img', size=1024 * 1024):
        self.filename = filename
        self.size = size
        self.cluster_size = 512
        self.fat_entries = self.size // self.cluster_size
        self.boot_sector_size = 512
        self.fat_size = self.fat_entries * 4
        self.fat_offset = self.boot_sector_size
        self.data_offset = self.fat_offset + self.fat_size
        self.disk = bytearray(self.size)
        self.root_dir_cluster = 2
        self.format_disk()
        self.save() 

    def format_disk(self):
        self.disk = bytearray(self.size)
        self._init_boot_sector()
        self._init_fat_table()
        self._init_root_directory()
        print("[✓] Disk formatted.")

    def _init_boot_sector(self):
        bs = b'FAT32    ' + b'\x00' * (self.boot_sector_size - 8)
        self.disk[0:self.boot_sector_size] = bs

    def _init_fat_table(self):
        for i in range(self.fat_entries):
            offset = self.fat_offset + i * 4
            self.disk[offset:offset+4] = (0x00000000).to_bytes(4, 'little')

    def _init_root_directory(self):
        self._allocate_cluster(self.root_dir_cluster)

    def _allocate_cluster(self, cluster):
        offset = self.fat_offset + cluster * 4
        self.disk[offset:offset+4] = (0xFFFFFFFF).to_bytes(4, 'little')

    def _find_free_cluster(self):
        for i in range(2, self.fat_entries):
            offset = self.fat_offset + i * 4
            entry = int.from_bytes(self.disk[offset:offset+4], 'little')
            if entry == 0x00000000:
                return i
        return None

    def _add_directory_entry(self, name, cluster, size):
        entry = name.ljust(32)[:32].encode('utf-8') + cluster.to_bytes(4, 'little') + size.to_bytes(4, 'little')
        dir_offset = self.data_offset + self.root_dir_cluster * self.cluster_size
        for i in range(0, self.cluster_size, 40):
            if self.disk[dir_offset+i:dir_offset+i+40] == b'\x00' * 40:
                self.disk[dir_offset+i:dir_offset+i+40] = entry
                break

    def _update_directory_entry(self, name, cluster, size):
        dir_offset = self.data_offset + self.root_dir_cluster * self.cluster_size
        for i in range(0, self.cluster_size, 40):
            entry = self.disk[dir_offset+i:dir_offset+i+40]
            existing_name = entry[:32].decode('utf-8', errors='ignore').strip()
            if existing_name == name:
                new_entry = name.ljust(32)[:32].encode('utf-8') + cluster.to_bytes(4, 'little') + size.to_bytes(4, 'little')
                self.disk[dir_offset+i:dir_offset+i+40] = new_entry
                return True
        return False

    def write_file(self, filename, content):
        cluster = self._find_free_cluster()
        if cluster is None:
            raise Exception("No free clusters available.")
        self._allocate_cluster(cluster)
        cluster_offset = self.data_offset + cluster * self.cluster_size
        encoded = content.encode()
        if len(encoded) > self.cluster_size:
            raise Exception("File too large for one cluster.")
        self.disk[cluster_offset:cluster_offset+len(encoded)] = encoded
        self._add_directory_entry(filename, cluster, len(encoded))
        print(f"[+] File '{filename}' written.")

    def update_file(self, filename, new_content):
        dir_offset = self.data_offset + self.root_dir_cluster * self.cluster_size
        for i in range(0, self.cluster_size, 40):
            entry = self.disk[dir_offset+i:dir_offset+i+40]
            name = entry[:32].decode('utf-8', errors='ignore').strip()
            if name == filename:
                old_cluster = int.from_bytes(entry[32:36], 'little')
                new_encoded = new_content.encode()
                if len(new_encoded) > self.cluster_size:
                    raise Exception("New content too large for one cluster.")

                new_cluster = self._find_free_cluster()
                if new_cluster is None:
                    raise Exception("No free clusters available.")
                self._allocate_cluster(new_cluster)
                cluster_offset = self.data_offset + new_cluster * self.cluster_size
                self.disk[cluster_offset:cluster_offset+len(new_encoded)] = new_encoded
                self._update_directory_entry(filename, new_cluster, len(new_encoded))
                print(f"[🔁] File '{filename}' updated.")
                return
        print(f"[!] File '{filename}' not found.")

    def read_file(self, filename):
        dir_offset = self.data_offset + self.root_dir_cluster * self.cluster_size
        for i in range(0, self.cluster_size, 40):
            entry = self.disk[dir_offset+i:dir_offset+i+40]
            if entry[:32] == b'\x00' * 32:
                continue
            name = entry[:32].decode('utf-8', errors='ignore').strip()
            if name == filename:
                cluster = int.from_bytes(entry[32:36], 'little')
                size = int.from_bytes(entry[36:40], 'little')
                data_offset = self.data_offset + cluster * self.cluster_size
                content = self.disk[data_offset:data_offset+size]
                print(f"[📖] Content of '{filename}':\n{content.decode('utf-8', errors='ignore')}")
                return
        print(f"[!] File '{filename}' not found.")

    def show_stats(self):
        used = 0
        for i in range(2, self.fat_entries):
            offset = self.fat_offset + i * 4
            entry = int.from_bytes(self.disk[offset:offset+4], 'little')
            if entry != 0:
                used += 1
        total = self.fat_entries - 2
        print(f"[📊] Disk Usage: {used}/{total} clusters used.")

    def save(self):
        with open(self.filename, 'wb') as f:
            f.write(self.disk)
        print(f"[💾] Disk saved to '{self.filename}'.")

    def clone_disk(self, clone_name):
        self.save()
        with open(self.filename, 'rb') as src, open(clone_name, 'wb') as dst:
            dst.write(src.read())
        print(f"[🌀] Disk cloned to '{clone_name}'.")
    def delete_file(self, filename):
        dir_offset = self.data_offset + self.root_dir_cluster * self.cluster_size
        for i in range(0, self.cluster_size, 40):
            entry = self.disk[dir_offset+i:dir_offset+i+40]
            name = entry[:32].decode('utf-8', errors='ignore').strip()
            if name == filename:
                cluster = int.from_bytes(entry[32:36], 'little')
                # Clear FAT entry
                fat_entry_offset = self.fat_offset + cluster * 4
                self.disk[fat_entry_offset:fat_entry_offset+4] = (0x00000000).to_bytes(4, 'little')
                # Clear data
                data_offset = self.data_offset + cluster * self.cluster_size
                self.disk[data_offset:data_offset+self.cluster_size] = b'\x00' * self.cluster_size
                # Clear directory entry
                self.disk[dir_offset+i:dir_offset+i+40] = b'\x00' * 40
                print(f"[🗑️] File '{filename}' deleted.")
                return
        print(f"[!] File '{filename}' not found.")
    def delete_disk(self):
        try:
            os.remove(self.filename)
            print(f"[⚠️] Disk file '{self.filename}' deleted from filesystem.")
        except FileNotFoundError:
            print(f"[!] Disk file '{self.filename}' not found.")

# === Interactive CLI ===
def main():
    disk = None

    while True:
        print("\n=== Virtual FAT32 Disk Menu ===")
        print("1. Create New Virtual Disk")
        print("2. Format Disk")
        print("3. Write File")
        print("4. Read File")
        print("5. Update File")
        print("6. Show Statistics")
        print("7. Save Disk")
        print("8. Clone Disk")
        print("9. Copy File Content to Clipboard")
        print("10. Paste Clipboard Content as New File")
        print("11. Delete File")
        print("12. Delete Disk File")

        print("0. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            filename = input("Enter disk filename: ")
            disk = FAT32VirtualDisk(filename=filename)
            print(f"[+] Virtual disk '{filename}' created.")

        elif choice == "2":
            if disk:
                disk.format_disk()
            else:
                print("[!] No disk created yet.")

        elif choice == "3":
            if disk:
                name = input("Enter file name: ")
                content = input("Enter content: ")
                disk.write_file(name, content)
            else:
                print("[!] No disk created yet.")

        elif choice == "4":
            if disk:
                name = input("Enter file name to read: ")
                disk.read_file(name)
            else:
                print("[!] No disk created yet.")

        elif choice == "5":
            if disk:
                name = input("Enter file name to update: ")
                content = input("Enter new content: ")
                disk.update_file(name, content)
            else:
                print("[!] No disk created yet.")

        elif choice == "6":
            if disk:
                disk.show_stats()
            else:
                print("[!] No disk created yet.")

        elif choice == "7":
            if disk:
                disk.save()
            else:
                print("[!] No disk created yet.")

        elif choice == "8":
            if disk:
                clone_name = input("Enter clone filename (e.g. clone.img): ")
                disk.clone_disk(clone_name)
            else:
                print("[!] No disk created yet.")

        elif choice == "9":
            if disk:
                name = input("Enter file name to copy: ")
                dir_offset = disk.data_offset + disk.root_dir_cluster * disk.cluster_size
                found = False
                for i in range(0, disk.cluster_size, 40):
                    entry = disk.disk[dir_offset+i:dir_offset+i+40]
                    entry_name = entry[:32].decode('utf-8', errors='ignore').strip()
                    if entry_name == name:
                        cluster = int.from_bytes(entry[32:36], 'little')
                        size = int.from_bytes(entry[36:40], 'little')
                        data_offset = disk.data_offset + cluster * disk.cluster_size
                        content = disk.disk[data_offset:data_offset+size].decode('utf-8', errors='ignore')
                        pyperclip.copy(content)
                        print(f"[📋] File '{name}' content copied to clipboard.")
                        found = True
                        break
                if not found:
                    print(f"[!] File '{name}' not found.")
            else:
                print("[!] No disk created yet.")

        elif choice == "10":
            if disk:
                name = input("Enter new file name to paste into: ")
                content = pyperclip.paste()
                if content:
                    disk.write_file(name, content)
                    print(f"[📥] Clipboard content pasted as '{name}'.")
                else:
                    print("[!] Clipboard is empty.")
            else:
                print("[!] No disk created yet.")
        elif choice == "11":
            if disk:
                name = input("Enter file name to delete: ")
                disk.delete_file(name)
            else:
                print("[!] No disk created yet.")

        elif choice == "12":
            if disk:
                confirm = input(f"Are you sure you want to delete the disk file '{disk.filename}'? (yes/no): ").strip().lower()
                if confirm == "yes":
                    disk.delete_disk()
                    disk = None
                else:
                    print("[i] Deletion cancelled.")
            else:
                print("[!] No disk created yet.")

        elif choice == "0":
            print("Exiting...")
            break

        else:
            print("[!] Invalid choice. Try again.")


if __name__ == "__main__":
    main()
