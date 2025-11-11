import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import get_files_info, schema_get_files_info
from functions.get_file_content import get_file_content, schema_get_file_content
from functions.run_python import run_python_file, schema_run_python_file
from functions.write_file import write_file, schema_write_file
from config import MAX_ITERS

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")



def main():
    def generate_content(client, messages, verbose):
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
            ),
        )
    
        if verbose:
            print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
        if response.candidates:
            for candidate in response.candidates:
                function_call_content = candidate.content
                messages.append(function_call_content)

        if not response.function_calls:
            return response.text
        
        function_responses = []
        for fn in response.function_calls:
            result = call_function(fn)
        if not result.parts and  not result.parts[0].function_response:
            raise Exception("empty function call result")
        if verbose:
            print(f"-> {result.parts[0].function_response.response}")
        function_responses.append(result.parts[0])

        if not function_responses:
            raise Exception("no function responses generated, exiting")
        messages.append(types.Content(role="user", parts=function_responses))

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
    system_prompt = """
You are a helpful AI agent designed to help the user write code within their codebase.

When a user asks a question or makes a request, make a function call plan. For example, if the user asks "what is in the config file in my current directory?", your plan might be:

1. Call a function to list the contents of the working directory.
2. Locate a file that looks like a config file
3. Call a function to read the contents of the config file.
4. Respond with a message containing the contents

You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security.

You are called in a loop, so you'll be able to execute more and more function calls with each message, so just take the next step in your overall plan.

Most of your plans should start by scanning the working directory (`.`) for relevant files and directories. Don't ask me where the code is, go look for it with your list tool.

Execute code (both the tests and the application itself, the tests alone aren't enough) when you're done making modifications to ensure that everything works as expected.
"""
    load_dotenv()
    API_KEY = os.environ.get("GEMINI_API_KEY")
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


    iters = 0
    while True:
        iters += 1
        if iters > MAX_ITERS:
            print(f"Maximum iterations ({MAX_ITERS}) reached.")
            sys.exit(1)

        try:
            final_response = generate_content(client, messages, verbose)
            if final_response:
                print("Final response:")
                print(final_response)
                break
        except Exception as e:
            print(f"Error in generate_content: {e}")


if __name__ == "__main__":
    main()
