def expand_query(query):
    synonyms = {
        "切割機": ["切割", "裁切", "切割設備"],
        "量測機": ["量測", "測試機"],
        "檢驗": ["檢查", "檢測"],
        "銲線": ["wire bonding", "bonding","銲線製程"],
        "檢查": [ "檢驗",
            "測試",
            "檢驗項目",
            "測試項目",
            "檢查項目",
            "品質檢驗"],
         "檢查什麼": ["檢驗項目", "測試項目", "檢查項目","品質項目"],  # 🔥 加這個
}


    expanded = [query]

    for k, v in synonyms.items():
        if k in query:
            expanded.extend(v)

    return list(set(expanded))