"""Generate unit test using abee qwen3-coder-30b"""

import requests
import time

# Read context
context_file = "C:\\Users\\10952\\.openclaw\\workspace\\ares_core\\abeegateway\\test_context_abeeclient.ts"
with open(context_file, 'r', encoding='utf-8') as f:
    context = f.read()

# Prompt for abee
prompt = f"""
你是专业的测试工程师。请为以下代码生成完整的 Vitest 单元测试：

{context}

要求：
1. 使用 vi.mock('axios') 模拟 HTTP 调用
2. 包含 4 个测试用例（成功、超时、5xx 错误、404 错误）
3. 使用 describe + it 结构
4. 每个测试用例有清晰的描述
5. 输出完整的 TypeScript 代码
"""

# Call abee API
url = "http://192.168.3.200:1234/v1/chat/completions"
payload = {
    "model": "qwen3-coder-30b-a3b-instruct",
    "messages": [
        {"role": "system", "content": "你是专业的测试工程师，擅长编写 Vitest 单元测试。"},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 2048,
    "temperature": 0.3,  # 低温，确保代码稳定
}

print("Requesting abee 30B to generate test code...")
print("-" * 60)

try:
    start = time.time()
    r = requests.post(url, json=payload, timeout=60)
    duration = time.time() - start

    if r.status_code == 200:
        response_data = r.json()
        content = response_data['choices'][0]['message']['content']
        usage = response_data['usage']

        print(f"Status: {r.status_code}")
        print(f"Latency: {duration:.2f}s")
        print(f"Tokens: {usage['prompt_tokens']} + {usage['completion_tokens']} = {usage['total_tokens']}")
        print("-" * 60)
        print("Generated Test Code:")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # Save to file
        output_file = "C:\\Users\\10952\\.openclaw\\workspace\\ares_core\\tests\\unit\\abee_client.test.ts"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\nSaved to: {output_file}")
        print("SUCCESS!")

    else:
        print(f"Error: {r.status_code}")
        print(f"Response: {r.text}")

except Exception as e:
    print(f"Exception: {e}")
    print("FAILED!")
