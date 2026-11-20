import json
import struct
import io
import sys

ZH = r"e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_2002.json"
EN = r"e:\works\Aidev\AddOn\acmepchi\.tmp\enres\JSNL_#2002.bin"
OUT_JSON = r"e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_2002.new.json"
OUT_BIN = r"e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_2002.new.bin"

BASE = {
    "Duct Route": "风管路线",
    "Duct Flexible Segment": "风管软管段",
    "Duct Rigid Segment": "风管刚性段",
    "Duct Elbow": "风管弯头",
    "Duct Branch": "风管分支",
    "Duct Terminal": "风管末端",
    "Duct Transition": "风管变径",
    "Duct Accessory": "风管附件",
    "Duct Fitting": "风管配件",
    "Duct Take-Off": "风管支管",
    "Pipe Route": "管道路线",
    "Pipe Flexible Segment": "管道软管段",
    "Pipe Rigid Segment": "管道刚性段",
    "Pipe Elbow": "管道弯头",
    "Pipe Branch": "管道分支",
    "Pipe Terminal": "管道末端",
    "Pipe Transition": "管道变径",
    "Pipe Accessory": "管道附件",
    "Pipe Fitting": "管道配件",
    "Cable Carrier Route": "桥架路线",
    "Cable Carrier Rigid Segment": "桥架刚性段",
    "Cable Carrier Elbow": "桥架弯头",
    "Cable Carrier Branch": "桥架分支",
    "Cable Carrier Transition": "桥架变径",
    "Cable Carrier Reducer": "桥架变径",
    "Cable Carrier Fitting": "桥架配件",
    "Equipment": "设备",
    "Electrical Panel": "电气配电盘",
    "Electrical Device": "电气设备",
    "Electrical Circuit": "电气回路",
    "Segment": "段",
    "Node": "节点",
}

SUFFIX = [
    (" Tool", "工具"),
    (" Default Settings", "默认设置"),
    (" Selection Settings", "选择设置"),
    (" Settings", "设置"),
    (" ID", " ID"),
]


def load(path, has_header):
    raw = open(path, "rb").read()
    if has_header:
        n = struct.unpack("<I", raw[:4])[0]
        body = raw[4:4 + n]
    else:
        body = raw
    body = body.rstrip(b"\x00")
    return json.loads(body.decode("utf-8"))


def translate_text(text):
    if text in BASE:
        return BASE[text]
    for en, zh in BASE.items():
        if text == en + " Tool":
            return zh + "工具"
        if text == en + " Default Settings":
            return zh + "默认设置"
        if text == en + " Selection Settings":
            return zh + "选择设置"
        if text == en + " Settings":
            return zh + "设置"
        if text == en + " ID":
            return zh + " ID"
        if text.startswith("Select All "):
            rest = text[len("Select All "):]
            if rest == en or rest == en + "s" or rest == en + "es":
                return "全选" + zh
    return text


def main():
    zh = load(ZH, True)
    en = load(EN, True)

    groups = zh["STRS"]
    have = {g["#id"] for g in groups}

    # 补齐 en 中存在、zh-CN 缺失的电气工具组
    for g in en["STRS"]:
        if g["#id"] in ("50301", "50302") and g["#id"] not in have:
            groups.append(json.loads(json.dumps(g)))
            have.add(g["#id"])

    changed = 0
    for g in groups:
        for it in g.get("items", []):
            if "text" not in it:
                continue
            new = translate_text(it["text"])
            if new != it["text"]:
                it["text"] = new
                changed += 1

    body = json.dumps(zh, ensure_ascii=False).encode("utf-8")
    open(OUT_JSON, "wb").write(body)
    open(OUT_BIN, "wb").write(struct.pack("<I", len(body)) + body)
    print("groups=%d changed=%d bytes=%d" % (len(groups), changed, len(body)))


main()
