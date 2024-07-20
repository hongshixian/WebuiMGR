import signal
import subprocess
import os
import shlex
import time


class Process:
    def __init__(self, cmd, log_dir="logs/test", cold_init=True):
        if isinstance(cmd, str):
            self.cmd = shlex.split(cmd)
        elif isinstance(cmd, list):
            self.cmd = cmd
        else:
            raise ValueError("cmd must be str or list")

        self.log_path = os.path.join(log_dir, f"stdout_{self.cmd[0].split('/')[-1]}.txt")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.stdout = open(self.log_path, mode="wb+")
        self.popen_kwargs = dict(
            args=self.cmd,
            # shell=True,  # 加了这个参数就不正常了
            stdout=self.stdout, stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
        print("Popen cmd:")
        print(self.popen_kwargs)
        if not cold_init:
            self.p = subprocess.Popen(**self.popen_kwargs)
        else:
            self.p = None

    def get_process_status(self):
        if not isinstance(self.p, subprocess.Popen):
            return -1  # 未启动
        elif self.p.poll() is None:
            return 1  # 正在运行
        else:
            return 0  # 运行结束

    def kill(self):
        if isinstance(self.p, subprocess.Popen):
            # self.p.kill()  # 这个内存不释放
            # self.p.terminate()
            # self.p.wait()
            os.killpg(self.p.pid, signal.SIGTERM)

    def run(self):
        if self.get_process_status() != 1:
            self.p = subprocess.Popen(**self.popen_kwargs)

    def read_stdout(self):
        with open(self.log_path) as f:
            stdout = f.read()
        return stdout


class Frpc(Process):
    def __init__(self, local_port, proxy_name, time_str="test"):
        self.local_port = local_port
        self.proxy_name = proxy_name
        self.time_str = time_str
        log_dir = os.path.join("logs", self.time_str, self.proxy_name)
        cmd_template = ("{frpc_cmd} http "
                        "--server_addr win.lihao.fun:7000 --token lihao67 "
                        "--local_ip 127.0.0.1 --local_port {local_port} "
                        "--custom_domain {proxy_name}.lihao.fun --proxy_name wsl-webui-{proxy_name}")
        frpc_cmd = "/home/lihao/frp/frp_0.51.0_linux_amd64/frpc"
        cmd = cmd_template.format(
            frpc_cmd=frpc_cmd,
            local_port=self.local_port,
            proxy_name=self.proxy_name
        )
        super(Frpc, self).__init__(cmd, log_dir=log_dir)
        pass


class MyServer(Process):
    def __init__(self, web_cmd, proxy_name, work_dir=None, time_str="test"):
        self.proxy_name = proxy_name
        self.time_str = time_str
        log_dir = os.path.join("logs", self.time_str, self.proxy_name)
        cmd = web_cmd
        super(MyServer, self).__init__(cmd, log_dir=log_dir)
        pass


class WebServer:
    def __init__(
            self,
            web_cmd,
            local_port,
            proxy_name,
            work_dir=None,
            time_str="test"
    ):
        self.proxy_name = proxy_name
        self.time_str = time_str

        self.frpc = Frpc(local_port, proxy_name, time_str=time_str)
        self.server = MyServer(web_cmd, proxy_name, work_dir=work_dir, time_str=time_str)

    def run(self):
        self.frpc.run()
        self.server.run()

    def kill(self):
        self.frpc.kill()
        self.server.kill()

    def get_process_status(self):
        status_frpc = self.frpc.get_process_status()
        status_server = self.server.get_process_status()
        return {"frpc": status_frpc, "server": status_server}

    def read_stdout(self):
        res_frpc = self.frpc.read_stdout()
        res_server = self.server.read_stdout()
        return "\n".join([res_frpc, res_server])


if __name__ == "__main__":
    # frpc test
    # p_test = Frpc(local_port=89632, proxy_name="frpc_test_1", time_str="test")
    # # webui test
    # p_test = MyServer(web_cmd="ping 127.0.0.1", proxy_name="frpc_test_1", time_str="test")
    p_test = WebServer(
        local_port=89632,
        web_cmd="ping 127.0.0.1", proxy_name="frpc_test_2", time_str="test20240609"
    )
    print(p_test)
    time.sleep(3)
    print(p_test.get_process_status())
    time.sleep(3)
    print(p_test.kill())
    time.sleep(1)
    print(p_test.get_process_status())
    time.sleep(3)
    print(p_test.run())
    time.sleep(1)
    print(p_test.get_process_status())
    time.sleep(3)
    print(p_test.kill())
    time.sleep(1)
    print(p_test.get_process_status())
    time.sleep(1)
    print(p_test.read_stdout())
    print()
