import argparse
from crawler import handler

parser = argparse.ArgumentParser(description="scrapper tool")

parser.add_argument("--save_path", type=str)
parser.add_argument("--url", type=str)
args = parser.parse_args()
url = args.url
path = args.save_path
handler(url=url, path=path)
