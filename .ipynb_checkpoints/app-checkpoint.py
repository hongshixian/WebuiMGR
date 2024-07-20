import argparse
from components import WebUI
from adapter import ModelAdapter


if __name__ == "__main__":
    model_adapter = ModelAdapter()

    ui = WebUI(model_adapter)
    ui.launch(server_name="0.0.0.0", server_port=23452, max_threads=2)
