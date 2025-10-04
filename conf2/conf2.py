import argparse
import csv
import json
import time
import base64
import sys


class VFSNode:
    def __init__(self, name, is_dir=False, data=None):
        self.name = name
        self.is_dir = is_dir
        self.data = data
        self.children = {}

    def add_child(self, child):
        self.children[child.name] = child

    def get_child(self, name):
        return self.children.get(name)

    def list_children(self):
        return sorted(self.children.keys())


class VirtualFileSystem:
    def __init__(self):
        self.root = VFSNode("/", is_dir=True)

    def add_entry(self, path, type_, content):
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts[:-1]:
            if part not in node.children:
                node.children[part] = VFSNode(part, is_dir=True)
            node = node.children[part]
        name = parts[-1] if parts else "/"
        if type_ == "dir":
            node.children[name] = VFSNode(name, is_dir=True)
        else:
            data = ""
            if content:
                try:
                    data = base64.b64decode(content).decode("utf-8")
                except Exception:
                    data = content
            node.children[name] = VFSNode(name, is_dir=False, data=data)

    def find_node(self, path):
        if path == "/" or path == "":
            return self.root
        parts = [p for p in path.strip("/").split("/") if p]
        node = self.root
        for part in parts:
            node = node.get_child(part)
            if node is None:
                return None
        return node


def load_vfs_from_csv(vfs_path):
    vfs = VirtualFileSystem()
    try:
        with open(vfs_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row.get("path")
                type_ = row.get("type")
                content = row.get("content", "")
                if not path or not type_:
                    raise ValueError("Missing required fields in CSV")
                vfs.add_entry(path, type_, content)
        return vfs
    except Exception as e:
        raise RuntimeError(f"Error loading VFS: {e}")


class VFSShell:
    def __init__(self, vfs, vfs_name="sasha"):
        self.vfs = vfs
        self.vfs_name = vfs_name
        self.current_path = "/"
        self.start_time = time.time()

    def get_prompt(self):
        return f"{self.vfs_name}:{self.current_path}$ "

    def resolve_path(self, path):
        if path.startswith("/"):
            full_path = path
        else:
            if self.current_path == "/":
                full_path = "/" + path
            else:
                full_path = self.current_path + "/" + path
        full_path = full_path.replace("//", "/")
        return full_path

    def cmd_ls(self, args):
        node = self.vfs.find_node(self.current_path)
        if node and node.is_dir:
            return "  ".join(node.list_children())
        return f"ls: cannot access '{self.current_path}'"

    def cmd_cd(self, args):
        if not args:
            return "cd: missing argument"
        dest = self.resolve_path(args[0])
        node = self.vfs.find_node(dest)
        if not node:
            return f"cd: Path '{dest}' not found in VFS"
        if not node.is_dir:
            return f"cd: '{dest}' is not a directory"
        self.current_path = dest
        return ""

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
        path = self.resolve_path(args[0])
        parts = [p for p in path.strip("/").split("/") if p]
        if not parts:
            return "touch: invalid path"
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        parent = self.vfs.find_node(parent_path)
        if not parent or not parent.is_dir:
            return f"touch: cannot create file in '{parent_path}'"
        name = parts[-1]
        parent.children[name] = VFSNode(name, is_dir=False, data="")
        return ""

    def cmd_mv(self, args):
        if len(args) < 2:
            return "mv: usage: mv <src> <dst>"
        src_path = self.resolve_path(args[0])
        dst_path = self.resolve_path(args[1])
        src_node = self.vfs.find_node(src_path)
        if not src_node:
            return f"mv: Source '{src_path}' not found"
        src_parts = [p for p in src_path.strip('/').split('/') if p]
        dst_parts = [p for p in dst_path.strip('/').split('/') if p]
        if not src_parts:
            return "mv: invalid source"
        src_parent_path = "/" + "/".join(src_parts[:-1]) if len(src_parts) > 1 else "/"
        src_parent = self.vfs.find_node(src_parent_path)
        dst_parent_path = "/" + "/".join(dst_parts[:-1]) if len(dst_parts) > 1 else "/"
        dst_parent = self.vfs.find_node(dst_parent_path)
        if not dst_parent or not dst_parent.is_dir:
            return f"mv: Destination '{dst_parent_path}' not found or not a directory"
        name = dst_parts[-1]
        dst_parent.children[name] = src_node
        del src_parent.children[src_parts[-1]]
        src_node.name = name
        return ""

    def cmd_cat(self, args):
        if not args:
            return "cat: missing file name"
        path = self.resolve_path(args[0])
        node = self.vfs.find_node(path)
        if not node:
            return f"cat: '{path}' not found"
        if node.is_dir:
            return f"cat: '{path}' is a directory"
        return node.data if node.data else ""

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
        elif command == "cat":
            return self.cmd_cat(args)
        elif command == "exit":
            return self.cmd_exit(args)
        else:
            return f"{self.vfs_name}: {command}: command not found"


class TerminalEmulator:
    def __init__(self, vfs, vfs_name="sasha", start_script=None):
        self.shell = VFSShell(vfs=vfs, vfs_name=vfs_name)
        self.start_script = start_script

    def _execute_line(self, line):
        line = line.strip()
        if not line or line.startswith("#"):
            return False
        print(f"{self.shell.get_prompt()}{line}")
        cmd_parts = line.split()
        if not cmd_parts:
            return False
        cmd, args = cmd_parts[0], cmd_parts[1:]
        result = self.shell.run_command(cmd, args)
        if result:
            print(result)
        if result == "exit":
            return True
        return False

    def start(self, interactive=True):
        if self.start_script:
            try:
                with open(self.start_script, "r", encoding="utf-8") as f:
                    for line in f:
                        should_exit = self._execute_line(line)
                        if should_exit:
                            return
            except Exception as e:
                print(f"Error reading start script: {e}")
        if interactive:
            while True:
                try:
                    user_input = input(self.shell.get_prompt())
                except EOFError:
                    print("")
                    break
                cmd, args = user_input.strip().split()[0], user_input.strip().split()[1:]
                result = self.shell.run_command(cmd, args)
                if result:
                    print(result)
                if result == "exit":
                    break


def load_json_config(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "vfs_path": data.get("vfs_path"),
                "start_script": data.get("start_script"),
            }
    except Exception as e:
        print(f"Error loading config file '{config_path}': {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="VFS Terminal Emulator")
    parser.add_argument("--vfs-path", help="Path to CSV VFS file")
    parser.add_argument("--start-script", help="Path to start script")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--no-interactive", action="store_true", help="Run without interactive shell")
    args = parser.parse_args()

    if args.config:
        cfg = load_json_config(args.config)
        if cfg.get("vfs_path"):
            args.vfs_path = cfg["vfs_path"]
        if cfg.get("start_script"):
            args.start_script = cfg["start_script"]

    if args.vfs_path:
        try:
            vfs = load_vfs_from_csv(args.vfs_path)
        except Exception as e:
            print(e)
            sys.exit(1)
    else:
        vfs = VirtualFileSystem()

    emulator = TerminalEmulator(vfs=vfs, vfs_name="sasha", start_script=args.start_script)
    emulator.start(interactive=not args.no_interactive)


if __name__ == "__main__":
    main()
