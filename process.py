from multiprocessing import Process, Pipe, Value

class process:
    def __init__(self):
        self.__cont = Value('i',1)
        self.send_pipe = None
        self.recv_pipe = None

    @property
    def cont(self):
        return self.__cont.value

    @cont.setter
    def cont(self,value):
        self.__cont.value = value

    def start(self, *args, **kwargs):
        def run_init(args, kwargs):
            self.run(*args, **kwargs)

        self.p = Process(target=run_init, args=(args, kwargs))
        self.cont = 1
        self.p.start()

    def stop(self):
        self.cont = 0
        self.p.join()

    def terminate(self):
        self.p.terminate()

    def join(self):
        self.p.join()

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def recv(self):
        raise NotImplementedError

    def send(self, data):
        self.send_pipe.send_bytes(data)

# recv_pipe cap send | recv interp send | recv show send

def process_chain(recv_pipe,processes):
    recvs = [recv_pipe]
    sends = []
    for i in range(len(processes)):
        recv,send = Pipe(False)
        recvs.append(recv)
        sends.append(send)

    for i in range(len(processes)):
        processes[i].send_pipe = sends[i]
        processes[i].recv_pipe = recvs[i]
        processes[i].start()
    return recvs[-1]
