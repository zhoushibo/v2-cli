"""Test qwen3-coder-30b after 397B unload"""

import requests
import time

url = 'http://192.168.3.200:1234/v1/chat/completions'
payload = {
    'model': 'qwen3-coder-30b-a3b-instruct',
    'messages': [{'role': 'user', 'content': 'Hello, who are you?'}],
    'max_tokens': 100
}

print('Testing qwen3-coder-30b after 397B unload...')
print('-' * 60)

try:
    print('Sending request...')
    start = time.time()
    r = requests.post(url, json=payload, timeout=60)
    duration = time.time() - start

    print(f'Status: {r.status_code}')
    print(f'Latency: {duration:.2f}s')

    if r.status_code == 200:
        data = r.json()
        content = data['choices'][0]['message']['content']
        usage = data['usage']
        print(f'Response: {content}')
        print(f'Tokens: {usage["prompt_tokens"]} + {usage["completion_tokens"]} = {usage["total_tokens"]}')
        print('SUCCESS!')
    else:
        print(f'Error: {r.text}')
        print('FAILED!')

except Exception as e:
    print(f'Exception: {e}')
    print('FAILED!')

print('-' * 60)
