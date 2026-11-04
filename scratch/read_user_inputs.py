import json, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\Friends\.gemini\antigravity-ide\brain\c7d999c2-8c48-41b0-8815-18b04c13d5ff\.system_generated\logs\transcript_full.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        idx = data.get('step_index', 0)
        if 2230 <= idx <= 2246:
            print(f"=== STEP {idx} [{data.get('type')}] ===")
            content = data.get('content') or ''
            if content:
                print("Content:\n", content[:2000])
