import gradio as gr


class BaseGradioBox:
    def __init__(self):
        self.box = None

    def render(self):
        raise NotImplementedError()
