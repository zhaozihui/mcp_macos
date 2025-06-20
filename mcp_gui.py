import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os
import sys

class MCPGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MCP Pipe 启动器")
        self.root.geometry("600x400")

        tk.Label(root, text="MCP_ENDPOINT:").pack(anchor='w', padx=10, pady=5)
        self.endpoint_var = tk.StringVar()
        self.endpoint_entry = tk.Entry(root, textvariable=self.endpoint_var, width=80)
        self.endpoint_entry.pack(fill='x', padx=10)

        self.run_btn = tk.Button(root, text="启动 mcp_pipe.py", command=self.run_mcp_pipe)
        self.run_btn.pack(pady=10)

        self.log_text = scrolledtext.ScrolledText(root, height=18, state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)

        self.proc = None

    def run_mcp_pipe(self):
        endpoint = self.endpoint_var.get().strip()
        if not endpoint:
            messagebox.showerror("错误", "请填写 MCP_ENDPOINT")
            return
        self.run_btn.config(state='disabled')
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"启动中...\n")
        self.log_text.config(state='disabled')
        threading.Thread(target=self._run_subprocess, args=(endpoint,), daemon=True).start()

    def _run_subprocess(self, endpoint):
        env = os.environ.copy()
        env['MCP_ENDPOINT'] = endpoint
        try:
            self.proc = subprocess.Popen(
                [sys.executable, 'mcp_pipe.py', 'macos.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                bufsize=1
            )
            for line in self.proc.stdout:
                self._append_log(line)
            self.proc.wait()
            self._append_log(f"\n进程已退出，返回码：{self.proc.returncode}\n")
        except Exception as e:
            self._append_log(f"\n发生错误: {e}\n")
        finally:
            self.run_btn.config(state='normal')

    def _append_log(self, msg):
        def inner():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, msg)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        self.root.after(0, inner)

if __name__ == "__main__":
    root = tk.Tk()
    app = MCPGuiApp(root)
    root.mainloop() 