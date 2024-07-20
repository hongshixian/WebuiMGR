import argparse
import glob
import json
import time
import datetime
import gradio as gr
from utils import BaseGradioBox
from utils.process_utils import WebServer, Frpc

time_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
server_port = 35937


class GrMicroServices(BaseGradioBox):
    def __init__(
            self,
            server_name,
            server_port,
            server_cmd,
            server_readme,
            **kwargs
    ):
        super().__init__()
        # server 属性
        self.server_name = server_name
        self.server_port = server_port
        self.server_cmd = server_cmd
        self.server_readme = f"{server_readme}"
        self.server_status = "Status: off"
        self.server_link = f"URL: [http://{self.server_name}.lihao.fun](http://{self.server_name}.lihao.fun)"
        # 后续加上服务的frp子域名用于启动frp服务、url超链接用于页面跳转

        # server
        self.server = WebServer(
            local_port=self.server_port,
            web_cmd=self.server_cmd, proxy_name=self.server_name, time_str=time_str
        )

        # gradio
        self.gr_readme = gr.Markdown(self.server_readme)
        self.gr_status = gr.Markdown(self.server_status)
        self.gr_link = gr.Markdown(self.server_link)
        self.gr_on = gr.Button(value="On", size="sm", min_width=50)
        self.gr_off = gr.Button(value="Off", size="sm", min_width=50)

    def render(self, demo):
        with gr.Column(min_width=200) as self.box:
            with gr.Tabs():
                with gr.TabItem(label=self.server_name):
                    with gr.Column():
                        self.gr_readme.render()
                        self.gr_link.render()
                        self.gr_status.render()
                        with gr.Row():
                            self.gr_on.render()
                            self.gr_off.render()

        # 注册按钮相应
        self.gr_on.click(
            fn=self.turn_on
        ).then(
            fn=self.show_status,
            outputs=self.gr_status
        )

        self.gr_off.click(
            fn=self.turn_off
        ).then(
            fn=self.show_status,
            outputs=self.gr_status
        )

        # 注册页面加载响应
        demo.load(
            fn=self.show_status,
            outputs=self.gr_status
        )

    def turn_on(self):
        self.server.run()
        time.sleep(1)

    def turn_off(self):
        self.server.kill()
        time.sleep(1)

    def show_status(self):
        status = self.server.get_process_status()
        self.server_status = f"Status: {status}"
        return self.server_status


class GrServicesBoard(BaseGradioBox):
    def __init__(self):
        super().__init__()
        # server
        self.server_configs_dir = "configs"
        server_list = []
        config_file_list = glob.glob(f"{self.server_configs_dir}/*.json")
        for config_file in config_file_list:
            with open(config_file) as f:
                json_str = f.read()
                config = json.loads(json_str)
            server_list.append(config)

        self.server_list = server_list

        # gr
        self.gr_server_list = [GrMicroServices(**server_kwargs) for server_kwargs in self.server_list]

    def render(self, demo):
        with gr.Tabs() as self.box:
            with gr.TabItem("ServicesBoard"):
                with gr.Row():
                    for gr_server in self.gr_server_list:
                        gr_server.render(demo)


if __name__ == "__main__":
    print("时间：", time_str)

    mgr_frpc = Frpc(
        local_port=server_port,
        proxy_name="webuimgr",
        time_str=time_str
    )
    mgr_frpc.run()

    gr_services_board = GrServicesBoard()

    with gr.Blocks(title="My LLMs Web UI") as demo:
        md = """# <center>My LLMs Web UI</center>"""
        gr.Markdown(md)
        gr.Markdown(time_str)
        gr_services_board.render(demo)

    demo.queue()
    demo.launch(server_name="127.0.0.1", server_port=server_port, max_threads=1)
