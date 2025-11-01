import argparse
import json
import csv
import os
import traceback

import config
from controller import JudgeController
from llm import GPTTest, OllamaTest, GeminiTest, DeepSeekTest, VLLMTest
from config import PROJECT_EVAL_DEFAULT_TEST_CASE
from utils import extract_json_files_from_folder, remove_temp_test_files
from types import SimpleNamespace

def run_judge(args):
    current_pid = os.getpid()
    print(f"ProjectEval Main PID: {current_pid}")

    if type(args) == dict:
        args = SimpleNamespace(**args)


    dirlist = json.loads(args.dirlist)
    dolist = set([_.replace(".json", "") for _ in json.loads(args.dolist)])
    dolist_para = args.dolist_para
    if dolist:
        print(f"Dolist set. {dolist}.")
    verbose = args.verbose
    if args.project_id_list:
        project_id_list = json.loads(args.project_id_list)
    else:
        project_id_list = [str(_) for _ in range(1, 21)]

    # If you are using a NON-ollama model, add your model prefix with its own LLMTestClass in start_with_dict{}, else skip this step.
    start_with_dict = {
        "gpt": GPTTest,
        "gemini": GeminiTest,
        "deepseek": DeepSeekTest,
        # "gpt-oss-20b": VLLMTest,
        "gpt-oss-20b": OllamaTest,
    }

    # Load config
    result_output_path = config.RESULT_REPORT_PATH
    project_level_detail_path = config.PROJECT_LEVEL_DETAIL_PATH
    test_point_report_path = config.TEST_POINT_REPORT_PATH

    # Set result analysis output path
    if verbose:
        project_level_detail_path = os.path.join(project_level_detail_path, verbose) + "/"
        test_point_report_path = os.path.join(test_point_report_path, verbose) + "/"
        with open(test_point_report_path + f"{verbose}-info.txt", "w", encoding="utf-8") as f:
            f.write(project_level_detail_path + f"projecteval-project_level_detail-{config.RUN_DATETIME}.csv\n")
            f.write(test_point_report_path + f"projecteval-test_point_result-{config.RUN_DATETIME}.csv\n")
            f.close()

    file = open(
        result_output_path + f"projecteval-result-{config.RUN_DATETIME}.csv",
        "w", encoding="utf-8", newline="")

    result_file = csv.DictWriter(
        file, delimiter=",",
        fieldnames=["date", "model", "mode", "timestamp", "level", "passed", "failed", "executed", "score"])
    result_file.writeheader()

    if not os.path.exists(test_point_report_path + f"projecteval-test_point_result-{config.RUN_DATETIME}.csv"):
        reason_file_source = open(test_point_report_path + f"projecteval-test_point_result-{config.RUN_DATETIME}.csv",
                                  "w", encoding="utf-8", newline="")
    else:
        reason_file_source = open(test_point_report_path + f"projecteval-test_point_result-{config.RUN_DATETIME}.csv",
                                  "a", encoding="utf-8", newline="")
    reason_file = csv.DictWriter(reason_file_source,
                                 fieldnames=["date", "model", "mode", "timestamp", "level", "project_id", "index",
                                             "status", "result", "reason", "function"])
    reason_file.writeheader()

    project_level_detail_file_source = open(
        project_level_detail_path + f"projecteval-project_level_detail-{config.RUN_DATETIME}.csv", "a",
        encoding="utf-8", newline="")
    project_level_detail_file = csv.DictWriter(project_level_detail_file_source,
                                               fieldnames=["date", "model", "mode", "timestamp", "level", "project_id",
                                                           "pass", "total", "reason"])
    project_level_detail_file.writeheader()

    result_output_path = result_output_path.replace(f"{verbose}/", "")

    # Start
    for date in dirlist:
        # Each model has its own directory
        model_list = os.listdir(os.path.join(result_output_path, date))
        for model in model_list:
            # Two mode mentioned in paper
            for mode in ("cascade", "direct"):
                dirpath = os.path.join(result_output_path, date, model, mode)
                if not os.path.exists(dirpath):
                    print(f"Skip {dirpath}. Not exists.")
                    continue
                file_group = extract_json_files_from_folder(dirpath, mode=True)
                for group in file_group:
                    if dolist_para and str(group) not in dolist:
                        print(f"Skip {group}. Not in dolist.")
                        continue
                    try:
                        level = int(str(group).split("_")[3])
                        if mode == "cascade" and level == 3:
                            print("Skip cascade level 3. It is a same mode of direct level 3.")
                            continue
                        if model in start_with_dict:
                            model_class = start_with_dict[model]
                            model_name = model
                        elif model.split("-")[0] in start_with_dict:
                            model_class = start_with_dict[model.split("-")[0]]
                            model_name = model
                        else:
                            model_class = OllamaTest
                            model_name = model.replace("-", ":")

                        if hasattr(model_class, "MODEL_REFLECTION") and model_name in model_class.MODEL_REFLECTION:
                            model_name = model_class.MODEL_REFLECTION[model_name]

                        print(f"Using {model_class.__name__} for {model_name}.")

                        tester = JudgeController(question_path=args.question_path,
                                                 answer_path=file_group[group]["answer_code_path"],
                                                 model_class=model_class,
                                                 parameter_file_path=file_group[group]["answer_parameter_path"],
                                                 llm=model_name,
                                                 device="GPU-e64683ee-8e58-13f4-b2aa-e88128cc3ef9",
                                                 )

                        tester.logger.info("Start:" + "-".join([date, model, mode, str(level)]))
                        initiate_command = {}
                        requirements = {}

                        # The following block is not within the scope of ProjectEval's selection.
                        # It allows the model to choose the library it likes to use and provide initial commands.
                        # The universality of this part of the code has not been fully tested, so please use and adapt it with caution.
                        if config.LANGUAGE == "python":
                            for project_id in project_id_list:
                                if project_id not in (str(_) for _ in range(16, 20)):
                                    # Website Initial
                                    initiate_command[project_id] = [[]]
                                    requirements[project_id] = ["django", "matplotlib", "pyperclip", "qrcode",
                                                                "markdown"]
                                else:
                                    # Console initial
                                    initiate_command[project_id] = []
                                    requirements[project_id] = ["openpyxl", "pandas"]
                        else:
                            for project_id in project_id_list:
                                if project_id not in (str(_) for _ in range(16, 20)):
                                    # Website Initial
                                    initiate_command[project_id] = [[]]
                                else:
                                    # Console initial
                                    initiate_command[project_id] = []

                        if "startfile" in file_group[group]:
                            start_file_list = json.load(open(file_group[group]["startfile"]))
                        else:
                            start_file_list = None
                        score, score_table, reason_list = tester.evaluate(initiate_command, requirements,
                                                                          project_id_list=project_id_list,
                                                                          start_file_list=start_file_list)
                        data = {
                            "date": date,
                            "model": model,
                            "mode": mode,
                            "timestamp": str(group).split("_")[1],
                            "level": level,
                            "passed": score["pass"],
                            "failed": PROJECT_EVAL_DEFAULT_TEST_CASE - score["pass"],
                            "executed": score["testcase"] if "testcase" in score else 0,
                            "score": score["pass@1"] if "pass@1" in score else 0,
                        }

                        for key in data:
                            data[key] = str(data[key])
                        result_file.writerow(data)
                        file.flush()
                        for index in range(len(reason_list)):
                            reason_list[index] = {
                                "date": date,
                                "model": model,
                                "mode": mode,
                                "timestamp": str(group).split("_")[1],
                                "level": level,
                                **reason_list[index],
                                # "index": reason_list[index]["index"],
                                # "status": reason_list[index]["status"],
                                # "result": reason_list[index]["result"],
                                # "reason": reason_list[index]["reason"],
                                # "function": reason_list[index]["function"],
                            }
                        reason_file.writerows(reason_list)
                        reason_file_source.flush()
                        for index in range(len(score_table)):
                            score_table[index] = {
                                "date": date,
                                "model": model,
                                "mode": mode,
                                "timestamp": str(group).split("_")[1],
                                "level": level,
                                **score_table[index]
                            }
                        project_level_detail_file.writerows(score_table)
                        project_level_detail_file_source.flush()
                    except Exception as e:
                        print(f"Got error: {e}")
                        print(f"{traceback.format_exc()}")

    if config.AUTOMATICALLY_DELETE or input(f"Delete all possible tempfiles generated by ProjectEval in Downloads?\nList:{config.POSSIBLE_TEMP_TEST_FILE}.\n(Y/n)")=="Y":
        if config.AUTOMATICALLY_DELETE or input(f"Are you sure?(Y/n)") == "Y":
            for file in config.POSSIBLE_TEMP_TEST_FILE:
                remove_temp_test_files(os.path.expanduser(f"~/Downloads/{file}"))
            print("Remove successfully.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--dirlist", type=str, required=True,
                        help="The directories that you want to evaluate. The directories must obey the rule of /directory_name/model_name/cascade(direct)/<model>_<timestamp>_level_<level>.json. Official-result is a good example.")
    parser.add_argument("-d", "--dolist", type=str, required=False, default="[]", )
    parser.add_argument("--dolist_para", action="store_true")
    parser.add_argument("-v", "--verbose", type=str, required=False, default="")
    parser.add_argument("-p", "--project_id_list", type=str, required=False, default="")
    parser.add_argument("--question_path", type=str, required=False, default="data/project_eval_project.json")

    # Load parameter
    args = parser.parse_args()
    run_judge(args)



