# coding : utf-8
# @Time : 2025/11/23 17:57 
# @Author : Adolph
# @File : bilibili.py 
# @Software : PyCharm
import hashlib
from urllib.parse import quote_plus


def bili_new_params():
	return {
		"game_id": '7840',
		"sdk_ver": '3.5.0',
		"timestamp": '0',
	}


def bili_encode(params) -> str:
	keys = sorted(params.keys())
	parts = []
	sign_builder = []
	for k in keys:
		v = params[k]
		key_escaped = quote_plus(str(k), safe='')
		parts.append(f"{key_escaped}={quote_plus(str(v), safe='')}")
		sign_builder.append(str(v))
	sign_raw = "".join(sign_builder) + "1eb3dc7d3f62405e8d7a86dcc12f74ac"
	sign_md5 = hashlib.md5(sign_raw.encode()).hexdigest()
	return "&".join(parts) + "&sign=" + sign_md5
