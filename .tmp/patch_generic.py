import sys
import shutil
import os

ORIG_RES = sys.argv[1]     # 原始 JSNL 资源（含4字节头）
NEW_JSON = sys.argv[2]     # 新 JSON 正文
TARGET = sys.argv[3]       # 目标 .mui

orig = open(ORIG_RES, "rb").read()
payload = orig[4:]
body = open(NEW_JSON, "rb").read()
if len(body) > len(payload):
    raise SystemExit("新内容过长：%d > %d" % (len(body), len(payload)))

idx = body.rfind(b"}")
padded = body[:idx] + b" " * (len(payload) - len(body)) + body[idx:]
assert len(padded) == len(payload)

data = open(TARGET, "rb").read()
marker = payload[:64]
hits = []
start = 0
while True:
    p = data.find(marker, start)
    if p < 0:
        break
    hits.append(p)
    start = p + 1
if len(hits) != 1:
    raise SystemExit("marker 匹配数=%d，中止" % len(hits))
pos = hits[0]
if data[pos:pos + len(payload)] != payload:
    raise SystemExit("区域内容不一致，中止")

bak = TARGET + ".bak-zhpatch"
if not os.path.exists(bak):
    shutil.copy2(TARGET, bak)
    print("已备份", bak)

out = bytearray(data)
out[pos:pos + len(payload)] = padded
open(TARGET, "wb").write(bytes(out))
print("已写入 %s offset=%d payload=%d" % (TARGET, pos + 4, len(padded)))
