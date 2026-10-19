"""Patch dailycheckin bilibili deprecated API.
在 pip install dailycheckin 之后运行，修复 B站已废弃的分区视频接口，
改用热门视频接口，避免签到崩溃。
"""
import os
import dailycheckin

base = os.path.dirname(dailycheckin.__file__)
path = os.path.join(base, "bilibili", "main.py")

with open(path, encoding="utf-8") as f:
    content = f.read()

replacements = [
    (
        'url = "https://api.bilibili.com/x/web-interface/dynamic/region?ps=" + str(num) + "&rid=" + str(rid)',
        'url = "https://api.bilibili.com/x/web-interface/popular?ps=" + str(num) + "&pn=1"',
    ),
    (
        'for one in ret.get("data", {}).get("archives", [])',
        'for one in (ret.get("data") or {}).get("list", [])',
    ),
    (
        '        url = "https://api.bilibili.com/x/vip/privilege/receive"\n        post_data = {"type": receive_type, "csrf": bili_jct}\n        ret = session.post(url=url, data=post_data).json()\n        return ret',
        '        url = "https://api.bilibili.com/x/vip/privilege/receive"\n        post_data = {"type": receive_type, "csrf": bili_jct}\n        try:\n            ret = session.post(url=url, data=post_data).json()\n        except Exception:\n            ret = {"code": -1, "message": "请求异常"}\n        return ret',
    ),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched bilibili main.py, applied %d/%d replacements" % (count, len(replacements)))
