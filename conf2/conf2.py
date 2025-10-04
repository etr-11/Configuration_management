import argparse
import os
import sys
import csv
import base64
import time

class MemoryVFS:
    def __init__(self):
        self.fs = {"type": "dir", "children": {}}

    def add_entry(self, path, entry_type, content=None):
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.fs
        for p in parts[:-1]:
            node = node["children"].setdefault(p, {"type": "dir", "children": {}})
        name = parts[-1] if parts else "/"
        if entry_type == "dir":
            node["children"][name] = {"type": "dir", "children": {}}
        else:
            node["children"][name] = {"type": "file", "content": base64.b64decode(content) if content else b""}

    def get_node(self, path):
        if path == "/":
            return self.fs
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.fs
        for p in parts:
            if "children" not in node or p not in node["children"]:
                raise FileNotFoundError(f"Path '{path}' not found in VFS")
            node = node["children"][p]
        return node

    def list_dir(self, path):
        node = self.get_node(path)
        if node["type"] != "dir":
            raise NotADirectoryError(f"Path '{path}' is not a directory")
        return list(node["children"].keys())

    def make_file(self, path):
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            raise ValueError("Invalid path")
        node = self.fs
        for p in parts[:-1]:
            if p not in node["children"]:
                node["children"][p] = {"type": "dir", "children": {}}
            node = node["children"][p]
        name = parts[-1]
        node["children"][name] = {"type": "file", "content": b""}

    def move_entry(self, src, dst):
        src_parts = [p for p in src.strip("/").split("/") if p]
        dst_parts = [p for p in dst.strip("/").split("/") if p]
        if not src_parts or not dst_parts:
            raise ValueError("Invalid source or destination path")
        src_parent = self.fs
        for p in src_parts[:-1]:
            src_parent = src_parent["children"][p]
        src_name = src_parts[-1]
        if src_name not in src_parent["children"]:
            raise FileNotFoundError(f"Source '{src}' not found")
        entry = src_parent["children"].pop(src_name)
        dst_parent = self.fs
        for p in dst_parts[:-1]:
            dst_parent = dst_parent["children"].setdefault(p, {"type": "dir", "children": {}})
        dst_name = dst_parts[-1]
        dst_parent["children"][dst_name] = entry

def load_vfs_from_csv(csv_path):
    vfs = MemoryVFS()
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row["path"]
                entry_type = row["type"]
                content = row.get("content", "")
                vfs.add_entry(path, entry_type, content)
        return vfs
    except FileNotFoundError:
        raise FileNotFoundError(f"VFS CSV '{csv_path}' not found")
    except Exception as e:
        raise ValueError(f"Error loading VFS: {e}")

def create_default_vfs():
    vfs = MemoryVFS()
    vfs.add_entry("/", "dir")
    vfs.add_entry("/readme.txt", "file", base64.b64encode(b"Welcome to default VFS").decode())
    vfs.add_entry("/folder1", "dir")
    vfs.add_entry("/folder1/test.txt", "file", base64.b64encode(b"Some data").decode())
    return vfs

class VFSShell:
    def __init__(self, vfs_name="sasha", vfs=None):
        self.vfs_name = vfs_name
        self.current_dir = "/"
        self.vfs = vfs or create_default_vfs()
        self.start_time = time.time()

    def get_prompt(self):
        return f"{self.vfs_name}:{self.current_dir}$ "

    def parse_command(self, input_string):
        parts = input_string.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]

    def resolve_path(self, dest):
        if dest.startswith("/"):
            return os.path.normpath(dest).replace("\\", "/")
        return os.path.normpath(os.path.join(self.current_dir, dest)).replace("\\", "/")

    def cmd_ls(self, args):
        path = self.current_dir if not args else self.resolve_path(args[0])
        try:
            entries = self.vfs.list_dir(path)
            return "  ".join(entries)
        except Exception as e:
            return f"ls: {e}"

    def cmd_cd(self, args):
        if not args:
            return "cd: missing argument"
        dest = self.resolve_path(args[0])
        try:
            node = self.vfs.get_node(dest)
            if node["type"] != "dir":
                return f"cd: '{dest}' is not a directory"
            self.current_dir = dest
            return ""
        except Exception as e:
            return f"cd: {e}"

    def cmd_rev(self, args):
        if not args:
            return "rev: missing argument"
        return " ".join(word[::-1] for word in args)

    def cmd_uptime(self, args):
        elapsed = time.time() - self.start_time
        return f"Uptime: {elapsed:.2f} seconds"

    def cmd_touch(self, args):
        if not args:
            return "touch: missing file name"
        try:
            for f in args:
                path = self.resolve_path(f)
                self.vfs.make_file(path)
            return ""
        except Exception as e:
            return f"touch: {e}"

    def cmd_mv(self, args):
        if len(args) != 2:
            return "mv: usage: mv <src> <dst>"
        try:
            src = self.resolve_path(args[0])
            dst = self.resolve_path(args[1])
            self.vfs.move_entry(src, dst)
            return ""
        except Exception as e:
            return f"mv: {e}"

    def cmd_exit(self, args):
        return "exit"

    def run_command(self, command, args):
        if command == "ls":
            return self.cmd_ls(args)
        elif command == "cd":
            return self.cmd_cd(args)
        elif command == "rev":
            return self.cmd_rev(args)
        elif command == "uptime":
            return self.cmd_uptime(args)
        elif command == "touch":
            return self.cmd_touch(args)
        elif command == "mv":
            return self.cmd_mv(args)
        elif command == "exit":
            return self.cmd_exit(args)
        else:
            return f"{self.vfs_name}: {command}: command not found"

class TerminalEmulator:
    def __init__(self, vfs_name="sasha", vfs_path=None, start_script=None):
        try:
            self.vfs = load_vfs_from_csv(vfs_path) if vfs_path else create_default_vfs()
        except Exception as e:
            print(f"Error loading VFS: {e}")
            self.vfs = create_default_vfs()
        self.shell = VFSShell(vfs_name=vfs_name, vfs=self.vfs)
        self.start_script = start_script

    def _execute_line(self, line):
        line = line.rstrip("\n")
        prompt = self.shell.get_prompt()
        print(f"{prompt}{line}")
        command, args = self.shell.parse_command(line)
        if command is None:
            return False
        result = self.shell.run_command(command, args)
        if result != "":
            print(result)
        if result == "exit":
            return True
        return False

    def start(self, interactive=True):
        if self.start_script:
            if not os.path.isfile(self.start_script):
                print(f"Start script '{self.start_script}' not found. Skipping.")
            else:
                try:
                    with open(self.start_script, "r", encoding="utf-8") as f:
                        for raw_line in f:
                            line = raw_line.strip()
                            if not line or line.startswith("#"):
                                continue
                            try:
                                should_exit = self._execute_line(line)
                                if should_exit:
                                    break
                            except Exception as e:
                                print(f"(error executing line, skipped): {e}")
                                continue
                except Exception as e:
                    print(f"Error reading start script: {e}")

        if interactive:
            try:
                while True:
                    try:
                        user_input = input(self.shell.get_prompt())
                    except EOFError:
                        print("")
                        break
                    command, args = self.shell.parse_command(user_input)
                    if command is None:
                        continue
                    result = self.shell.run_command(command, args)
                    if result != "":
                        print(result)
                    if result == "exit":
                        break
            except KeyboardInterrupt:
                print("\nInterrupted. Exiting.")

def main():
    parser = argparse.ArgumentParser(description="VFS Terminal Emulator")
    parser.add_argument("--vfs-path", help="Physical VFS path")
    parser.add_argument("--start-script", help="Path to start script file")
    parser.add_argument("--no-interactive", action="store_true", help="Do not enter interactive mode after running start script")
    args = parser.parse_args()
    emulator = TerminalEmulator(vfs_name="sasha", vfs_path=args.vfs_path, start_script=args.start_script)
    emulator.start(interactive=not args.no_interactive)

if __name__ == "__main__":
    main()
