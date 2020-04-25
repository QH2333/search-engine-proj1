import time
import hanlp
import jieba
import pkuseg
import pynlpir
import thulac
hanlp_seg = hanlp.load('PKU_NAME_MERGED_SIX_MONTHS_CONVSEG')
pkuseg_seg = pkuseg.pkuseg()
thu_seg = thulac.thulac(seg_only=True)

content = ""

with open("data.txt", "r", encoding="UTF-8") as f:
    content = f.read()

print("__HanLP__")
t1 = time.time()
for i in range(10):
    hanlp_seg(content)
t2 = time.time()
print("Avg: %f" % ((t2 - t1) / 10))

print("__jieba__")
t1 = time.time()
for i in range(10):
    jieba.cut_for_search(content)
t2 = time.time()
print("Avg: %f" % ((t2 - t1) / 10))

print("__pkuseg__")
t1 = time.time()
for i in range(10):
    pkuseg_seg.cut(content)
t2 = time.time()
print("Avg: %f" % ((t2 - t1) / 10))

print("__pynlpir__")
pynlpir.open()
t1 = time.time()
for i in range(10):
    pynlpir.segment(content)
t2 = time.time()
print("Avg: %f" % ((t2 - t1) / 10))

print("__thulac__")
t1 = time.time()
for i in range(10):
    thu_seg.cut(content, text=True)
t2 = time.time()
print("Avg: %f" % ((t2 - t1) / 10))