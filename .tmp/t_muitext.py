from acme_lp import muitext
from pathlib import Path
p = Path(r"e:\works\Aidev\AddOn\acmepchi\.tmp\muitext_test\en.mui")
q = Path(r"e:\works\Aidev\AddOn\acmepchi\.tmp\muitext_test\zh.mui")
a, b = p.stat().st_size, q.stat().st_size
h1, h2 = muitext.patch_file(p), muitext.patch_file(q)
print("hits", h1, h2, "size", a, p.stat().st_size, b, q.stat().st_size)
needle = "\u98ce\u7ba1\u8def\u7ebf".encode("utf-8")
print("zh?", needle in p.read_bytes(), needle in q.read_bytes())
print("rerun", muitext.patch_file(p))
