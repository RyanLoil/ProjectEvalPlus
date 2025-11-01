import asyncio
import json
import csv
import subprocess
import os
from openai import OpenAI
import shutil

import config
from controller import BaseController, TranslationController
from llm import VLLMTest, OllamaTest, DeepSeekTest, GPTTest
from run_judge import run_judge


MAX_ITER = 5
TARGET_SCORE = 0.9  # 90%

LR = {
    "js": "NodeJS",
    "java": "Java"
}
def run_translation(model_name, language):
    verbose = f"renew_{language}"
    model_name = "gpt-5" # "gpt-oss:20b" #"gpt-5-mini" # "deepseek-chat"
    workdir = f"experiments/{verbose}/"
    
    python_canonical_answer = "data/project_eval_answer.json"
    if not os.path.exists(workdir + f"/{model_name.replace(':','-')}/direct/{model_name.replace(':','-')}_{config.RUN_DATETIME}_level_3.json"):
        open(workdir + f"/{model_name.replace(':','-')}/direct/{model_name.replace(':','-')}_{config.RUN_DATETIME}_level_3.json","w",encoding="utf-8")
        shutil.copy("data/project_eval_answer_paramter.json",workdir + f"/{model_name.replace(':','-')}/direct/{model_name.replace(':','-')}_{config.RUN_DATETIME}_level_3_parameter.json")
        with open(workdir + f"/{model_name.replace(':','-')}/direct/{model_name.replace(':','-')}_{config.RUN_DATETIME}_level_3_startfile.json","w",encoding="utf-8") as file:
            json.dump({str(_):"start.py" for _ in range(1,21)})
        
    answer_file = workdir + f"/{model_name.replace(':','-')}/direct/{model_name.replace(':','-')}_20251018-123000_level_3.json"
    parameter_file = f"data/project_eval_parameter_{language}.json"
    project_file  = f"data/project_eval_project_{language}.json"
    result_info = workdir + f"{verbose}-info.txt"
    language = LR[language]
    skip_list_set = {1,2,3,4,5,6,7,8,9,10,14,15,17} #{1,2,3,4,5,6,9,11,14,15,16,17,18} # TODO GPT-5-mini JavaScript gpt-5-mini 7-13和20卡死，但11、12、13、19、20结果不正确
    class_dict = {
        "deepseek-chat":DeepSeekTest,
        "gpt-oss:20b": OllamaTest,
        "gpt-5-mini": GPTTest,
        "gpt-5": GPTTest,
        "gemma3:27b":OllamaTest,
    }
    controller = TranslationController(project_file, python_canonical_answer, parameter_file, verbose,
                                       result_info, class_dict[model_name],
                                       model_name)
    csv_file = open(workdir + f"{verbose}_iteration_translation_output_{config.RUN_DATETIME}.csv","w",encoding="utf-8",newline="")
    output_csv = csv.DictWriter(csv_file, fieldnames=["project_id","iteration","score"])
    output_csv.writeheader()

    for i in range(1,21):
        if i in skip_list_set:
            controller.logger.info(f"Skipping project {i}.")
            continue
        controller.logger.info(f"\n=== Iteration {i}-1 ===")
        project_id = str(i)

        # Initial
        controller.set_answer_file(python_canonical_answer)
        prev_answer = controller.read_answer(project_id)
        parameter = controller.read_parameter(project_id)
        nl_prompt, testcase = controller.read_project(project_id)
        try:
            prev_answer = controller.generate_new_language_answer(nl_prompt, testcase, parameter, prev_answer, None, "s", language)
        except Exception as e:
            controller.logger.info(f"Failed to generate new language answer of project {project_id}: {e}")
            continue

        # Initial test
        controller.set_answer_file(answer_file)
        controller.write_answer(prev_answer,project_id)
        controller.logger.info("New answer written: {}".format(prev_answer))
        controller.logger.info("Running judge...")
        controller.run_judge(project_id)
        flag = False
        prev_score, prev_result = controller.read_result(project_id)
        best_answer = prev_answer
        best_score = prev_score
        controller.logger.info(f"New score: {best_score}")
        output_csv.writerow({"project_id":i,"iteration":1,"score":best_score})
        csv_file.flush()

        for j in range(2, controller.max_iter+1):
            controller.logger.info(f"\n=== Iteration {i}-{j} ===")
            controller.logger.info(f"Previous score: {prev_score * 100:.2f}%")
            if prev_score >= controller.target_score:
                controller.logger.info(f"Target score reached for project {i}. Best score:{best_score}. Stopping.")
                flag = True
                break

            # Renew answer
            try:
                new_answer = controller.generate_new_language_answer(nl_prompt, testcase,parameter, prev_answer, prev_result,"e", language)
            except Exception as e:
                controller.logger.error(f"Failed to generate new language answer: {e}.")
                continue
            if not new_answer:
                continue
            controller.write_answer(new_answer, project_id)
            controller.logger.info("New answer written: {}".format(new_answer))

            # Test answer
            controller.logger.info("Running judge...")
            controller.run_judge(project_id)
            new_score, new_test_point_result = controller.read_result(project_id)
            controller.logger.info(f"New score: {new_score * 100:.2f}%")
            if new_score <= best_score:
                controller.write_answer(best_answer, project_id)
                controller.logger.info(f"New answer is not getting better, reverse to old answer.")
            else:
                best_answer = new_answer
                best_score = new_score
                controller.logger.info(f"New answer is getting better, write down.")
            prev_answer = new_answer
            prev_score = new_score
            prev_result = new_test_point_result
            output_csv.writerow({"project_id": i, "iteration": j, "score": new_score})
            csv_file.flush()


        if not flag:
            controller.logger.warning(f"Project {i} reached maximum iteration. Best score:{best_score}. Stopping.")

if __name__ == "__main__":
    parser.add_argument("-l", "--language", type=str, required=True,
                        help="The programming language you want test, support Java and JavaScript.")
    parser.add_argument("-m", "--model", type=str, required=True,
                        help="The model you want test.")

    args = parser.parse_args()
    run_translation(args)


