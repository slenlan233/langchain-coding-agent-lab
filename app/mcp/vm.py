import io
import os
import shlex
import subprocess
import tarfile
import tempfile
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

os.environ["LIMA_HOME"] = r"C:\lima-home"
mcp = FastMCP()

def run_limavm_shell_command(command):
    try:
        wrapper_command = "limactl shell lima-test " + command
        shell_command = shlex.split(wrapper_command)
        shell_command[0] = r"C:\lima-2.2.0-Windows-AMD64\bin\limactl.exe"

        res = subprocess.run(
            shell_command,
            shell=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15
        )

        if res.returncode != 0:
            return res.stderr

        return res.stdout
    except Exception as e:
        return str(e)

def run_limavm_command(command):
    try:
        wrapper_command = "limactl " + command
        shell_command = shlex.split(wrapper_command, posix=False)
        shell_command[0] = r"C:\lima-2.2.0-Windows-AMD64\bin\limactl.exe"

        res = subprocess.run(
            shell_command,
            shell=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15
        )

        if res.returncode != 0:
            return res.stderr
        return res.stdout
    except Exception as e:
        return str(e)


@mcp.tool(name="make_dir_in_vm", description="在指定的虚拟机中创建目录，相当于 mkdir -p 命令")
def make_dir_in_vm(dir_path: Annotated[str, Field(description="要创建的目录路径", examples=["/home/lima.guest/nginx/uploads"])]):
    """在虚拟机中创建目录"""
    return run_limavm_shell_command("mkdir -p " + dir_path)


@mcp.tool(name="list_files_in_vm", description="查看虚拟机中指定目录，相当于 ls -al 命令")
def list_files_in_vm(dir_path: Annotated[str, Field(description="要查看的目录路径", examples=["/home/lima.guest/nginx/uploads"])]):
    """查看虚拟机指定目录下的文件"""
    return run_limavm_shell_command("ls -al " + dir_path)

@mcp.tool(name="write_file_to_vm", description="向虚拟机中写入指定文件")
def write_file_to_vm(
        file_path: Annotated[str, Field(
            description="写入虚拟机中的文件地址",
            examples=["/home/lima.guest/nginx/uploads/index.html"]
        )],
        content: Annotated[str, Field(
            description="写入虚拟机中的文件内容",
            examples=["<div>hello limavm</div>"]
        )]
):
    temp_path = file_path + ".tmp"

    shell_command = [
        r"C:\lima-2.2.0-Windows-AMD64\bin\limactl.exe",
        "shell",
        "lima-test",
        "tee",
        temp_path
    ]

    try:
        res = subprocess.run(
            shell_command,
            shell=False,
            input=content,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15
        )

        if res.returncode != 0:
            return res.stderr

        chmod_result = run_limavm_shell_command(
            f"chmod 644 {temp_path}"
        )

        if chmod_result:
            return "修改权限失败：" + chmod_result

        mv_result = run_limavm_shell_command(
            f"mv {temp_path} {file_path}"
        )

        if mv_result:
            return "重命名文件失败：" + mv_result

        return "写入成功"

    except Exception as e:
        return str(e)


def change_file_permission_in_vm(file_path, mode):
    return run_limavm_shell_command(f"chmod {mode} {file_path}")

@mcp.tool(name="upload_directory_to_vm", description="将本地文件目录上传至虚拟机指定目录")
def upload_directory_to_vm(
        local_dir: Annotated[str, Field(
            description="本地文件目录",
            examples=[r"D:\学习Java\ai项目\3.xiangmu\.temp\vue2-test"]
        )],
        vm_dest_dir: Annotated[str, Field(
            description="虚拟机文件目录",
            examples=["/home/lima.guest/nginx/uploads"]
        )],
):
    if not os.path.exists(local_dir):
        return f"本地目录不存在：{local_dir}"

    if not os.path.isdir(local_dir):
        return f"指定路径不是文件夹：{local_dir}"

    mkdir_result = make_dir_in_vm(vm_dest_dir)

    if mkdir_result:
        return "创建虚拟机目录失败：" + mkdir_result

    buffer = io.BytesIO()

    def filter_file(tarinfo):
        parts = tarinfo.name.replace("\\", "/").split("/")

        if "node_modules" in parts or ".git" in parts:
            return None

        return tarinfo

    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        tar.add(
            local_dir,
            arcname=".",
            filter=filter_file
        )

    shell_command = [
        r"C:\lima-2.2.0-Windows-AMD64\bin\limactl.exe",
        "shell",
        "lima-test",
        "tar",
        "-xzf",
        "-",
        "-C",
        vm_dest_dir
    ]

    res = subprocess.run(
        shell_command,
        shell=False,
        input=buffer.getvalue(),
        capture_output=True,
        timeout=60
    )

    if res.returncode != 0:
        return (
            f"上传失败\n"
            f"returncode = {res.returncode}\n"
            f"stdout = {res.stdout.decode('utf-8', errors='replace')}\n"
            f"stderr = {res.stderr.decode('utf-8', errors='replace')}"
        )

    return f"上传 [{local_dir}] 至 lima-test:[{vm_dest_dir}] 成功"


if __name__ == '__main__':
    mcp.run(transport="stdio")
