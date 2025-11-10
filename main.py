import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import (
    schema_get_files_info,
    schema_get_file_content,
    schema_write_file,
    schema_run_python_file,
    get_files_info,
    get_file_content,
    write_file,
    run_python_file,
)

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")


def call_function(function_call, verbose=False):
    available_functions = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "run_python_file": run_python_file,
    }
    function_name = function_call.name
    if verbose:
        print(f"Calling function: {function_name}({function_call.args})")
    else:
        print(f" - Calling function: {function_name}")
    args = dict(function_call.args)
    args["working_directory"] = "./calculator"
    if function_name not in available_functions:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )
    fn = available_functions.get(function_name)
    result = fn(**args)
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": result},
            )
        ],
    )


def main():
    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""
    client = genai.Client(api_key=API_KEY)
    arg = sys.argv
    verbose = "--verbose" in sys.argv
    if len(arg) == 1:
        print("Please enter a prompt")
        exit(1)
    prompt = arg[1]
    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_write_file,
            schema_get_file_content,
            schema_run_python_file,
        ]
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=messages,
        config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        ),
    )
    for fn in response.function_calls:
        result = call_function(fn)
        if not result.parts[0].function_response.response:
            raise TypeError()
        if verbose:
            print(f"-> {result.parts[0].function_response.response}")

    if verbose:
        print(f"User prompt: {prompt}")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")


if __name__ == "__main__":
    main()
