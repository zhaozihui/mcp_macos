# server.py
from mcp.server.fastmcp import FastMCP
import sys
import logging
import subprocess
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

logger = logging.getLogger('Calculator')

import math
import random

# Create an MCP server
mcp = FastMCP("Calculator")
@mcp.tool()
def get_current_datetime() -> dict:
    """
    获取当前日期和时间。
    返回：{'datetime': 'YYYY-MM-DD HH:MM:SS'}
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return {"success": True, "datetime": now} 
# Add an addition tool
@mcp.tool()
def calculator(python_expression: str) -> dict:
    """For mathamatical calculation, always use this tool to calculate the result of a python expression. `math` and `random` are available."""
    result = eval(python_expression)
    logger.info(f"Calculating formula: {python_expression}, result: {result}")
    return {"success": True, "result": result}

# 新增：添加备忘录内容工具
@mcp.tool()
def add_note_to_mac_notes(title: str, content: str, account: str = "iCloud") -> dict:
    """
    在 macOS 备忘录中创建新备忘录。Markdown格式
    参数：
      - title: 备忘录标题
      - content: 备忘录内容
      - account: 账户名，默认iCloud，另一个常见值是"On My Mac"
    """
    def escape_applescript_string(s):
        return s.replace("\\", "\\\\").replace('"', '\\"').replace('\n', '\\n')

    # AppleScript 脚本
    applescript = f'''
    tell application "Notes"
        activate
        tell account "{account}"
            make new note with properties {{name:"{escape_applescript_string(title)}", body:"{escape_applescript_string(content)}"}}
        end tell
    end tell
    '''

    try:
        # 调用osascript执行AppleScript
        subprocess.run(["osascript", "-e", applescript], check=True)
        logger.info(f"Added note to {account} with title '{title}'")
        return {"success": True, "message": f"Note '{title}' added to {account}."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to add note: {e}")
        return {"success": False, "error": str(e)}
EMAIL_ACCOUNTS = {
    "default": {
        "smtp_server": "",
        "smtp_port": 25,
        "username": "",
        "password": ""  # 推荐从环境变量或密文管理加载
    },
    # 可以添加更多配置：
    # "internal": { ... },
}
# 简化的发送邮件工具
@mcp.tool()
def send_email_simple(to: str, subject: str, body: str, account: str = "default") -> dict:
    """
    发送邮件（使用预设SMTP账户）。
    
    参数：
      - to: 收件人邮箱地址
      - subject: 邮件主题
      - body: 邮件正文
      - account: 使用的邮件配置（默认 "default"）
    """
    if account not in EMAIL_ACCOUNTS:
        return {"success": False, "error": f"Unknown account '{account}'"}

    cfg = EMAIL_ACCOUNTS[account]

    try:
        msg = EmailMessage()
        msg["From"] = cfg["username"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
            server.login(cfg["username"], cfg["password"])
            server.send_message(msg)

        logger.info(f"Email sent to {to} via account '{account}'")
        return {"success": True, "message": f"Email sent to {to}."}
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def add_calendar_event(title: str, start: str, end: str = None, calendar: str = "个人") -> dict:
    """
    添加事件到 macOS 日历。会议预定等

    参数：
    - title: 事件标题
    - start: 开始时间，格式：YYYY-MM-DD HH:MM
    - end: （可选）结束时间，格式相同，默认 +1 小时
    - calendar: 使用的日历名称（默认 "个人"）

    返回：
    - dict: { "success": True/False, "message": str }
    """
    try:
        # 解析时间
        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M")
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M")
        else:
            end_dt = start_dt + timedelta(hours=1)

        # 生成 AppleScript 日期设定脚本（语言无关）
        applescript = f'''
        set startDate to current date
        set year of startDate to {start_dt.year}
        set month of startDate to {start_dt.strftime("%B")}
        set day of startDate to {start_dt.day}
        set hours of startDate to {start_dt.hour}
        set minutes of startDate to {start_dt.minute}

        set endDate to current date
        set year of endDate to {end_dt.year}
        set month of endDate to {end_dt.strftime("%B")}
        set day of endDate to {end_dt.day}
        set hours of endDate to {end_dt.hour}
        set minutes of endDate to {end_dt.minute}

        tell application "Calendar"
            tell calendar "{calendar}"
                make new event with properties {{summary:"{title}", start date:startDate, end date:endDate}}
            end tell
        end tell
        '''

        # 执行 AppleScript
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)

        if result.returncode != 0:
            return {"success": False, "message": result.stderr.strip()}
        return {"success": True, "message": "事件已添加到日历。"}

    except Exception as e:
        return {"success": False, "message": str(e)}

@mcp.tool()
def run_osascript(script: str) -> dict:
    """
    运行 macOS 的 osascript 命令。

    参数:
    - script: AppleScript 脚本内容（支持多行）

    返回:
    - 执行结果输出，或错误信息
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "error": str(e)
        }
# Start the server
if __name__ == "__main__":
    # mcp.run(transport="stdio")
    mcp.run(transport="sse")
