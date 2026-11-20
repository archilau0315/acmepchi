import sys
import shutil
import os

ORIG_RES = r"e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_2002.json"      # 原始资源（含4字节头）
NEW_JSON = r"e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_2002.new.json"  # 新 JSON 正文


def main(target):
    orig = open(ORIG_RES, "rb").read()
    header, payload = orig[:4], orig[4:]
    total = len(orig)

    body = open(NEW_JSON, "rb").read()
    if len(body) > len(payload):
        raise SystemExit("新内容过长：%d > %d" % (len(body), len(payload)))

    # 在末尾 } 前补空格，保持 JSON 合法且长度不变
    idx = body.rfind(b"}")
    padded = body[:idx] + b" " * (len(payload) - len(body)) + body[idx:]
    assert len(padded) == len(payload)

    data = open(target, "rb").read()
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

    if target.lower().endswith(".mui") and "test" not in os.path.basename(target).lower():
        bak = target + ".bak-zhpatch"
        if not os.path.exists(bak):
            shutil.copy2(target, bak)
            print("已备份", bak)

    out = bytearray(data)
    out[pos:pos + len(payload)] = padded
    # 保留原始 4 字节头（值不变）
    open(target, "wb").write(bytes(out))
    print("已写入 %s offset=%d payload=%d" % (target, pos + 4, len(padded)))


main(sys.argv[1])
