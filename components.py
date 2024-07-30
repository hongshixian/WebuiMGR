import gradio as gr


class ChatBotWithLLM:
    def __init__(self, model_name, adapter):
        # 由，自有成员、渲染、响应函数，三部分组成
        # 静态组件
        # 所有功能自治
        # 不由外部控制
        self.model_name = model_name
        self.adapter = adapter
        self.box = self.render_box()

    def render_box(self):
        with gr.Column() as box:
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbot",
                bubble_full_width=False,
            )

            with gr.Row():
                clear_btn = gr.Button("清空", variant="secondary")
                txt = gr.Textbox(
                    scale=4,
                    show_label=False,
                    placeholder="Enter text and press enter",
                    container=False,
                )
                submit_btn = gr.Button("提交", variant="primary")

            # 提交的响应
            btn_msg = gr.on(
                triggers=[txt.submit, submit_btn.click],
                fn=self.add_text, inputs=[chatbot, txt], outputs=[chatbot, txt],
                queue=False
            )
            btn_msg = btn_msg.then(self.bot, [chatbot, self.adapter], chatbot, api_name="bot_response")
            btn_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)

            # 清空聊天记录
            clear_btn.click(self.clear_text, None, chatbot)

        return box

    @staticmethod
    def add_text(history, text):
        history = history + [(text, None)]
        return history, gr.Textbox(value="", interactive=False)

    def bot(self, history, adapter):
        history = adapter.gradio_chat(self.model_name, history)
        return history

    @staticmethod
    def clear_text():
        return []


class ChatTabs:
    def __init__(self, model_list, adapter):
        self.adapter = adapter
        self.model_list = model_list
        self.tab_list = []
        self.box = self.rander_box()

    def rander_box(self):
        with gr.Tabs() as box:
            for model_name in self.model_list:
                with gr.TabItem(model_name) as tab:
                    cp = ChatBotWithLLM(model_name, self.adapter)
                    self.tab_list.append(cp.box)

        return box


class ModelCard:
    def __init__(self, model_name, adapter):
        # 由，自有成员、渲染、响应函数，三部分组成
        # 静态组件
        # 所有功能自治
        # 不由外部控制
        self.model_name = model_name
        self.adapter = adapter
        self.start_btn = None
        self.stop_btn = None
        self.start_msg = None
        self.stop_msg = None
        self.box = self.rander_box()

    def rander_box(self):
        name = f"{self.model_name}"
        info = f"模型信息暂略"


        with gr.Accordion(name, open=False) as box:
            model_info = gr.Markdown(info)
            with gr.Row():
                self.stop_btn = gr.Button("停止", variant="stop", size="sm", min_width=20)
                self.start_btn = gr.Button("启动", variant="primary", size="sm", min_width=20)

        self.stop_msg = self.stop_btn.click(fn=self.stop_model, inputs=self.adapter, outputs=box)
        self.start_msg = self.start_btn.click(fn=self.start_model, inputs=self.adapter, outputs=box)

        return box

    def start_model(self, adapter):
        res = adapter.load_model(self.model_name)
        gr.Info(str(res))
        return gr.update()

    def stop_model(self, adapter):
        res = adapter.kill_model(self.model_name)
        gr.Info(str(res))
        return gr.update()


class ModelPool:
    def __init__(self, all_model_list, pool_name, adapter):
        # 由，自有成员、渲染、响应函数，三部分组成
        # 静态组件
        # 所有功能自治
        # 不由外部控制
        self.pool_name = pool_name
        self.all_model_list = all_model_list
        self.card_list = []
        self.start_btn_list = []
        self.stop_btn_list = []
        self.click_msg_list = []
        self.box = self.rander_box(adapter)

    def rander_box(self, adapter):
        with gr.Tabs() as box:
            with gr.TabItem(self.pool_name):
                for model_name in self.all_model_list:
                    card = ModelCard(model_name, adapter)
                    self.card_list.append(card.box)
                    self.start_btn_list.append(card.start_btn)
                    self.stop_btn_list.append(card.stop_btn)
                    self.click_msg_list.append(card.start_msg)
                    self.click_msg_list.append(card.stop_msg)
        return box


class WebUI:
    def __init__(self, model_adapter):
        # 先获取模型信息
        model_info = model_adapter.get_model_list()
        self.registed_model_list = model_info.get("registed_models")

        # 组件
        self.comp_adapter = None
        self.unloaded_cards = None
        self.loaded_cards = None
        self.chat_tabs = None
        self.update_boxes = None
        self.click_msg_list = []

        # 渲染
        self.demo = self.render(model_adapter)

    def render(self, model_adapter):
        with gr.Blocks(title="My LLMs Web UI") as demo:
            md = """# <center>My LLMs Web UI</center>"""
            gr.Markdown(md)
            self.comp_adapter = gr.State(model_adapter)
            with gr.Column():
                with gr.Row():
                    with gr.Column(scale=1):
                        self.loaded_cards = ModelPool(self.registed_model_list, "正在运行模型", self.comp_adapter)
                        self.unloaded_cards = ModelPool(self.registed_model_list, "未加载模型", self.comp_adapter)
                    with gr.Column(scale=4):
                        self.chat_tabs = ChatTabs(self.registed_model_list, self.comp_adapter)

            self.update_boxes = self.loaded_cards.card_list + self.unloaded_cards.card_list + self.chat_tabs.tab_list
            self.click_msg_list += self.loaded_cards.click_msg_list
            self.click_msg_list += self.unloaded_cards.click_msg_list

            # self.update_triggers += [btn.click for btn in self.loaded_cards.start_btn_list]
            # self.update_triggers += [btn.click for btn in self.loaded_cards.stop_btn_list]
            # self.update_triggers += [btn.click for btn in self.unloaded_cards.start_btn_list]
            # self.update_triggers += [btn.click for btn in self.unloaded_cards.stop_btn_list]

            # 每5秒更新模型状态
            demo.load(
                fn=self.update_model_status,
                inputs=self.comp_adapter,
                outputs=self.update_boxes,
                # every=10
            )

            # click后更新模型状态
            for click_msg in self.click_msg_list:
                click_msg.then(
                    fn=self.update_model_status,
                    inputs=self.comp_adapter,
                    outputs=self.update_boxes,
                )

        return demo

    @staticmethod
    def update_model_status(adapter):
        model_info = adapter.get_model_list()

        registed_models = model_info.get("registed_models")
        loaded_models = model_info.get("loaded_models")
        unloaded_models = list(set(registed_models) - set(loaded_models))

        loaded_cards = [gr.update(visible=True) if model in loaded_models else gr.update(visible=False)
                        for model in registed_models]
        unloaded_cards = [gr.update(visible=True) if model not in loaded_models else gr.update(visible=False)
                          for model in registed_models]
        chat_tab = loaded_cards

        return loaded_cards + unloaded_cards + chat_tab

    def launch(self, **kwargs):
        self.demo.queue()
        self.demo.launch(**kwargs)
