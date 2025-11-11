import json

with open("result.json") as f:
    data = json.load(f)
    messages = data["messages"]
    filtered = []
    for msg in messages:
        if "width" not in msg and "height" not in msg:
            continue
        if msg["width"] != 1280 or msg["height"] != 1280:
            continue
        text_entities = msg["text_entities"]
        plain_text = [s['text']
                      for s in text_entities if s['type'] == 'plain'][0]
        text = msg["text"] if isinstance(msg["text"], str) else plain_text
        coin = plain_text.split('\n')
        coin_name, coin_symb = coin[0], coin[1]
        filtered_msg = {
            "photo": msg["photo"],
            "coin": coin_name,
            "coin_sym": coin_symb,
            "source": f"https://t.me/CrypoIslam/{msg['id']}"
        }
        if "judgement" in text.lower():
            filtered_msg["judgement"] = "not permitted" if "not permitted" \
                    in text.lower() else "permitted"
        filtered.append(filtered_msg)
        # print(msg["text"])

with open("filtered_results.json", "w") as f:
    json.dump(filtered, f, indent=4)
