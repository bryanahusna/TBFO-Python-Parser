import argparse
from parser import Parser

argparser = argparse.ArgumentParser()
argparser.add_argument('input')

args = argparser.parse_args()

filename = args.input

parser = Parser()
parser.parse(filename)

print("No error(s) found.")
