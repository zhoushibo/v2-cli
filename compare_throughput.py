"""Compare LM Studio vs Ollama - Tokens/s throughput"""

import requests
import time
import json

# Test function
def test_model(provider, model_id, url, prompt, max_tokens=100):
    print(f'\nTesting {provider}: {model_id}')
    print('-' * 60)

    payload = {
        'model': model_id,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
        'stream': False,
    }

    try:
        # Warm-up
        print('Warm-up request...')
        requests.post(url, json=payload, timeout=60)
        time.sleep(1)

        # Actual test
        print('Actual test...')
        start = time.time()
        r = requests.post(url, json=payload, timeout=120)
        duration = time.time() - start

        if r.status_code == 200:
            data = r.json()
            usage = data.get('usage', {})
            completion_tokens = usage.get('completion_tokens', 0)
            prompt_tokens = usage.get('prompt_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)

            # Calculate throughput
            tokens_per_second = completion_tokens / duration if duration > 0 else 0
            tokens_per_total = total_tokens / duration if duration > 0 else 0

            print(f'status_code: {r.status_code}')
            print(f'duration: {duration:.2f}s')
            print(f'prompt_tokens: {prompt_tokens}')
            print(f'completion_tokens: {completion_tokens}')
            print(f'total_tokens: {total_tokens}')
            print(f'tokens/s (completion only): {tokens_per_second:.1f}')
            print(f'tokens/s (total): {tokens_per_total:.1f}')

            return {
                'provider': provider,
                'model': model_id,
                'status': 'success',
                'duration': duration,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'tokens_per_second_completion': tokens_per_second,
                'tokens_per_second_total': tokens_per_total,
            }
        else:
            print(f'Error: {r.status_code}')

    except Exception as e:
        print(f'Exception: {e}')
        return None

# Test configurations
test_cases = [
    {
        'name': 'LM Studio - qwen2-7b',
        'provider': 'lm_studio',
        'model': 'qwen2-7b-instruct',
        'url': 'http://192.168.3.200:1234/v1/chat/completions',
        'prompt': 'Write a short paragraph about AI.',
        'max_tokens': 200,
    },
    {
        'name': 'Ollama - qwen2.5-coder:32b',
        'provider': 'ollama',
        'model': 'qwen2.5-coder:32b',
        'url': 'http://192.168.3.200:11434/v1/chat/completions',
        'prompt': 'Write a short paragraph about AI.',
        'max_tokens': 200,
    },
    {
        'name': 'LM Studio - qwen3-coder-30b',
        'provider': 'lm_studio',
        'model': 'qwen3-coder-30b-a3b-instruct',
        'url': 'http://192.168.3.200:1234/v1/chat/completions',
        'prompt': 'Write a short paragraph about AI.',
        'max_tokens': 200,
    },
]

# Run tests
print('=' * 70)
print('Throughput Comparison: LM Studio vs Ollama')
print('=' * 70)

results = []
for test_case in test_cases:
    result = test_model(
        test_case['provider'],
        test_case['model'],
        test_case['url'],
        test_case['prompt'],
        test_case['max_tokens'],
    )
    if result:
        results.append(result)

# Summary
print('\n' + '=' * 70)
print('SUMMARY')
print('=' * 70)

if results:
    print(f'\n{"Model":<40} {"Tokens/s (total)":<20} {"Duration (s)":<15}')
    print('-' * 75)

    for result in results:
        name = f"{result['provider']} - {result['model'][:30]}"
        print(f"{name:<40} {result['tokens_per_second_total']:<20.1f} {result['duration']:<15.2f}")

    # Find fastest
    fastest = max(results, key=lambda x: x['tokens_per_second_total'])
    print(f'\nFastest: {fastest["provider"]} - {fastest["model"]}')
    print(f'Tokens/s: {fastest["tokens_per_second_total"]:.1f}')
else:
    print('No successful tests!')
