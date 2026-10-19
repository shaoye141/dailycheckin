"""Patch dailycheckin for robustness.
1. 修复 B站已废弃的分区视频接口，改用热门视频接口。
2. 通用加固所有 data 为 None 的访问，避免风控/国外 IP 崩溃。
3. 让核心异常处理打印完整 traceback，便于定位。
"""
import os
import re
import dailycheckin

base = os.path.dirname(dailycheckin.__file__)

# ---------- 1. Patch bilibili main.py ----------
bili_path = os.path.join(base, "bilibili", "main.py")
with open(bili_path, encoding="utf-8") as f:
    c = f.read()

# 废弃接口替换为热门接口
c = c.replace(
    'url = "https://api.bilibili.com/x/web-interface/dynamic/region?ps=" + str(num) + "&rid=" + str(rid)',
    'url = "https://api.bilibili.com/x/web-interface/popular?ps=" + str(num) + "&pn=1"',
)
c = c.replace(
    "for one in ret.get(\"data\", {}).get(\"archives\", [])",
    "for one in (ret.get(\"data\") or {}).get(\"list\", [])",
)

# 通用加固: X.get("data", {}).get(  -> (X.get("data") or {}).get(
c = re.sub(
    r'(\w+)\.get\("data", ?\{\}\)\.get\(',
    r'(\1.get("data") or {}).get(',
    c,
)

# 通用加固: session.get(url=url).json().get("data").get("list")
c = re.sub(
    r'(session\.get\(url=url\)\.json\(\))\.get\("data"\)\.get\("list"\)',
    r'(\1.get("data") or {}).get("list") or []',
    c,
)

# vip_privilege_receive 请求容错
c = c.replace(
    '        url = "https://api.bilibili.com/x/vip/privilege/receive"\n        post_data = {"type": receive_type, "csrf": bili_jct}\n        ret = session.post(url=url, data=post_data).json()\n        return ret',
    '        url = "https://api.bilibili.com/x/vip/privilege/receive"\n        post_data = {"type": receive_type, "csrf": bili_jct}\n        try:\n            ret = session.post(url=url, data=post_data).json()\n        except Exception:\n            ret = {"code": -1, "message": "请求异常"}\n        return ret',
)

with open(bili_path, "w", encoding="utf-8") as f:
    f.write(c)
print("Patched bilibili main.py")

# ---------- 2. Patch core main.py to print traceback ----------
core_path = os.path.join(base, "main.py")
with open(core_path, encoding="utf-8") as f:
    core = f.read()

needle = '''                except Exception as e:
                    content_list.append(f"「{check_name}」\\n{e}")
                    print(f"第 {index + 1} 个账号: ❌❌❌❌❌\\n{e}")'''
replacement = '''                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    content_list.append(f"「{check_name}」\\n{e}")
                    print(f"第 {index + q} 个账号: ❌❌❌❌❌\\n{e}")'''
if needle in core:
    core = core.replace(needle, replacement)
    with open(core_path, "w", encoding="utf-8") as f:
        f.write(core)
    print("Patched core main.py to print traceback")
else:
    print("core needle not found (may already be patched)")
