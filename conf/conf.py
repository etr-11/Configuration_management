class VFSShell:
    def __init__(self, vfs_name="sasha"):
        self.vfs_name = vfs_name
        self.current_dir = "/"
    
    def get_prompt(self):
        return f"{self.vfs_name}:{self.current_dir}$ "
    
    def parse_command(self, input_string):
        parts = input_string.strip().split()
        if not parts:
            return None, []
        return parts[0], parts[1:]
    
    def cmd_ls(self, args):
        return "ls called with arguments: {}".format(args)
    
    def cmd_cd(self, args):
        if not args:
            return "cd: missing argument"
        return "cd called with arguments: {}".format(args)
    
    def cmd_exit(self, args):
        return "exit"
    
    def run_command(self, command, args):
        if command == "ls":
            return self.cmd_ls(args)
        elif command == "cd":
            return self.cmd_cd(args)
        elif command == "exit":
            return self.cmd_exit(args)
        else:
            return f"{self.vfs_name}: {command}: command not found"

class TerminalEmulator:
    def __init__(self):
        self.shell = VFSShell("sasha")
    
    def start(self, script=None):
        while True:
            user_input = input(self.shell.get_prompt())
            command, args = self.shell.parse_command(user_input)
            if command is None:
                continue
            result = self.shell.run_command(command, args)
            print(result)
            if result == "exit":
                break

def main():
    terminal = TerminalEmulator()
    terminal.start()

if __name__ == "__main__":
    main()