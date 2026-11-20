import json
import struct
import sys

SRC = sys.argv[1]          # 含 4 字节头的 JSNL 资源
OUT_JSON = sys.argv[2]

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
            if rest in (en, en + "s", en + "es"):
                return "全选" + zh
    return text


def main():
    raw = open(SRC, "rb").read()
    n = struct.unpack("<I", raw[:4])[0]
    obj = json.loads(raw[4:4 + n].rstrip(b"\x00").decode("utf-8"))
    changed = 0
    for g in obj.get("STRS", []):
        for it in g.get("items", []):
            if "text" in it:
                new = translate_text(it["text"])
                if new != it["text"]:
                    it["text"] = new
                    changed += 1
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    open(OUT_JSON, "wb").write(body)
    print("groups=%d changed=%d bytes=%d (orig payload=%d)" % (len(obj.get("STRS", [])), changed, len(body), n))


main()
