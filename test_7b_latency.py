"""Test qwen2-7b (realtime model) latency"""

import requests
import time

url = 'http://192.168.3.200:1234/v1/chat/completions'
payload = {
    'model': 'qwen2-7b-instruct',
    'messages': [{'role': 'user', 'content': 'Hi'}],
    'max_tokens': 50
}

print('Testing qwen2-7b (realtime model)...')
print('-' * 60)

# 测试 3 次求平均
latencies = []
for i in range(3):
    try:
        print(f'Test {i+1}/3...')
        start = time.time()
        r = requests.post(url, json=payload, timeout=30)
        duration = time.time() - start

        if r.status_code == 200:
            latencies.append(duration)
            print(f'  Status: {r.status_code}')
            print(f'  Latency: {duration:.2f}s')
        else:
            print(f'  Error: {r.text}')

        time.sleep(1)  # 避免过快请求

    except Exception as e:
        print(f'  Exception: {e}')

print('-' * 60)
if latencies:
    avg = sum(latencies) / len(latencies)
    avg_ms = avg * 1000
    print(f'Average latency: {avg:.2f}s ({avg_ms:.0f}ms)')
    print(f'Min: {min(latencies):.2f}s')
    print(f'Max: {max(latencies):.2f}s')
else:
    print('No successful tests!')
