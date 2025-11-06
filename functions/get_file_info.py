import os
import subprocess
from config import CHARACTER_LIMIT

def get_file_info(working_directory, directory="."):
    abs_wd, abs_td = get_abs_path(working_directory, directory)
    if not os.path.commonpath([abs_wd, abs_td]) == abs_wd:
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
    elif not os.path.isdir(abs_td):
        return f'Error: "{directory}" is not a directory'
    
    files_info = []
    for name in os.listdir(abs_td):
        full_path = os.path.join(abs_td, name)
        is_dir = os.path.isdir(full_path)
        size = os.path.getsize(full_path)
        files_info.append(f"- {name}: files_size={size}, is_dir={is_dir}")
    return "\n".join(files_info)

def get_file_content(working_directory, file_path):
    abs_wd, abs_td = get_abs_path(working_directory, file_path)
    # This could probably be cleaned up
    if not os.path.commonpath([abs_wd, abs_td]) == abs_wd:
        return f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
    elif not os.path.isfile(abs_td):
        return f'Error: File not found or is not a regular file: "{file_path}"'
    
    try:
        with open(abs_td, "r") as f:
            file_content = f.read(CHARACTER_LIMIT + 1)
            if len(file_content) > 10000:
                file_content = file_content[:CHARACTER_LIMIT]
                return f"{file_content}... truncated at {CHARACTER_LIMIT} characters"
            return file_content
    except (FileNotFoundError, PermissionError, OSError) as e :
        return f"Error: {e}"
    
    
def write_file(working_directory, file_path, content):
    abs_wd, abs_td = get_abs_path(working_directory, file_path)
    dir_path = os.path.dirname(abs_td)
    if not os.path.commonpath([abs_wd, abs_td]) == abs_wd:
        return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
    elif dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except (FileNotFoundError, PermissionError, OSError) as e:
            return f"Error: {e}"
    try:
        with open(abs_td, "w") as f:
            f.write(content)
            return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except (FileNotFoundError, PermissionError, OSError) as e :
        return f"Error: {e}"
    
def run_python_file(working_directory, file_path, args=[]):
    output = ""
    abs_wd, abs_td = get_abs_path(working_directory, file_path)
    if not os.path.commonpath([abs_wd, abs_td]) == abs_wd:
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    elif not os.path.isfile(abs_td):
        return f'Error: File "{file_path}" not found'
    elif not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'
    try:
        result = subprocess.run(["uv", "run", f"{abs_td}"] + args, capture_output=True, timeout=0.3, text=True)
        output += f"STDOUT: {result.stdout}\nSTDERR:{result.stderr}\n"
        if result.returncode != 0:
            output += f"Process exited with code {result.returncode}"
        return output
    except (FileNotFoundError, PermissionError, OSError) as e:
        return f"Error: executing Python file: {e}"




def get_abs_path(working_directory, file_path):
    abs_wd = os.path.abspath(working_directory)
    abs_td = os.path.abspath(os.path.join(working_directory, file_path))    
    return (abs_wd, abs_td)