# coding : utf-8
# @Time : 2025/11/17 15:44 
# @Author : Adolph
# @File : device.py 
# @Software : PyCharm
import uuid
from dataclasses import dataclass, asdict
import random
import time
from typing import Optional

import faker

DEFAULT_IOS_VERSION = "2.18.0"
NET_TYPES = ["WIFI", "5G"]
OS_VERSIONS = ["17.1.2", "17.1.1"]
VENDORS = ["中国移动", "中国联通", "中国电信"]
faker_ = faker.Faker()

@dataclass
class ExtFields:
	packageVersion: str
	osVersion: str
	proxyStatus: str
	isSimInserted: str
	packageName: str
	deviceName: str
	romRemain: str
	chargeStatus: str
	ramRemain: str
	networkType: str
	cpuType: str
	screenBrightness: str
	batteryStatus: str
	isJailBreak: str
	magnetometer: str
	cpuCores: str
	screenSize: str
	appInstallTimeDiff: str
	isPushEnabled: str
	model: str
	vendor: str
	appMemory: str
	accelerometer: str
	ramCapacity: str
	buildTime: str
	gyroscope: str
	appUpdateTimeDiff: str
	romCapacity: str
	hasVpn: str
	IDFV: str


@dataclass
class ExtFieldsJson:
	ext: ExtFields


def get_utc_time_ms() -> str:
	# 返回毫秒级时间戳（与 Go 的 GetUtcTime 接近）
	return str(int((time.time() - 8 * 3600) * 1000))


def make_model() -> str:
	return "ipad14.4"


def make_device_name() -> str:
	
	return random.choice(faker_.name()) + "'s iPad"


def make_app_memory() -> str:
	# 类似 Go 实现：在 670..690 范围内
	return str(random.randint(670, 690))


def make_vendor() -> str:
	return random.choice(VENDORS)


def make_net_type() -> str:
	return random.choice(NET_TYPES)


def make_rom_or_ram(capacity_str: str) -> str:
	try:
		cap = int(capacity_str)
	except Exception:
		return capacity_str
	# 产生一个在 cap/2 .. cap 的值（近似 Go 的实现）
	low = max(1, cap // 2)
	return str(random.randint(low, cap))


def make_screen() -> str:
	# 生成类似 0.XXX 的字符串，保留三位小数
	val = random.random() * 0.8 + 0.2  # in [0.2,1.0)
	# 四舍五入到 0.05 的倍数，然后格式化为 3 位小数
	step = 0.05
	val = round(val / step) * step
	return f"{val:.3f}"


def make_gyro() -> str:
	gyro_x = random.random() * 0.002 + 0.001
	gyro_z = random.random() * 0.002 - 0.002
	gyro_y = random.random() * 0.002 - 0.003
	return f"{gyro_x:.6f}x{gyro_y:.6f}x{gyro_z:.6f}"


def make_acc() -> str:
	acc_x = random.random() * 1.5 - 0.75
	acc_y = random.random() * 0.0015 + 0.000854
	acc_z = random.random() * 1.5 - 0.668854
	return f"{acc_x:.6f}x{acc_y:.6f}x{acc_z:.6f}"


def make_mag() -> str:
	mag_x = random.random() * 65 + 32.805115
	mag_y = random.random() * 30 - 11.795166
	mag_z = random.random() * 50 - 22.653793
	return f"{mag_x:.6f}x{mag_y:.6f}x{mag_z:.6f}"


def make_battery_status() -> str:
	# Go: random 0..70 + 10 -> 10..80
	return str(random.randint(10, 80))


def new_ext_fields(uid: str, ios_version: Optional[str] = None) -> ExtFieldsJson:
	ios_ver = ios_version or DEFAULT_IOS_VERSION
	ext = ExtFields(
		packageVersion=ios_ver,
		osVersion=OS_VERSIONS[0],
		proxyStatus="0",
		isSimInserted="1",
		packageName="com.miHoYo.HSoDv2CN",
		deviceName=make_device_name(),
		romRemain=make_rom_or_ram("954125"),
		chargeStatus="1",
		ramRemain=make_rom_or_ram("7519"),
		networkType=make_net_type(),
		cpuType="CPU_TYPE_ARM64",
		screenBrightness=make_screen(),
		batteryStatus=make_battery_status(),
		isJailBreak="0",
		magnetometer=make_mag(),
		cpuCores="8",
		screenSize="1194×834",
		appInstallTimeDiff=get_utc_time_ms(),
		isPushEnabled="1",
		model=make_model(),
		vendor=make_vendor(),
		appMemory=make_app_memory(),
		accelerometer=make_acc(),
		ramCapacity="7519",
		buildTime=get_utc_time_ms(),
		gyroscope=make_gyro(),
		appUpdateTimeDiff=str(int(time.time() * 1000)),  # common.GetTime(false) 替代
		romCapacity="954125",
		hasVpn="0",
		IDFV=uid,
	)
	return ExtFieldsJson(ext=ext)


# 可选：将 dataclass 转为 dict（方便序列化）
def ext_to_dict(extjson: ExtFieldsJson) -> dict:
	return asdict(extjson)


if __name__ == '__main__':
	uid = str(uuid.uuid4()).upper()
	ef = new_ext_fields(uid)
	print(ext_to_dict(ef))
