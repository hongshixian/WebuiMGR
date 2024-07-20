import requests
import json


class ModelAdapter:
    def __init__(self):
        self.url_root = "http://llmworker.lihao.fun"

    def gradio_chat(self, model_name, chat_bot):
        messages = []
        for a, b in chat_bot:
            if a:
                message = {"role": "user", "content": a}
                messages.append(message)

            if b:
                message = {"role": "assistant", "content": b}
                messages.append(message)

        res_messages = self.complete(model_name, messages)

        # 直接将最后一条回复添加上去
        last_messages = res_messages[-1]
        last_answer = last_messages.get("content")
        chat_bot[-1][1] = last_answer

        return chat_bot

    def complete(self, model_name, messages):
        url_api = "/api/complate"
        full_url = self.url_root + url_api

        header = {"Content-Type": "application/json"}

        body = {
            "model_name": model_name,
            "messages": messages
        }

        response = requests.request(method="POST", url=full_url, headers=header, json=body)
        res_json = response.json()

        return res_json

    def get_model_list(self):
        url_api = "/api/models"
        full_url = self.url_root + url_api
        response = requests.request(method="GET", url=full_url)
        res_json = response.json()

        return res_json

    def get_cuda_info(self):
        url_api = "/api/status"
        full_url = self.url_root + url_api
        response = requests.request(method="GET", url=full_url)
        res_json = response.json()

        return res_json

    def load_model(self, model_name, **kwargs):
        url_api = "/api/load_model"
        full_url = self.url_root + url_api

        header = {"Content-Type": "application/json"}

        body = {
            "model_name": model_name,
            "model_args": kwargs
        }

        response = requests.request(method="POST", url=full_url, headers=header, json=body)
        res_json = response.json()

        return res_json

    def kill_model(self, model_name):
        url_api = "/api/kill_model"
        full_url = self.url_root + url_api

        header = {"Content-Type": "application/json"}

        body = {
            "model_name": model_name
        }

        response = requests.request(method="POST", url=full_url, headers=header, json=body)
        res_json = response.json()

        return res_json


if __name__ == "__main__":
    ma = ModelAdapter()
    model_name = "ChatGLM2-6B"
    chatbota = [["你好", None]]
    model_list = ma.gradio_chat(model_name, chatbota)
    print(model_list)
