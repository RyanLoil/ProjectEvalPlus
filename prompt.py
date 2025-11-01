"""
This is all the prompt that is using in ProjectEval.
We are welcome that you edit any of them to get higher scores.
"""
import copy

CLOSE_SOURCE = {
    "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views '
                          'using the following JSON format as [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO additional content, instruction or summary.',
    "python_generate_skeleton": """
        Based on this checklist:
        {nl_checklist}
        **Give a framework of {technical_stack}.**
        You MUST use the following use JSON format to output:[{{"file":"xxx.py","path":"somepath/somedir/xxx.py","code":"the_skeleton"}}, {{...}}, ...] . 
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "javascript_generate_skeleton":
        """
        Based on this checklist:
        {nl_checklist}
        **Give a framework of {technical_stack}.**'
        You MUST use the following JSON format to output:[{{"file":"xxx.(e)js","path":"somepath/somedir/xxx.(e)js","code":"the_skeleton"}}, {{...}}, ...] . 
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "java_generate_skeleton":
        """
        Based on this checklist:
        {nl_checklist}
        **Give a framework of {technical_stack}.**'
        You MUST use the following JSON format to output:[{{"file":"xxx.java","path":"somepath/somedir/xxx.(e)js","code":"the_skeleton"}}, {{...}}, ...] . 
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "python_generate_answer":"""
        Based on this prompt: 
        {description}
        **Give a {technical_stack} project of its all files (INCLUDING the essential files to run the project) to meet the requirement.**
        You MUST use the following JSON format to output: [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{...}},...] .
        You are recommended adding an id attribute to each HTML element and adding classes for them too.
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "javascript_generate_answer":
        """
        Based on this prompt: 
        {description}
        **Give a {technical_stack} project of its all files (INCLUDING the essential files to run the project) to meet the requirement.**
        You MUST add a start.py to start the project, and if you are using third party package of NodeJS, you MUST add the "npm install <sth>" command in start.py.
        **start.py is ONLY used for starting the Java project. DO NOT SOLVE THE PROBLEM IN IT!!! **
        Add "shell=True" if you are using subprocess in start.py.
        You MUST use the following JSON format to output: [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{...}},...] .
        You are recommended adding an id attribute to each HTML element and adding classes for them too.
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "java_generate_answer":
        """
        Based on this prompt: 
        {description}
        **Give a {technical_stack} project of its all files (INCLUDING the essential files to run the project) to meet the requirement.**
        **Maven is the ONLY allowed package manager.**
        **start.py is ONLY used for starting the Java project. DO NOT SOLVE THE PROBLEM IN IT!!! **
        Add "shell=True" if you are using subprocess in start.py.
        You MUST use the following JSON format to output: [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{...}},...] .
        You are recommended adding an id attribute to each HTML element and adding classes for them too.
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT NEST MORE JSON IN THE VALUE.
        """,
    "generate_parameter":"""
        Based on the {technical_stack} project you given which is:
        {answer}
        **Give the required parameters\' values of the django project for each test in the {parameter_required}.**
        You MUST use the following JSON format to output [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] .
        For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'.
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT CHANGE THE KEYS OF JSON. 
        DO NOT NEST MORE JSON IN THE VALUE.
    """,
    "generate_information":"""
        Based on the {technical_stack} project you given which is:
        {answer}
        Assume that all files and environments have been created in root {project_root}, and projects and apps have been created.
        **Give the run commands, homepage\'s url and requirements of the {technical_stack} project.** 
        You MUST use the following JSON format to output: {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...], "requirements": [XXXX, YYYY]}} .
        DO NOT CONTAIN ANY OTHER CONTENTS.
        DO NOT CHANGE THE KEYS OF JSON. 
        DO NOT NEST MORE JSON IN THE VALUE.
    """,

    "generate_entry_point":"""
        Based on the {technical_stack} project you given which is:
        {answer}
        Assume that all files and environments have been created in root {project_root}, and projects and apps have been created.
        **Find the entry file to run the project. **
        ONLY return the path such as "example/run.py"
        DO NOT CONTAIN ANY OTHER CONTENTS.
        Do NOT add root path into the answer, but only the relative path.
    """,

    "python_mask_framework":"""
        You are tasked with standardizing code project files into a structured format. Here are the files that need to be structured:
        {answer}
        Follow these specific steps:\n\n1. **Input Structure**:  \n   Each project is a list of dictionary where:  \n   - The each dictionary represents a file.  \n   - Each dictionary contains:\n     - "file": the filename.\n     - "path": the file path.\n     - "code": the code content.\n\n2. **Standardization Rules**:  \n   Each project must follow this format:  \n   - **File Content**: The code must have clearly defined placeholder functions with docstrings describing their purpose.  \n   - **Consistent Sections**: Include these sections in order:  \n     - Python:\n\t\t- Import statements  \n\t\t- File paths or global variables  \n\t\t- Function definitions (each with docstrings, if there is no docstrings, make one)  \n\t\t- (Optional) main() function or entry point (if __name__ == "__main__")  \n\t - HTML:\n\t\t- <head> tag and its content\n\t\t- <body> tag WITHOUT its content and replace the content with comment of docstrings describing the content purpose.\n   - **Retained Files**: The following type of files should remain UNCHANGE:\n     - Django default files like: migrations, wsgi, asgi, manage, settings.\n\t - Python default files like: __init__\n   - **Removing Sections**:\n\t - All other contents that are NOT in the Consistent Sections or Retained Files include "return" and "pass" sentence and its parameter\n\t - DO NOT remove any contents that are mentioned in the Consistent Sections or Retained Files\n3. **Output Structure**:  \n   Maintain the input format but with all projects standardized similarly to Example Output belowed. Ensure the code style, comments, and placeholders are clean and consistent across all projects.\n\n4. **Specific Adjustments**:  \n   - Replace incomplete or inconsistent docstrings with meaningful placeholders like:  \n     \npython\n     \"\"\"\n     Brief description of the function\'s purpose.\n     \"\"\"\n  \n   - Ensure imports are grouped logically at the top.  \n   - Use consistent naming conventions for variables, file paths, and methods.  \n   - Retain project-specific logic while ensuring stylistic consistency.\n\n5. **Example Output**:  \n   Here\'s the desired structure for any given project:  \n   \njson\n[\n       {{\n         "file": "file_name.py",\n         "path": "file_name.py",\n         "code": "import module\n\n# Global variables\ninput_file = "input_file.xlsx"\noutput_file = "output_file.xlsx"\n\ndef function_name():\n    \"\"\"\n    Brief description of function.\n    \"\"\"\n    pass\n\ndef main():\n    \"\"\"\n    Main execution function.\n    \"\"\"\n    pass\n\nif __name__ == "__main__":\n    main()"\n       }},\n\t   {{\n\t   ...\n\t   }},\n\t   ...\n]\n'
    """,
    "javascript_mask_framework":"""
        You are tasked with standardizing code project files into a structured format. Here are the files that need to be structured:
        {answer}
        Follow these specific steps:\n\n1. **Input Structure**:  \n   Each project is a list of dictionary where:  \n   - Each dictionary represents a file.  \n   - Each dictionary contains:\n     - \"file\": the filename.\n     - \"path\": the file path.\n     - \"code\": the code content.\n\n2. **Standardization Rules**:  \n   Each project must follow this format:  \n   - **File Content**: The code must have clearly defined placeholder functions with JSDoc-style comments describing their purpose.  \n   - **Consistent Sections**: Include these sections in order:  \n     - JavaScript:\n\t   - Import statements (`import` or `require`)  \n\t   - File paths or global variables  \n\t   - Function definitions (each with JSDoc comments; if there is no comment, create one)  \n\t   - (Optional) `main()` function or entry point (`main();` at the end of the file)  \n     - HTML:\n\t   - <head> tag and its content  \n\t   - <body> tag WITHOUT its content and replace the content with comment of docstrings describing the content purpose.  \n   - **Retained Files**: The following type of files should remain UNCHANGED:\n\t   - Default project files like: `package.json`, `node_modules` configs, `webpack.config.js`  \n\t   - JavaScript default files like: `index.js`  \n   - **Removing Sections**:\n\t   - For all JavaScript functions (including app.js, utils.js, etc.), **replace their entire body with a placeholder**:\n\t\t```javascript\n\t\t// TODO: implement\n\t\t```\n\t\tor for functions that must return a value, replace with `return null;` or similar placeholder.\n\t   - Remove any empty statements, `return` statements with concrete logic, or `pass` equivalents.\n\n3. **Output Structure**:  \n   Maintain the input format but with all projects standardized similarly to Example Output below. Ensure the code style, comments, and placeholders are clean and consistent across all projects.\n\n4. **Specific Adjustments**:  \n   - Replace incomplete or inconsistent JSDoc comments with meaningful placeholders like:  \n\n```javascript\n/**\n * Brief description of the function's purpose.\n */\n```\n\n   - Ensure imports are grouped logically at the top.  \n   - Use consistent naming conventions for variables, file paths, and functions.  \n   - **All function bodies must be masked**, keeping only the signature and JSDoc.\n\n5. **Example Output**:  \n   Here's the desired structure for any given project:\n\n```json\n[\n    {{\n        \"file\": \"file_name.js\",\n        \"path\": \"file_name.js\",\n        \"code\": \"import module from 'module';\\n\\n// Global variables\\nconst inputFile = 'input_file.json';\\nconst outputFile = 'output_file.json';\\n\\n/**\\n * Brief description of function.\\n */\\nfunction functionName() {{\\n    // TODO: implement\\n}}\\n\\n/**\\n * Main execution function.\\n */\\nfunction main() {{\\n    // TODO: implement\\n}}\\n\\nmain();\"\n    }},\n    {{\n        ...\n    }}\n]\n```"
    """,
    "java_mask_framework":"""
        You are tasked with standardizing Java project files into a structured format. Here are the files that need to be structured:
        {answer}
        Follow these specific steps:\n\n1. **Input Structure**:\n   Each project is a list of dictionary where:\n   - Each dictionary represents a file.\n   - Each dictionary contains:\n     - "file": the filename.\n     - "path": the file path.\n     - "code": the code content.\n\n2. **Standardization Rules**:\n   Each project must follow this format:\n   - **File Content**: The code must have clearly defined placeholder methods with Javadoc-style comments describing their purpose.\n   - **Consistent Sections**: Include these sections in order:\n     - Java:\n       - Package declaration (if any)\n       - Import statements\n       - Class definitions (each with Javadoc comments for the class and its methods; if there is no comment, create one)\n       - Method definitions (each with Javadoc; method bodies should be replaced with placeholders)\n       - (Optional) main() method as entry point\n     - HTML:\n       - <head> tag and its content\n       - <body> tag WITHOUT its content and replace the content with comment describing the purpose.\n\n   - **Retained Files**: The following type of files should remain UNCHANGED:\n       - Default project files like `pom.xml`, `build.gradle`, `.gitignore`\n       - Java default files like `package-info.java`\n   \n   - **Removing Sections**:\n       - For all Java methods (including utility classes, service classes, etc.), replace their entire body with a placeholder:\n         ```java\n         // TODO: implement\n         ```\n         or if the method must return a value, replace with a suitable placeholder like `return null;` or `return 0;`.\n       - Remove any other statements not in the Consistent Sections or Retained Files.\n\n3. **Output Structure**:\n   Maintain the input format but with all projects standardized similarly to Example Output below. Ensure the code style, comments, and placeholders are clean and consistent across all projects.\n\n4. **Specific Adjustments**:\n   - Replace incomplete or inconsistent Javadoc comments with meaningful placeholders like:\n     ```java\n     /**\n      * Brief description of the method's purpose.\n      */\n     ```\n   - Ensure imports are grouped logically at the top.\n   - Use consistent naming conventions for variables, class names, and methods.\n   - All method bodies must be masked, keeping only the signature and Javadoc.\n\n5. **Example Output**:\n   Here's the desired structure for any given project:\n\n```json\n[\n    {{\n        "file": "ExampleClass.java",\n        "path": "src/main/java/com/example/ExampleClass.java",\n        "code": "package com.example;\\n\\nimport java.util.*;\\n\\n/**\\n * Brief description of the class.\\n */\\npublic class ExampleClass {{\\n\\n    /**\\n     * Brief description of the method.\\n     */\\n    public void exampleMethod() {{\\n        // TODO: implement\\n    }}\\n\\n    /**\\n     * Main execution method.\\n     */\\n    public static void main(String[] args) {{\\n        // TODO: implement\\n    }}\\n}}"\n    }},\n    {{\n        ...\n    }}\n]
    """
    }

prompt = {
    "GPTTest": CLOSE_SOURCE,
    "GeminiTest": CLOSE_SOURCE,
    # "OllamaTest": {
    #     "generate_checklist": '{nl_prompt}.Give a natural language function checklist from the users\' views. '
    #                           'Only return as a JSON object which template is [{{"page":"XXX", "function":[{{"function":"XXX", "description"; "YYYY"}}, {{...}}, ...]}}, {{...}}, ...}} with NO other content. '
    #                           'Respond only with natural language valid JSON. Do not write an introduction or summary.',
    #     "python_generate_skeleton": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack}.'
    #                                  'Only return as a JSON object which template is [{{"file":"xxx.py","path":"somepath/somedir/xxx.py","code":"the_skeleton"}}, {{...}}, ...]. '
    #                                  'If the file is not a python file, the json format should be {{"file": "/example_app/xxx.xx", "description":"XXXX"}}. DO NOT CONTAIN ANY OTHER CONTENTS. '
    #                                  'Respond only with valid JSON. Do not write an introduction or summary.',
    #     "javascript_generate_skeleton": 'Based on this checklist {nl_checklist}, give a framework of {technical_stack} '
    #                                     'also used JSON format of [{{"file":"xxx.(e)js","path":"somepath/somedir/xxx.(e)js","code":"the_skeleton"}}, {{...}}, ...]. '
    #                                     'DO NOT CONTAIN ANY OTHER CONTENTS.',
    #     "python_generate_answer": 'Based on this "{description}", give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement.'
    #                        'Only return as a JSON object which template is [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{…}},…] with NO other content. '
    #                        'Respond only with valid JSON. Do not write an introduction or summary. '
    #                        'Recommend adding an id attribute to each HTML element and adding classes for them too.',
    #     "javascript_generate_answer": 'Based on this "{description}", give a {technical_stack} Project of its all files (including the essential files to run the project) to meet the requirement.'
    #                               'Only return as a JSON object which template is [{{"file":"answer.something","path":"somepath/somedir/answer.something", "code":"the_code_in_the_file"}},{{…}},…] with NO other content. '
    #                               'Respond only with valid JSON. Do not write an introduction or summary. '
    #                               'Recommend adding an id attribute to each HTML element and adding classes for them too.'
    #                               'You MUST add a start.py to start the project, and if you are using third party package of NodeJS, you MUST add the "npm install <sth>" command in start.py'
    #                               'Add "shell=True" if you are using subprocess in start.py.',
    #     "generate_parameter": 'Based on the {technical_stack} project you given which is {answer}, give the required parameters\' values of the django project for each test in the {parameter_required}. '
    #                           'Return as a JSON object which template is [{{"page":"XXX", "function":"[{{"function":"XXX", "parameter": [{{"name":"XXX", "answer": "your_answer_parameter"}}, {{...}}, ...]}}, {{...}}, ...], {{...}}, ...] with NO other content and DO NOT CHANGE THE KEYS OF JSON. '
    #                           'For example, the requested parameter name is \'test_url\' and the answer may be \'http://localhost:8000/\'. '
    #                           'Respond only with valid JSON. Do not write an introduction or summary.',
    #     "generate_information": 'Based on the {technical_stack} project you given which is {answer}, assume that all files and environments have been created in root {project_root}, '
    #                             'and projects and apps have been created, give the run commands, homepage\'s url and requirements of the {technical_stack} project. '
    #                             'Only return as a JSON object which template is {{"initiate_commands": [["manage.py","makemigrations"],["manage.py","migrate"],[XXX,YYY],...], "requirements": [XXXX, YYYY]}} with NO other content. '
    #                             'Respond only with valid JSON. Do not write an introduction or summary.',
    #     "generate_entry_point": 'Based on the {technical_stack} project you given which is {answer}, '
    #                             'assume that all files and environments have been created in root {project_root}, find the entry file to run the project. '
    #                             'ONLY return the path such as "example/run.py" with NO other content. Do NOT add root path into the answer, but only the relative path.'
    #                             'Do NOT write an introduction or summary.'
    # },
    "OllamaTest": CLOSE_SOURCE, # All prompt are unified now.
}

prompt["DeepSeekTest"] = copy.deepcopy(prompt["OllamaTest"])
prompt["VLLMTest"] = copy.deepcopy(prompt["OllamaTest"])