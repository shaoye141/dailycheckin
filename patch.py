"""Patch dailycheckin bilibili for robustness.
1. 修复 get_region 已废弃的分区视频接口，改用热门视频接口。
2. 用健壮版本整体替换 main 方法，每个子任务独立容错。
3. 同时 patch site-packages 与仓库本地源码，
   覆盖 dailycheckin 命令与本地模块两种加载方式。
"""
import os
import re
import ast
import base64
import sysconfig

robust_b64 = (
    "ICAgIGRlZiBtYWluKHNlbGYpOgogICAgICAgIGJpbGliaWxpX2Nvb2tpZSA9IHsKICAgICAgICAg"
    "ICAgaXRlbS5zcGxpdCgiPSIpWzBdOiAoaXRlbS5zcGxpdCgiPSIpWzFdIGlmIGxlbihpdGVtLnNw"
    "bGl0KCI9IikpID4gMSBlbHNlICIiKQogICAgICAgICAgICBmb3IgaXRlbSBpbiBzZWxmLmNoZWNr"
    "X2l0ZW0uZ2V0KCJjb29raWUiKS5zcGxpdCgiOyAiKQogICAgICAgIH0KICAgICAgICBiaWxpX2pj"
    "dCA9IGJpbGliaWxpX2Nvb2tpZS5nZXQoImJpbGlfamN0IikKICAgICAgICBjb2luX251bSA9IHNl"
    "bGYuY2hlY2tfaXRlbS5nZXQoImNvaW5fbnVtIiwgMCkKICAgICAgICBjb2luX3R5cGUgPSBzZWxm"
    "LmNoZWNrX2l0ZW0uZ2V0KCJjb2luX3R5cGUiLCAxKQogICAgICAgIHNpbHZlcjJjb2luID0gc2Vs"
    "Zi5jaGVja19pdGVtLmdldCgic2lsdmVyMmNvaW4iLCBGYWxzZSkKCiAgICAgICAgc2Vzc2lvbiA9"
    "IHJlcXVlc3RzLnNlc3Npb24oKQogICAgICAgIHJlcXVlc3RzLnV0aWxzLmFkZF9kaWN0X3RvX2Nv"
    "b2tpZWphcihzZXNzaW9uLmNvb2tpZXMsIGJpbGliaWxpX2Nvb2tpZSkKICAgICAgICBzZXNzaW9u"
    "LmhlYWRlcnMudXBkYXRlKAogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAidXNlci1hZ2Vu"
    "dCI6ICJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0KSBBcHBsZVdlYktp"
    "dC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTIwLjAuMC4wIFNhZmFyaS81Mzcu"
    "MzYiLAogICAgICAgICAgICAgICAgIlJlZmVyZXIiOiAiaHR0cHM6Ly93d3cuYmlsaWJpbGkuY29t"
    "LyIsCiAgICAgICAgICAgICAgICAiYWNjZXB0LWxhbmd1YWdlIjogInpoLUNOLHpoO3E9MC45LGVu"
    "O3E9MC44IiwKICAgICAgICAgICAgICAgICJDb25uZWN0aW9uIjogImtlZXAtYWxpdmUiLAogICAg"
    "ICAgICAgICB9CiAgICAgICAgKQoKICAgICAgICBuYXZfZXJyID0gIiIKICAgICAgICBpc19sb2dp"
    "biA9IEZhbHNlCiAgICAgICAgdHJ5OgogICAgICAgICAgICB1bmFtZSwgdWlkLCBpc19sb2dpbiwg"
    "Y29pbiwgdmlwX3R5cGUsIGN1cnJlbnRfZXhwID0gc2VsZi5nZXRfbmF2KHNlc3Npb249c2Vzc2lv"
    "bikKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIG5hdl9lcnIgPSBz"
    "dHIoZSkKCiAgICAgICAgaWYgbm90IGlzX2xvZ2luOgogICAgICAgICAgICByZXR1cm4gIuacqueZ"
    "u+W9leaIlueZu+W9leaAgeWkseaViDogIiArIG5hdl9lcnIKCiAgICAgICAgbWFuaHVhX21zZyA9"
    "IGxpdmVfbXNnID0gIuacquaJp+ihjCIKICAgICAgICByZXBvcnRfbXNnID0gc2hhcmVfbXNnID0g"
    "czJjX21zZyA9IGNvaW5fbXNnID0gIuacquaJp+ihjCIKICAgICAgICBhaWRfbGlzdCA9IFtdCiAg"
    "ICAgICAgbGl2ZV9zdGF0cyA9IFtdCgogICAgICAgIHRyeToKICAgICAgICAgICAgbWFuaHVhX21z"
    "ZyA9IHNlbGYubWFuZ2Ffc2lnbihzZXNzaW9uPXNlc3Npb24pCiAgICAgICAgZXhjZXB0IEV4Y2Vw"
    "dGlvbiBhcyBlOgogICAgICAgICAgICBtYW5odWFfbXNnID0gIuW8guW4uDogIiArIHN0cihlKQoK"
    "ICAgICAgICB0cnk6CiAgICAgICAgICAgIGxpdmVfbXNnID0gc2VsZi5saXZlX3NpZ24oc2Vzc2lv"
    "bj1zZXNzaW9uKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgbGl2"
    "ZV9tc2cgPSAi5byC5bi4OiAiICsgc3RyKGUpCgogICAgICAgIHRyeToKICAgICAgICAgICAgYWlk"
    "X2xpc3QgPSBzZWxmLmdldF9yZWdpb24oc2Vzc2lvbj1zZXNzaW9uKQogICAgICAgIGV4Y2VwdCBF"
    "eGNlcHRpb24gYXMgZToKICAgICAgICAgICAgYWlkX2xpc3QgPSBbXQoKICAgICAgICAjIOWkp+S8"
    "muWRmOadg+ebigogICAgICAgIHRyeToKICAgICAgICAgICAgdmlwX3ByaXZpbGVnZV9teV9yZXQg"
    "PSBzZWxmLnZpcF9wcml2aWxlZ2VfbXkoc2Vzc2lvbj1zZXNzaW9uKQogICAgICAgICAgICB3ZWxm"
    "YXJlX2xpc3QgPSAodmlwX3ByaXZpbGVnZV9teV9yZXQuZ2V0KCJkYXRhIikgb3Ige30pLmdldCgi"
    "bGlzdCIsIFtdKQogICAgICAgICAgICBmb3Igd2VsZmFyZSBpbiB3ZWxmYXJlX2xpc3Q6CiAgICAg"
    "ICAgICAgICAgICBpZiB3ZWxmYXJlLmdldCgic3RhdGUiKSA9PSAwIGFuZCB3ZWxmYXJlLmdldCgi"
    "dmlwX3R5cGUiKSA9PSB2aXBfdHlwZToKICAgICAgICAgICAgICAgICAgICBzZWxmLnZpcF9wcml2"
    "aWxlZ2VfcmVjZWl2ZSgKICAgICAgICAgICAgICAgICAgICAgICAgc2Vzc2lvbj1zZXNzaW9uLAog"
    "ICAgICAgICAgICAgICAgICAgICAgICBiaWxpX2pjdD1iaWxpX2pjdCwKICAgICAgICAgICAgICAg"
    "ICAgICAgICAgcmVjZWl2ZV90eXBlPXdlbGZhcmUuZ2V0KCJ0eXBlIiksCiAgICAgICAgICAgICAg"
    "ICAgICAgKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgcHJpbnQo"
    "InZpcCB3ZWxmYXJlIGVycm9yOiIsIGUpCgogICAgICAgICMg5LuK5pel5bey5oqV5biB5pWwCiAg"
    "ICAgICAgY29pbnNfYXZfY291bnQgPSAwCiAgICAgICAgdHJ5OgogICAgICAgICAgICBjb2luc19h"
    "dl9jb3VudCA9IGxlbigKICAgICAgICAgICAgICAgIGxpc3QoCiAgICAgICAgICAgICAgICAgICAg"
    "ZmlsdGVyKAogICAgICAgICAgICAgICAgICAgICAgICBsYW1iZGEgeDogeC5nZXQoInJlYXNvbiIp"
    "ID09ICLop4bpopHmipXluIHlpZblirEiLAogICAgICAgICAgICAgICAgICAgICAgICBzZWxmLmdl"
    "dF90b2RheV9leHAoc2Vzc2lvbj1zZXNzaW9uKSwKICAgICAgICAgICAgICAgICAgICApCiAgICAg"
    "ICAgICAgICAgICApCiAgICAgICAgICAgICkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6"
    "CiAgICAgICAgICAgIGNvaW5zX2F2X2NvdW50ID0gMAoKICAgICAgICB0YXJnZXRfY29pbl9udW0g"
    "PSBjb2luX251bSAtIGNvaW5zX2F2X2NvdW50CiAgICAgICAgdHJ5OgogICAgICAgICAgICB0YXJn"
    "ZXRfY29pbl9udW0gPSB0YXJnZXRfY29pbl9udW0gaWYgdGFyZ2V0X2NvaW5fbnVtIDwgY29pbiBl"
    "bHNlIGNvaW4KICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCgogICAg"
    "ICAgIHN1Y2Nlc3NfY291bnQgPSAwCiAgICAgICAgaWYgY29pbl90eXBlID09IDEgYW5kIHRhcmdl"
    "dF9jb2luX251bSA+IDA6CiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIGZvbGxvd2lu"
    "Z19saXN0ID0gc2VsZi5nZXRfZm9sbG93aW5ncyhzZXNzaW9uPXNlc3Npb24sIHVpZD11aWQpCiAg"
    "ICAgICAgICAgICAgICBjb3VudCA9IDAKICAgICAgICAgICAgICAgIGZvciBmb2xsb3dpbmcgaW4g"
    "KGZvbGxvd2luZ19saXN0LmdldCgiZGF0YSIpIG9yIHt9KS5nZXQoImxpc3QiKSBvciBbXToKICAg"
    "ICAgICAgICAgICAgICAgICBtaWQgPSBmb2xsb3dpbmcuZ2V0KCJtaWQiKQogICAgICAgICAgICAg"
    "ICAgICAgIGlmIG1pZDoKICAgICAgICAgICAgICAgICAgICAgICAgdG1wbGlzdCwgdG1wY291bnQg"
    "PSBzZWxmLnNwYWNlX2FyY19zZWFyY2goc2Vzc2lvbj1zZXNzaW9uLCB1aWQ9bWlkKQogICAgICAg"
    "ICAgICAgICAgICAgICAgICBhaWRfbGlzdCArPSB0bXBsaXN0CiAgICAgICAgICAgICAgICAgICAg"
    "ICAgIGNvdW50ICs9IHRtcGNvdW50CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIGNvdW50ID4g"
    "dGFyZ2V0X2NvaW5fbnVtOgogICAgICAgICAgICAgICAgICAgICAgICAgICAgcHJpbnQoIuW3suiO"
    "t+WPlui2s+Wkn+WFs+azqOeUqOaIt+eahOinhumikSIpCiAgICAgICAgICAgICAgICAgICAgICAg"
    "ICAgICBicmVhawogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAg"
    "ICAgICBwcmludCgiZm9sbG93aW5ncyBlcnJvcjoiLCBlKQoKICAgICAgICBpZiB0YXJnZXRfY29p"
    "bl9udW0gPiAwOgogICAgICAgICAgICBmb3IgYWlkIGluIGFpZF9saXN0Wzo6LTFdOgogICAgICAg"
    "ICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgICAgIHJldCA9IHNlbGYuY29pbl9hZGQoc2Vz"
    "c2lvbj1zZXNzaW9uLCBhaWQ9YWlkLmdldCgiYWlkIiksIGJpbGlfamN0PWJpbGlfamN0KQogICAg"
    "ICAgICAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBlOgogICAgICAgICAgICAgICAgICAgIHBy"
    "aW50KCJjb2luIGVycm9yOiIsIGUpCiAgICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAg"
    "ICAgICAgIGlmIHJldC5nZXQoImNvZGUiKSA9PSAwOgogICAgICAgICAgICAgICAgICAgIHN1Y2Nl"
    "c3NfY291bnQgKz0gMQogICAgICAgICAgICAgICAgICAgIHRhcmdldF9jb2luX251bSAtPSAxCiAg"
    "ICAgICAgICAgICAgICBlbGlmIHJldC5nZXQoImNvZGUiKSA9PSAzNDAwNToKICAgICAgICAgICAg"
    "ICAgICAgICBjb250aW51ZQogICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAg"
    "ICBwcmludCgi5oqV5biB5aSx6LSlOiIsIHJldC5nZXQoIm1lc3NhZ2UiKSkKICAgICAgICAgICAg"
    "ICAgICAgICBicmVhawogICAgICAgICAgICAgICAgaWYgdGFyZ2V0X2NvaW5fbnVtIDw9IDA6CiAg"
    "ICAgICAgICAgICAgICAgICAgYnJlYWsKICAgICAgICAgICAgY29pbl9tc2cgPSBmIuS7iuaXpeaI"
    "kOWKn+aKleW4gXtzdWNjZXNzX2NvdW50ICsgY29pbnNfYXZfY291bnR9L3tzZWxmLmNoZWNrX2l0"
    "ZW0uZ2V0KCdjb2luX251bScsIDUpfeS4qiIKICAgICAgICBlbHNlOgogICAgICAgICAgICBjb2lu"
    "X21zZyA9IGYi5LuK5pel5oiQ5Yqf5oqV5biBe2NvaW5zX2F2X2NvdW50fS97c2VsZi5jaGVja19p"
    "dGVtLmdldCgnY29pbl9udW0nLCA1KX3kuKoiCgogICAgICAgICMg6KeC55yLICsg5YiG5Lqr77yI"
    "6ZyA6KaB6Iez5bCR5LiA5Liq6KeG6aKR77yJCiAgICAgICAgaWYgYWlkX2xpc3Q6CiAgICAgICAg"
    "ICAgIGZpcnN0ID0gYWlkX2xpc3RbMF0KICAgICAgICAgICAgYWlkID0gZmlyc3QuZ2V0KCJhaWQi"
    "KQogICAgICAgICAgICBjaWQgPSBmaXJzdC5nZXQoImNpZCIpCiAgICAgICAgICAgIHRpdGxlID0g"
    "Zmlyc3QuZ2V0KCJ0aXRsZSIpCiAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgIHJlcG9y"
    "dF9yZXQgPSBzZWxmLnJlcG9ydF90YXNrKHNlc3Npb249c2Vzc2lvbiwgYmlsaV9qY3Q9YmlsaV9q"
    "Y3QsIGFpZD1haWQsIGNpZD1jaWQpCiAgICAgICAgICAgICAgICByZXBvcnRfbXNnID0gZiLop4Ln"
    "nIvjgIp7dGl0bGV944CLMzAw56eSIiBpZiByZXBvcnRfcmV0LmdldCgiY29kZSIpID09IDAgZWxz"
    "ZSAi5Lu75Yqh5aSx6LSlIgogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAg"
    "ICAgICAgICAgICByZXBvcnRfbXNnID0gIuW8guW4uDogIiArIHN0cihlKQogICAgICAgICAgICB0"
    "cnk6CiAgICAgICAgICAgICAgICBzaGFyZV9yZXQgPSBzZWxmLnNoYXJlX3Rhc2soc2Vzc2lvbj1z"
    "ZXNzaW9uLCBiaWxpX2pjdD1iaWxpX2pjdCwgYWlkPWFpZCkKICAgICAgICAgICAgICAgIHNoYXJl"
    "X21zZyA9IGYi5YiG5Lqr44CKe3RpdGxlfeOAi+aIkOWKnyIgaWYgc2hhcmVfcmV0LmdldCgiY29k"
    "ZSIpID09IDAgZWxzZSAi5YiG5Lqr5aSx6LSlIgogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9u"
    "IGFzIGU6CiAgICAgICAgICAgICAgICBzaGFyZV9tc2cgPSAi5byC5bi4OiAiICsgc3RyKGUpCgog"
    "ICAgICAgIGlmIHNpbHZlcjJjb2luOgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBz"
    "MmMgPSBzZWxmLnNpbHZlcjJjb2luKHNlc3Npb249c2Vzc2lvbiwgYmlsaV9qY3Q9YmlsaV9qY3Qp"
    "CiAgICAgICAgICAgICAgICBzMmNfbXNnID0gczJjLmdldCgibWVzc2FnZSIpCiAgICAgICAgICAg"
    "IGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgICAgIHMyY19tc2cgPSAi5byC5bi4"
    "OiAiICsgc3RyKGUpCiAgICAgICAgZWxzZToKICAgICAgICAgICAgczJjX21zZyA9ICLkuI3lhZHm"
    "jaLnoazluIEiCgogICAgICAgIHRyeToKICAgICAgICAgICAgbGl2ZV9zdGF0cyA9IHNlbGYubGl2"
    "ZV9zdGF0dXMoc2Vzc2lvbj1zZXNzaW9uKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToK"
    "ICAgICAgICAgICAgbGl2ZV9zdGF0cyA9IFtdCgogICAgICAgIHRvZGF5X2V4cCA9IDAKICAgICAg"
    "ICBuZXdfY3VycmVudF9leHAgPSAwCiAgICAgICAgdXBkYXRlX2RhdGEgPSAiLSIKICAgICAgICB0"
    "cnk6CiAgICAgICAgICAgIF8sIF8sIF8sIF8sIF8sIG5ld19jdXJyZW50X2V4cCA9IHNlbGYuZ2V0"
    "X25hdihzZXNzaW9uPXNlc3Npb24pCiAgICAgICAgICAgIHRvZGF5X2V4cCA9IHN1bSgKICAgICAg"
    "ICAgICAgICAgIG1hcChsYW1iZGEgeDogeC5nZXQoImRlbHRhIiwgMCksIHNlbGYuZ2V0X3RvZGF5"
    "X2V4cChzZXNzaW9uPXNlc3Npb24pKQogICAgICAgICAgICApCiAgICAgICAgICAgIHVwZGF0ZV9k"
    "YXRhID0gKDI4ODAwIC0gbmV3X2N1cnJlbnRfZXhwKSAvLyAodG9kYXlfZXhwIGlmIHRvZGF5X2V4"
    "cCBlbHNlIDEpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjoKICAgICAgICAgICAgcGFzcwoKICAg"
    "ICAgICBtc2cgPSBbCiAgICAgICAgICAgIHsibmFtZSI6ICLluJDlj7fkv6Hmga8iLCAidmFsdWUi"
    "OiB1bmFtZX0sCiAgICAgICAgICAgIHsibmFtZSI6ICLmvKvnlLvnrb7liLAiLCAidmFsdWUiOiBt"
    "YW5odWFfbXNnfSwKICAgICAgICAgICAgeyJuYW1lIjogIuebtOaSreetvuWIsCIsICJ2YWx1ZSI6"
    "IGxpdmVfbXNnfSwKICAgICAgICAgICAgeyJuYW1lIjogIueZu+mZhuS7u+WKoSIsICJ2YWx1ZSI6"
    "ICLku4rml6Xlt7LnmbvpmYYifSwKICAgICAgICAgICAgeyJuYW1lIjogIuingueci+inhumikSIs"
    "ICJ2YWx1ZSI6IHJlcG9ydF9tc2d9LAogICAgICAgICAgICB7Im5hbWUiOiAi5YiG5Lqr5Lu75Yqh"
    "IiwgInZhbHVlIjogc2hhcmVfbXNnfSwKICAgICAgICAgICAgeyJuYW1lIjogIueTnOWtkOWFkeaN"
    "oiIsICJ2YWx1ZSI6IHMyY19tc2d9LAogICAgICAgICAgICB7Im5hbWUiOiAi5oqV5biB5Lu75Yqh"
    "IiwgInZhbHVlIjogY29pbl9tc2d9LAogICAgICAgICAgICB7Im5hbWUiOiAi5LuK5pel57uP6aqM"
    "IiwgInZhbHVlIjogdG9kYXlfZXhwfSwKICAgICAgICAgICAgeyJuYW1lIjogIuW9k+WJjee7j+mq"
    "jCIsICJ2YWx1ZSI6IG5ld19jdXJyZW50X2V4cH0sCiAgICAgICAgICAgIHsibmFtZSI6ICLljYfn"
    "uqfov5jpnIAiLCAidmFsdWUiOiBmInt1cGRhdGVfZGF0YX3lpKkifSwKICAgICAgICAgICAgKmxp"
    "dmVfc3RhdHMsCiAgICAgICAgXQogICAgICAgIG1zZyA9ICJcbiIuam9pbihmIntvbmUuZ2V0KCdu"
    "YW1lJyl9OiB7b25lLmdldCgndmFsdWUnKX0iIGZvciBvbmUgaW4gbXNnKQogICAgICAgIHJldHVy"
    "biBtc2cK"
)
robust_main = base64.b64decode(robust_b64).decode("utf-8")

MAIN_PATTERN = re.compile(r"    def main\(self\):.*?(?=\nif __name__)", re.DOTALL)


def find_targets():
    targets = []
    # 1. site-packages（dailycheckin 命令实际加载位置）
    purelib = sysconfig.get_paths().get("purelib")
    if purelib:
        p = os.path.join(purelib, "dailycheckin", "bilibili", "main.py")
        if os.path.exists(p):
            targets.append(p)
    # 2. 仓库本地源码（python patch.py 时 import 可能命中的位置）
    local = os.path.join(os.getcwd(), "dailycheckin", "bilibili", "main.py")
    if os.path.exists(local) and local not in targets:
        targets.append(local)
    return targets


def patch_one(path):
    with open(path, encoding="utf-8") as f:
        c = f.read()

    # 修复 get_region 废弃接口
    c = c.replace(
        'url = "https://api.bilibili.com/x/web-interface/dynamic/region?ps=" + str(num) + "&rid=" + str(rid)',
        'url = "https://api.bilibili.com/x/web-interface/popular?ps=" + str(num) + "&pn=1"',
    )
    c = c.replace(
        'for one in ret.get("data", {}).get("archives", [])',
        'for one in (ret.get("data") or {}).get("list", [])',
    )

    # 健壮版本替换 main
    if MAIN_PATTERN.search(c):
        new_main = robust_main.rstrip("\n")
        c = MAIN_PATTERN.sub(lambda m: new_main, c)
        replaced = True
    else:
        replaced = False

    # 语法校验
    try:
        ast.parse(c)
        syn = "OK"
    except Exception as e:
        syn = "ERR " + str(e)

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)

    print(f"Patched: {path}")
    print(f"  replaced={replaced} syntax={syn}")


targets = find_targets()
print("DIAG targets:", len(targets))
for t in targets:
    print("DIAG target:", t)
for t in targets:
    patch_one(t)
