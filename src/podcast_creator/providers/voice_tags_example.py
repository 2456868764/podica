"""示例：如何使用 Voice Tags (Paralinguistic Controls)"""

from podcast_creator.providers.index_tts import IndexTTSTextToSpeechModel
from podcast_creator.providers.kokoro_tts import KokoroTextToSpeechModel


def example_voice_tags_usage():
    """演示如何使用 voice tags (副语言控制)"""
    
    # 创建 IndexTTS provider
    index_tts = IndexTTSTextToSpeechModel(
        base_url="http://localhost:9000/v1"
    )
    
    # 获取 capability
    cap = index_tts.capability
    
    print("=== IndexTTS Capability ===")
    print(f"支持 voice tags (副语言控制): {cap.supports_voice_tags}")
    print(f"可用的 voice tags: {cap.available_voice_tags}")
    print()
    
    # Voice tags 是副语言控制，用于在文本中嵌入笑声、叹息等
    # 示例：在文本中使用 voice tags
    print("=== 使用 Voice Tags 生成语音 ===")
    
    # 示例文本，包含副语言控制标记
    text_with_tags = """
    今天天气真好！[laughter] 我们去公园散步吧。
    不过有点累[breath]，让我先休息一下[sigh]。
    好了，我们出发吧！[pause]
    """
    
    print(f"包含 voice tags 的文本:\n{text_with_tags}")
    print()
    
    # 检查 provider 是否支持特定的 voice tag
    def check_voice_tag_support(tts_provider, tag: str) -> bool:
        """检查 provider 是否支持特定的 voice tag"""
        cap = tts_provider.capability
        if not cap.supports_voice_tags:
            return False
        return tag.lower() in [t.lower() for t in (cap.available_voice_tags or [])]
    
    # 检查各个 voice tags 的支持情况
    print("=== Voice Tags 支持情况 ===")
    tags_to_check = ["laughter", "sigh", "breath", "pause", "cough", "gasp"]
    for tag in tags_to_check:
        supported = check_voice_tag_support(index_tts, tag)
        print(f"{tag}: {'✅ 支持' if supported else '❌ 不支持'}")
    print()
    
    # Kokoro TTS 示例
    print("=== Kokoro TTS Capability ===")
    kokoro_tts = KokoroTextToSpeechModel(
        base_url="http://localhost:9000/v1"
    )
    kokoro_cap = kokoro_tts.capability
    print(f"支持 voice tags: {kokoro_cap.supports_voice_tags}")
    print(f"可用的 voice tags: {kokoro_cap.available_voice_tags}")
    print()
    
    # 显示所有可用的 voice tags
    print("=== 所有可用的 Voice Tags ===")
    if kokoro_cap.available_voice_tags:
        for tag in kokoro_cap.available_voice_tags:
            print(f"  - {tag}")
    print()
    
    # 使用示例：在文本中嵌入 voice tags
    print("=== Voice Tags 使用示例 ===")
    example_texts = [
        "哈哈[laughter]，这太有趣了！",
        "唉[sigh]，今天真是累啊。",
        "让我深呼吸一下[breath]，然后继续。",
        "等一下[pause]，让我想想。",
    ]
    
    for text in example_texts:
        print(f"  {text}")
    print()
    
    print("注意：Voice tags 的具体格式和用法可能因 Provider 而异，")
    print("请参考各 Provider 的文档了解详细的使用方法。")


if __name__ == "__main__":
    example_voice_tags_usage()

