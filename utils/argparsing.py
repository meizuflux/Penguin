import shlex
import argparse

class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)

text = "-c --total --cash --bank"

parser = Arguments(allow_abbrev=False, add_help=False)
parser.add_argument('-c', '-cash', '--cash', action='store_true', default=False)
parser.add_argument('--bank', action='store_true', default=False)
parser.add_argument('--total', action='store_true', default=True)

try:
    args = parser.parse_args(shlex.split(text, True))
except RuntimeError as e:
    print(str(e))
else:
    amount = args.total + args.bank + args.total
    if amount != 2:
        raise parser.error("Only one flag is allowed!")
    print(amount)
