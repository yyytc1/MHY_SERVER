# diagnose_mem.py
# 运行前请确保本服务在本机运行 (默认 http://127.0.0.1:8080)
# 作用：循环调用登录接口，周期性打印进程 RSS、GC 对象计数、tracemalloc 热点，帮助定位内存增长来源

import requests
import time
import gc
import tracemalloc
import os
from collections import Counter

# 可选依赖 psutil（更精确的 RSS），如果没有会退回到 tracemalloc
try:
    import psutil
    _psutil = True
except Exception:
    _psutil = False

# 配置
URL = "http://127.0.0.1:8080/api/login"  # 根据你的服务修改
PAYLOAD = {"user": "test_user", "pass": "test_pass", "city": "6"}
ITER = 200
DELAY = 0.05
REPORT_EVERY = 10

tracemalloc.start()
proc = psutil.Process(os.getpid()) if _psutil else None


def object_counts():
    objs = gc.get_objects()
    c = Counter(type(o).__name__ for o in objs)
    interesting = {k: c[k] for k in c if k in ('dict', 'list', 'tuple', 'str', 'bytes')}
    # Response/Session 等类型 名称取决于库实现，列出 top 10
    top = c.most_common(10)
    return interesting, top


def rss_mb():
    if _psutil:
        return proc.memory_info().rss / 1024 / 1024
    else:
        # 退回到 tracemalloc（仅表示 Python 分配，不等同 RSS）
        current, peak = tracemalloc.get_traced_memory()
        return current / 1024 / 1024


if __name__ == '__main__':
    print('Start memory diagnosis')
    gc.collect()
    for i in range(ITER):
        try:
            r = requests.post(URL, json=PAYLOAD, timeout=10)
            # 尽量不读取大量内容
            _ = r.status_code
        except Exception as e:
            print(f'iter {i} request error: {e}')
        finally:
            try:
                r.close()
            except Exception:
                pass

        if i % REPORT_EVERY == 0:
            gc.collect()
            mem = rss_mb()
            interesting, top = object_counts()
            print(f'iter={i} rss={mem:.1f}MB interesting={interesting}')
            print('Top object types:', top)
            snap = tracemalloc.take_snapshot()
            stats = snap.statistics('lineno')[:5]
            print('Top tracemalloc allocations:')
            for st in stats:
                print(st)
            print('-' * 60)

        time.sleep(DELAY)

    print('Done')
