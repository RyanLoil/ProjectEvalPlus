import json
import logging
import os
import re
import time
from datetime import datetime

import requests
from openai import OpenAI, NOT_GIVEN
from google import genai
from openai.types.chat import ChatCompletion
from sympy.physics.units import temperature

import config
from config import OPENAI_KEY, GOOGLE_AI_KEY, LOG_PATH, RUN_DATE
from prompt import prompt


class LLMTest:
    def __init__(self, llm: str, *args, **kwargs):
        self.llm = llm
        # logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(level=logging.DEBUG)
        if not self.logger.handlers:
            os.makedirs(os.path.dirname(f"{LOG_PATH}/{RUN_DATE}/"), exist_ok=True)
            handler = logging.FileHandler(f"{LOG_PATH}/{RUN_DATE}/{datetime.now().strftime('%Y%m%d-%H%M%S')}-LLM.log",encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.addHandler(console)
        self.usage = []

    def send_message(self, message, role_message):
        pass

    def generate_checklist(self, nl_prompt):
        pass

    def generate_skeleton(self, language, technical_stack, nl_checklist):
        pass

    def generate_answer(self, language, prompt, technical_stack):
        pass

    def get_parameter(self, answer, technical_stack, parameter_required):
        '''
        Get parameters for the testcode.
        You can override this function to manually provide parameters which are required by the testcode.
        :param answer:
        :param technical_stack:
        :param parameter_required:
        :return:
        '''
        pass

    def get_information(self, answer, technical_stack, project_root):
        '''
        Get any information that may use for the project judge.
        NOTE: initiate command will always be requested in this function. However, we do recommend that give the initiate command manually as most of the LLM can't do it correctly
        You can override this function to manually provide parameters which are required by the testcode.
        :param answer:
        :param technical_stack:
        :param project_root:
        :return:
        '''
        pass

    def json_to_file(self, answer):
        """
        Transform the answer into files so that the judge can run the project.
        :param answer: The answer should follow the JSON format of [{"file": <filename>, "path": <filepath>, "code": <content>}, {...}, ... ]

        :return: None
        """
        for file in answer:
            filepath = file["path"]
            last_slash = filepath.rfind("/")
            if last_slash != -1:
                dirpath = filepath[:last_slash]
                if not os.path.isdir(dirpath):
                    os.makedirs(dirpath)
            with open(filepath, 'w', encoding="utf-8") as f:
                f.write(file["code"])
                f.close()

    @staticmethod
    def parse(rsp, pattern: str = r"```json(.*)```"):
        match = re.search(pattern, rsp, re.DOTALL)
        code_text = match.group(1) if match else rsp
        return code_text




class GPTTest(LLMTest):
    def __init__(self, llm="gpt-4o", *args, **kwargs):
        super(GPTTest, self).__init__(llm, *args, **kwargs)
        self.client:OpenAI = OpenAI(api_key=OPENAI_KEY)
        if "stream" in kwargs:
            self.stream = kwargs["stream"]
        else:
            self.stream = False

    TEMPERATURE_DICT = {
        "gpt-5-mini":1, # gpt-5-mini does not support 0
        "gpt-5": 1, # gpt-5 does not support 0
    }

    # def _list_completions(self, limit: int = 20, before: str = None, after: str = None,**kwargs):
    #     """
    #     l completion 列表。
    #     仅支持在 OpenAI 平台中有启用数据保存的账户。
    #     """
    #
    #     url = "https://api.openai.com/v1/chat/completions"
    #     headers = {
    #         "Authorization": f"Bearer {self.client.api_key}",
    #         "Content-Type": "application/json",
    #     }
    #     # payload = {
    #     #     "model": self.llm,
    #     #     "messages": [{ "role": "user", "content": "Hello" }],
    #     #     **kwargs,  # 允许传入 temperature, max_tokens 等参数
    #     # }
    #     params = {"limit": limit}
    #     if before:
    #         params["before"] = before
    #     if after:
    #         params["after"] = after
    #
    #     response = requests.get(url, headers=headers, params=params, timeout=30)
    #     if not response.ok:
    #         raise RuntimeError(
    #             f"OpenAI API returned {response.status_code}: {response.text}"
    #         )
    #     data = response.json()
    #     if isinstance(data, dict) and "data" in data:
    #         completions = [
    #             ChatCompletion.model_validate(item) for item in data["data"]
    #         ]
    #     else:
    #         completions = [ChatCompletion.model_validate(data)]
    #
    #     return completions

    def send_message(self, message, role_message):
        self.logger.debug("Sending:" + message)
        try:
            completion = self.client.chat.completions.create(
                model=self.llm,
                messages=[
                    {"role": "system",
                     "content": role_message},
                    {"role": "user",
                     "content": message}
                ],
                temperature=self.TEMPERATURE_DICT[self.llm] if self.llm in self.TEMPERATURE_DICT else 0,
                max_tokens=getattr(self,"max_tokens") if hasattr(self,"max_tokens") else NOT_GIVEN,
                stream=self.stream,
                store=True,
                timeout=600,
            )
        except Exception as e:
            if self.__class__ == GPTTest:
                self.logger.error(
                    f"Got error:{e}, if you are using a openai official api, you can input the id of message in https://platform.openai.com/logs?api=chat-completions.\n Or you just type N to continue.")
                completion_id = input("OpenAI completion ID or N:")
                if completion_id == "N":
                    raise ValueError(f"Got error: {e}")
                else:
                    counter = 0
                    while counter < 5:
                        try:
                            completion = self.client.chat.completions.retrieve(completion_id=completion_id)
                            break
                        except Exception as e:
                            self.logger.error(f"Retriving got error:{e}")
                            counter += 1
                    if counter == 5:
                        self.logger.error(f"Got error: {e}")
                    self.logger.info(f"Got completion {completion_id} successfully.")
            else:
                self.logger.error(f"Got error: {e}")

        if self.stream:
            # stream 模式：逐步获取 token
            content = ""
            for event in completion:
                # 每个 event 是 dict
                # 注意在新版 SDK 中 event.type 或 event.choices 可用
                # 安全获取 choices
                choices = getattr(event, "choices", None) or event.get("choices") if isinstance(event, dict) else None
                if choices:
                    delta = choices[0].get("delta", {})
                    token = delta.get("content")
                    if token:
                        content += token
                        # 实时输出或回调
                        self.logger.debug(token)
            # stream 模式完成后记录 usage（如果有）
            if hasattr(completion, "usage"):
                self.usage.append(completion.usage)
                self.logger.debug(f"Usage: {completion.usage}")
            return content
        else:
            self.logger.debug("Received:" + completion.choices[0].message.content)
            if hasattr(completion, "usage"):
                self.usage.append(completion.usage)
                self.logger.debug(f"Usage: {completion.usage}")
            return completion


    def _completion_to_dict(self, s):
        try:
            return json.loads(LLMTest.parse(s))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json(.*)```: {e}")
        try:
            return json.loads(LLMTest.parse(s, pattern=r"```json\n(\[.*?\])\n\```"))
        except Exception as e:
            self.logger.debug(f"Completion to dict failed by using pattern ```json\\n(\\[.*?\\])\\n``` : {e}")
        try:
            return json.loads(s)
        except Exception as e:
            self.logger.debug(f"Completion to dict failed directly: {e}")
            self.logger.debug("Completion to dict: trying replace \\")
        try:
            s = s.replace("\\", "\\\\")
        except Exception as e:
            self.logger.debug(f"Completion to dict failed directly: {e}")
            self.logger.debug("Returning empty string")
            s = ""
        return s

    def completion_to_dict(self, answer):
        s = answer.choices[0].message.content
        return self._completion_to_dict(s)


    def generate_checklist(self, nl_prompt):
        message = prompt[self.__class__.__name__]['generate_checklist'].format(nl_prompt=nl_prompt)
        completion = self.send_message(message, "You are a professional project manager (PM).")
        return self.completion_to_dict(completion)

    def generate_skeleton(self, language, technical_stack, nl_checklist):
        message = prompt[self.__class__.__name__][language.lower() + '_generate_skeleton'].format(
            nl_checklist=nl_checklist,
            technical_stack=technical_stack)
        completion = self.send_message(message, "You are a professional computer program architect.")
        return self.completion_to_dict(completion)

    def generate_answer(self, language, description, technical_stack):
        """
        Generate the answer by using GPT.
        :param description: depends on the level chose by user, the prompt can be natural language description, natural language checklist or programming language framework
        :param technical_stack: decided by user
        :return: generated answer in json format
        """
        message = prompt[self.__class__.__name__][language.lower() + '_generate_answer'].format(description=description,
                                                                            technical_stack=technical_stack if technical_stack else "")
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_parameter(self, answer, technical_stack, parameter_required):
        """
        GPT can automatically recognize the request parameter for the test.
        :param answer: the answer that was given by gpt
        :param technical_stack: decided by user in the "generate answer" step
        :param parameter_required: request by the judge
        :return: generated parameters in json format
        """
        message = prompt[self.__class__.__name__]["generate_parameter"].format(answer=answer,
                                                                               technical_stack=technical_stack if technical_stack else "",
                                                                               parameter_required=parameter_required)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_information(self, answer, technical_stack, project_root):
        """
        GPT can automatically recognize the initial command, requirements and other necessary information.
        :param answer:
        :param technical_stack:
        :return: message
        """
        message = prompt[self.__class__.__name__]["generate_information"].format(answer=answer,
                                                                                 technical_stack=technical_stack if technical_stack else "",
                                                                                 project_root=project_root)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def get_start_file(self, answer, technical_stack, project_root):
        """
        GPT can automatically recognize the entry point of a console project.
        :param answer:
        :param technical_stack:
        :param project_root:
        :return: message
        """
        message = prompt[self.__class__.__name__]["generate_entry_point"].format(answer=answer,
                                                                                 technical_stack=technical_stack if technical_stack else "",
                                                                                 project_root=project_root)
        completion = self.send_message(message, "You are a professional computer programmer.")
        return self.completion_to_dict(completion)

    def mask_skeleton(self, answer, language):
        """
        as masker need to describe the using method of canonical answer, it required LLM to analyze and give brief.
        :param answer:
        :return:
        """
        message = prompt[self.__class__.__name__][f'{language.lower()}_mask_framework'].format(answer=answer)
        completion = self.send_message(message, "You are a professional computer program architect.")
        return self.completion_to_dict(completion)

    def renew_language(self, answer, language):
        """

        """
        # TODO new function



class OllamaTest(GPTTest):
    MODEL_REFLECTION = {
        "gpt-oss-20b": "gpt-oss:20b",
    }
    def __init__(self, llm="llama3.2", device: str = "", *args, **kwargs):
        '''
        This llama test class is created base on Ollama. Ollama supports OpenAI pattern.
        :param llm: any model that Ollama supports can use in this class.
        :param device: If you want to use other GPU rather than GPU:0, set the UUID in this param. Check the UUID by using "nvidia-smi -L".
        '''
        super(OllamaTest, self).__init__(llm)
        OLLAMA_HOST = config.OLLAMA_HOST
        if os.environ.get('DOCKER', '0') == '1':
            if not OLLAMA_HOST:
                self.logger.info("Docker set. Ollama is using host.docker.internal:11434/v1/. If you wish to use your remote server, change OLLAMA_HOST in config.ini.")
                OLLAMA_HOST = "http://host.docker.internal:11434/v1/"
            else:
                self.logger.info(f"Docker set. Ollama is using {OLLAMA_HOST}.")
        else:
            if not OLLAMA_HOST:
                self.logger.info("Ollama is using localhost:11434/v1/. If you wish to use your remote server, change OLLAMA_HOST in config.ini.")
                OLLAMA_HOST = "http://localhost:11434/v1/"
            else:
                self.logger.info(f"Docker set. Ollama is using {OLLAMA_HOST}.")

        if device:
            os.environ['CUDA_VISIBLE_DEVICES'] = device
        os.environ['NO_PROXY'] = "localhost,127.0.0.1"  # Ollama didn't fit the proxy settings which will lead to 502 error.
        self.client = OpenAI(
            base_url=OLLAMA_HOST,
            api_key="llama"  # Required but ignored
        )
        del os.environ['NO_PROXY']
        if device:
            del os.environ['CUDA_VISIBLE_DEVICES']

class DeepSeekTest(GPTTest):
    DEEPSEEK_MAX_TOKENS = {
        "deepseek-chat": 8000,
        "deepseek-reason": 64000,
    }
    def __init__(self, llm="deepseek-chat", device: str = "", *args, **kwargs):
        '''
        This deepseek test class is created base on DeepSeek.
        :param llm:
        :param device:
        :param args:
        :param kwargs:
        '''
        super(DeepSeekTest, self).__init__(llm)
        DEEPSEEK_HOST = config.DEEPSEEK_HOST
        self.client = OpenAI(api_key=config.DEEPSEEK_KEY, base_url=DEEPSEEK_HOST)
        self.max_tokens = self.DEEPSEEK_MAX_TOKENS.get(llm, NOT_GIVEN)

    def _completion_to_dict(self, s):
        s = super()._completion_to_dict(s)
        result = None
        if type(s) == dict:
            for key in s:
                result = s[key]
                break
        else:
            result = s
        return result


class GeminiTest(GPTTest):
    def __init__(self, llm="gemini-1.5-flash",  *args, **kwargs):
        super(GeminiTest, self).__init__(llm)
        self.client = genai.Client(api_key=GOOGLE_AI_KEY)

    def send_message(self, message, role_message):
        self.logger.debug("Sending:" + message)
        completion = self.client.models.generate_content(
            model=self.llm,
            contents = message,
        )
        self.logger.debug("Received:" + completion.text)
        time.sleep(1)
        return completion

    def completion_to_dict(self, answer):
        s = answer.text
        return self._completion_to_dict(s)

class VLLMTest(GPTTest):
    def __init__(self, llm="gpt-oss", *args, **kwargs):
        super(VLLMTest, self).__init__(llm,*args, **kwargs)
        self.client = None
        self.VLLM_HOST = config.VLLM_HOST
        if not self.VLLM_HOST:
            self.logger.info(
                "Vllm is using localhost:11434/v1/. If you wish to use your remote server, change VLLM_HOST in config.ini.")
            self.VLLM_HOST = "http://localhost:11434/v1/"


    VLLM_MAX_TOKENS = {
        "gpt-oss": 100000,
    }

    VLLM_TEMPLATE = {
        "gpt-oss": "<|start|>system<|message|>{role_message}\nKnowledge cutoff: 2024-06\nCurrent date: {date}\nReasoning: medium\nValid channels: analysis, commentary, final. Channel must be included for every message.<|end|><|end|><|start|>user<|message|>{message}<|end|><|start|>assistant\n",
        "Qwen3-30B-A3B-Instruct-2507":"<|im_start|>\nsystem{role_message}\n<im_end|>\n<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant"
    }
    def completion_to_dict(self, answer):
        s = answer
        return self._completion_to_dict(s)

    def send_message(self, message, role_message):
        self.logger.debug("Sending:" + message)
        headers = {
            "Content-Type": "application/json"
        }
        max_token = 8000
        for key in VLLMTest.VLLM_MAX_TOKENS:
            if key in self.llm:
                max_token = VLLMTest.VLLM_MAX_TOKENS[key]
                break
        template = ""
        for key in VLLMTest.VLLM_TEMPLATE:
            if key in self.llm:
                template = VLLMTest.VLLM_TEMPLATE[key]


        payload = {
            "model": config.VLLM_MODEL_PATH + self.llm,
            "prompt": template.format(role_message=role_message,message=message,date=datetime.now().date().isoformat()),
            "max_tokens": max_token,
            "temperature": 0
        }

        response = requests.post(self.VLLM_HOST, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            # 返回生成文本
            completion = response.json()
            # vLLM 的返回可能有 choices 列表
            self.logger.debug("Received:" + completion["choices"][0]["text"])
            text = completion["choices"][0]["text"].split("assistantfinal")[-1]
            return text
        else:
            self.logger.debug(f"Error {response.status_code}: {response.text}")
            return None
