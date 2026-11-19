import json

path = r'C:\Users\dhars\.gemini\antigravity\brain\abce62e2-969f-4ae8-ab09-628694c519bd\.system_generated\logs\transcript_full.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        if '"step_index":18975' in line:
            obj = json.loads(line)
            with open('scratch/step_18975.txt', 'w', encoding='utf-8') as out:
                out.write(obj.get('content', ''))
            print("Extracted step 18975")
            break
