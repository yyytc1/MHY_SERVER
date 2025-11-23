# coding : utf-8
# @Time : 2025/11/14 21:55 
# @Author : Adolph
# @File : stringFunc.py 
# @Software : PyCharm
import base64
import binascii
import hashlib
import hmac
import json
import random
import string
import time
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def get_random_digit(n: int) -> str:
	return str(random.randint(10 ** (n - 1), 10 ** n - 1))


def get_sign(app_id, channel_id, data, device):
	str_bytes = f"app_id={app_id}&channel_id={channel_id}&data={data}&device={device}".encode()
	
	if app_id == 11:
		key = b"d74818dabd4182d4fbac7f8df1622648"
	else:
		key = b"4650f3a396d34d576c3d65df26415394"
	
	signature = hmac.new(key, str_bytes, hashlib.sha256).digest()
	return binascii.hexlify(signature).decode()


def rsa_encrypt(city: int | str, message: str, key: str | None = None) -> str:
	city = int(city)
	if key is None:
		if city == 1:
			PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
			MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDDvekdPMHN3AYhm/vktJT+YJr7
			cI5DcsNKqdsx5DZX0gDuWFuIjzdwButrIYPNmRJ1G8ybDIF7oDW2eEpm5sMbL9zs
			9ExXCdvqrn51qELbqj0XxtMTIpaCHFSI50PfPpTFV9Xt/hmyVwokoOXFlAEgCn+Q
			CgGs52bFoYMtyi+xEQIDAQAB
			-----END PUBLIC KEY-----"""
		elif city == 6:
			PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
			MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDjb4V7EidX/ym28t2ybo0U6t0n
			6p4ej8VjqKHg100va6jkNbNTrLQqMCQCAYtXMXXp2Fwkk6WR+12N9zknLjf+C9sx
			/+l48mjUU8RqahiFD1XT/u2e0m2EN029OhCgkHx3Fc/KlFSIbak93EH/XlYis0w+
			Xl69GV6klzgxW6d2xQIDAQAB
			-----END PUBLIC KEY-----"""
		else:
			PUBLIC_KEY_PEM ="""-----BEGIN PUBLIC KEY-----
			MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4PMS2JVMwBsOIrYWRluY
			wEiFZL7Aphtm9z5Eu/anzJ09nB00uhW+ScrDWFECPwpQto/GlOJYCUwVM/raQpAj
			/xvcjK5tNVzzK94mhk+j9RiQ+aWHaTXmOgurhxSp3YbwlRDvOgcq5yPiTz0+kSeK
			ZJcGeJ95bvJ+hJ/UMP0Zx2qB5PElZmiKvfiNqVUk8A8oxLJdBB5eCpqWV6CUqDKQ
			KSQP4sM0mZvQ1Sr4UcACVcYgYnCbTZMWhJTWkrNXqI8TMomekgny3y+d6NX/cFa6
			6jozFIF4HCX5aW8bp8C8vq2tFvFbleQ/Q3CU56EWWKMrOcpmFtRmC18s9biZBVR/
			8QIDAQAB
			-----END PUBLIC KEY-----"""
	else:
		PUBLIC_KEY_PEM = key
	"""RSA PKCS#1 v1.5 加密并返回 Base64 字符串"""
	# 1. 加载 PEM 公钥
	public_key = serialization.load_pem_public_key(
		PUBLIC_KEY_PEM.encode(),
		backend=default_backend()
	)
	
	# 2. 加密
	encrypted = public_key.encrypt(
		message.encode("utf-8"),
		padding.PKCS1v15()
	)
	
	# 3. Base64 编码
	return base64.b64encode(encrypted).decode("utf-8")


def random_unity_ua():
	unity_versions = [
		"2018.4.36f1",
		"2019.4.34f1",
		"2019.4.40f1",
		"2020.3.48f1",
		"2021.3.20f1",
		"2022.3.5f1",
	]
	
	unity_webreq_versions = [
		"1.0", "1.1", "1.2", "2.0"
	]
	
	libcurl_versions = [
		"7.58.0", "7.64.1", "7.75.0", "7.82.0", "7.85.0", "7.75.0-DEV"
	]
	unity_ver = random.choice(unity_versions)
	webreq_ver = random.choice(unity_webreq_versions)
	curl_ver = random.choice(libcurl_versions)
	
	return unity_ver, f"UnityPlayer/{unity_ver} (UnityWebRequest/{webreq_ver}, libcurl/{curl_ver})"


def random_device_id(k=53):
	return ''.join(random.choices(string.hexdigits, k=k)).lower()


def random_device_model():
	VENDORS = [
		"HUANANZHI",
		"ASUS",
		"GIGABYTE",
		"MSI",
		"ASRock",
		"Lenovo",
		"Dell",
		"HP",
		"HASEE",
	]
	vendor = random.choice(VENDORS)
	return f"Unknown ({vendor})"


def random_device_fp():
	return '38d' + ''.join(random.choices(string.hexdigits, k=10)).lower()


def random_device_name():
	base_str = string.ascii_uppercase + string.digits
	return 'DESKTOP-' + ''.join(random.choices(base_str, k=7))


def random_win10_version():
	WIN10_VERSIONS = [
		"Windows 10 (10.0.18363) 64bit",
		"Windows 10 (10.0.19041) 64bit",
		"Windows 10 (10.0.19042) 64bit",
		"Windows 10 (10.0.19043) 64bit",
		"Windows 10 (10.0.19044) 64bit",
		"Windows 10 (10.0.19045) 64bit",
	]
	return random.choice(WIN10_VERSIONS)


def random_seed_id():
	base_str = string.ascii_lowercase + string.digits
	return ''.join(random.choices(base_str, k=16))


def seed_ts():
	return str(int(time.time() * 1000))


def get_uuid():
	return str(uuid.uuid4())


def get_fixed_ext_fields():
	ext_fields_ = {
		"browserLanguage": "zh-CN",
		"browserPlat": "Win32",
		"browserScreenSize": "1623930",
		"browserTimeZone": "Asia/Shanghai",
		"canvas": "1234a8e9be3b87b0097867706da1f4f9f5750364ef19a438fb02d3530ff34366",
		"colorDepth": "24",
		"cpuClass": "HTC B9",
		"deviceMemory": "8",
		"hardwareConcurrency": "24",
		"hasLiedBrowser": "0",
		"hasLiedLanguage": "0",
		"hasLiedOs": "0",
		"hasLiedResolution": "1",
		"ifAdBlock": "0",
		"ifNotTrack": "HTC B9",
		"isTouchSupported": "0",
		"listOfPlugins": [
			"PDF Viewer",
			"Chrome PDF Viewer",
			"Chromium PDF Viewer",
			"Microsoft Edge PDF Viewer",
			"WebKit built-in PDF"
		],
		"maxTouchPoints": "0",
		"numOfPlugins": "5",
		"packageName": "unknown",
		"packageVersion": "2.43.0",
		"pixelRatio": "1",
		"screenRatio": "1",
		"userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
		"webDriver": "0",
		"webGlRender": "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)",
		"webGlVendor": "Google Inc. (Google)",
		"webgl": "d0f0176272facf04c66de189044c4aa5f1f14eeae7ea5b1b7048b6e66cb7184a"
	}
	return json.dumps(ext_fields_)


def base64_sccode(seccode: dict):
	json_bytes = json.dumps(seccode, separators=(',', ':')).encode('utf-8')
	json_base64 = base64.b64encode(json_bytes).decode('utf-8')
	return json_base64


if __name__ == '__main__':
	print(random_unity_ua())
	print(random_device_id())
	print(random_device_model())
	print(random_device_fp())
	print(random_device_name())
