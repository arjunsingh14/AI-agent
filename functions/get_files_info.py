import os
import subprocess
from config import CHARACTER_LIMIT
from google.genai import types

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="List the content of a file up to 100000 characters.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path of the file we want to extract the content from relative to the working directory, if not returns an error string.",
            ),
        },
        required=["file_path"],
    ),
)


schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Write or overwrite file, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path of the file we write/overwrite to relative to the working directory, if not returns an error string.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="Message content that should be written to the file.",
            ),
        },
        required=["file_path"],
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs a Python file, constrained to the working directory",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path of the Python file to run, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                description="Optional CLI args passed to the script.",
                items=types.Schema(type=types.Type.STRING),
            ),
        },
        required=["file_path"],
    ),
)


def get_files_info(working_directory, directory="."):
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
    except (FileNotFoundError, PermissionError, OSError) as e:
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
    except (FileNotFoundError, PermissionError, OSError) as e:
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
        result = subprocess.run(
            ["uv", "run", f"{abs_td}"] + args,
            capture_output=True,
            timeout=0.3,
            text=True,
        )
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
