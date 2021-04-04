import argparser


class Arguments(argparser.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)
