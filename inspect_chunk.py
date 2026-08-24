import json

def main():
    path = "/Users/jincaistudy201236/.gemini/antigravity/brain/de1cd367-8176-4573-b273-e5dff52a050d/.system_generated/logs/transcript.jsonl"
    
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if "foundSelectableBuffs.forEach" in line:
                try:
                    data = json.loads(line)
                    text_sources = []
                    if data.get("content"):
                        text_sources.append(data["content"])
                    if data.get("tool_calls"):
                        for tc in data["tool_calls"]:
                            args = tc.get("args", {})
                            for k, v in args.items():
                                if isinstance(v, str):
                                    text_sources.append(v)
                    
                    for text in text_sources:
                        if "foundSelectableBuffs.forEach" in text:
                            idx_func = text.find("foundSelectableBuffs.forEach")
                            print(f"--- MATCH {idx+1} ---")
                            print(text[idx_func:idx_func+1500])
                            print("="*80)
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()

