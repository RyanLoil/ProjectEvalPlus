from django.templatetags.i18n import language

from controller import MaskerController
from llm import GPTTest

if __name__ == '__main__':
    tester = MaskerController(
                answer_path="data/project_eval_answer_java.json",
                model_class=GPTTest,
                llm="gpt-5",
                output_path = "data/masked_java.json",
                language= "Java",
    )
    tester.run()