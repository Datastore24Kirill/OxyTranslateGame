"""Opt-in download and recognition check using synthetic, non-private text."""
import argparse
from pathlib import Path
from threading import Event
import unicodedata
import cv2
from engines import LocalEngines
from ocr_models import install

def letters(s):return ''.join(c for c in s if unicodedata.category(c).startswith(('L','N')))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--model-dir',required=True);parser.add_argument('--download',action='store_true');args=parser.parse_args()
 engine=LocalEngines(Path(args.model_dir));expected={'ja':'こんにちは、世界。冒険を始めよう。','ko':'안녕하세요. 새로운 모험을 시작합니다.','zh':'你好世界。我们开始新的冒险。'}
 for lang,text in expected.items():
  if args.download:install(engine.directory,lang,lambda message:None,Event())
  image=cv2.imread(str(Path(__file__).parent/'tests/fixtures'/f'{lang}.png'))
  actual=engine.read(image,lang)
  if letters(actual)!=letters(text):raise RuntimeError(f'{lang}: recognition fixture mismatch: {actual!r}')
  print(lang,'OCR fixture passed',flush=True)
if __name__=='__main__':main()
