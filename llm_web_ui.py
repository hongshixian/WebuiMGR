import time
import argparse
from vllm import LLM, SamplingParams
from fastchat.model import get_conversation_template
import gradio as gr


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--model', type=str, help='model_id_or_path', required=True)
arg_parser.add_argument('--port', type=int, help='port', required=True)
args = arg_parser.parse_args()


class ChatModel:
    def __init__(self, model_or_repo_id: str, **kwargs):
        # init model
        self.model_id = model_or_repo_id
        self.llm = LLM(model=model_or_repo_id, trust_remote_code=True)
        self.sampler = SamplingParams(**kwargs)
        #
        self._conversation_template = get_conversation_template(self.model_id)

    def generate(self, input_text: str) -> str:
        # generate outputs
        outputs = self.llm.generate([input_text], self.sampler)
        generated_text = outputs[0].outputs[0].text
        return generated_text

    def get_new_conversation_template(self):
        return get_conversation_template(self.model_id)


# model_id = "/home/lihao/git/chatglm2-6b"
model_id = args.model
model = ChatModel(
    model_id,
    temperature=0.7, top_p=0.8, repetition_penalty=1.05, max_tokens=512
)

def predict(input, chatbot, max_length, top_p, temperature, conversation):
    # Prepare your prompts
    prompt = input
    #
    conversation.append_message(conversation.roles[0], prompt)
    conversation.append_message(conversation.roles[1], "")
    chatbot = conversation.to_gradio_chatbot()

    yield chatbot, conversation

    # chat
    input_text = conversation.get_prompt()
    generated_text = model.generate(input_text)
    #
    conversation.update_last_message(generated_text)
    chatbot = conversation.to_gradio_chatbot()

    yield chatbot, conversation


def reset_user_input():
    return gr.update(value='')


def reset_state():
    return [], model.get_new_conversation_template()


if __name__ == "__main__":
    with gr.Blocks() as demo:
        gr.HTML("""<h1 align="center">My ChatBot</h1>""")
        gr.Markdown(f"{model_id.split('/')[-1]}")

        chatbot = gr.Chatbot()
        with gr.Row():
            with gr.Column(scale=4):
                with gr.Column(scale=12):
                    user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=10)
                with gr.Column(min_width=32, scale=1):
                    submitBtn = gr.Button("Submit", variant="primary")
            with gr.Column(scale=1):
                emptyBtn = gr.Button("Clear History")
                max_length = gr.Slider(0, 4096, value=2048, step=1.0, label="Maximum length", interactive=True)
                top_p = gr.Slider(0, 1, value=0.7, step=0.01, label="Top P", interactive=True)
                temperature = gr.Slider(0, 1, value=0.95, step=0.01, label="Temperature", interactive=True)

        conversation = gr.State(model.get_new_conversation_template())

        submitBtn.click(predict,
                        [user_input, chatbot, max_length, top_p, temperature, conversation],
                        [chatbot, conversation],
                        show_progress=True)
        submitBtn.click(reset_user_input, [], [user_input])

        emptyBtn.click(reset_state, outputs=[chatbot, conversation], show_progress=True)

    demo.queue().launch(share=False, inbrowser=True, server_name="0.0.0.0", server_port=args.port)
