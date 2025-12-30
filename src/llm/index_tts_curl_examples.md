# IndexTTS API curl 请求示例

## 基本请求

### 1. 最简单的请求（使用默认声音）

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "你好，这是一个测试文本。",
    "voice": "男声1",
    "response_format": "wav"
  }' \
  --output output.wav
```

### 2. 带情感指令的请求

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "soulx",
    "input": "价格大跳水[laughter] 1克拉大钻石只要3500元[sigh],近年来[breathing]，培育钻石价格持续走低，[throat_clearing]如今1克拉培育钻价格已从8000元跌至3500元，[coughing]不及同等品质天然钻石价格十分之一",
    "voice": "女生_新闻联播",
    "instructions": "Voice Affect: 低沉、安静、悬疑；传达紧张和阴谋。Tone: 严肃而神秘，始终保持不安的暗流。Pacing: 缓慢、慎重，在悬疑时刻后稍作停顿以增强戏剧性。Emotion: 克制但强烈——声音应该在关键的悬疑点微妙地颤抖或收紧。",
    "response_format": "wav"
  }' \
  --output output_with_instructions.wav
```

<|laughter|>, <|sigh|>, <|breathing|>, <|coughing|>, <|throat_clearing|>

### 3. 使用自定义参考音频（Base64 编码）

```bash
# 首先将音频文件编码为 base64
REFERENCE_AUDIO_B64=$(base64 -i example/男声1.wav | tr -d '\n')

curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"index-tts\",
    \"input\": \"这是使用自定义参考音频生成的语音。\",
    \"voice\": \"男声1\",
    \"reference_audio\": \"${REFERENCE_AUDIO_B64}\",
    \"response_format\": \"wav\"
  }" \
  --output output_custom_voice.wav
```

### 4. 完整参数请求

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "这是一个完整的测试请求，包含所有参数。",
    "voice": "女生_新闻联播",
    "instructions": "Tone: 声音应该专业、正式，像新闻播报员一样。Pacing: 语速稍慢，清晰有力。Emotion: 保持中性、客观的情绪。Pronunciation: 字正腔圆，发音清晰。",
    "response_format": "wav",
    "speed": 1.0
  }' \
  --output output_full.wav
```

## 可用的声音选项

根据配置，IndexTTS 支持以下声音：

- `default` - 默认声音（对应 example/男声1.wav）
- `郭德纲` - 对应 example/郭德纲.wav
- `蜡笔小新` - 对应 example/蜡笔小新.wav
- `男声1` - 对应 example/男声1.wav
- `男声2` - 对应 example/男声2.wav
- `女生_安陵容` - 对应 example/女生_安陵容.wav
- `女生_明兰` - 对应 example/女生_明兰.wav
- `女生_新闻联播` - 对应 example/女生_新闻联播.wav
- `女生_甄嬛` - 对应 example/女生_甄嬛.wav
- `佩奇` - 对应 example/佩奇.wav
- `童声_男` - 对应 example/童声_男.wav
- `童声_女` - 对应 example/童声_女.wav
- `星爷` - 对应 example/星爷.wav

## 支持的音频格式

- `mp3` - MP3 格式（默认）
- `wav` - WAV 格式（推荐用于 IndexTTS）
- `opus` - Opus 格式
- `aac` - AAC 格式
- `flac` - FLAC 格式
- `pcm16` - PCM 16-bit 格式

## 情感指令（instructions）格式示例

### 示例 1：轻松愉快的语调
```json
{
  "instructions": "Tone: 声音应该轻松愉快，充满活力。Pacing: 语速适中，不要过快。Emotion: 表达出开心和兴奋的情绪。"
}
```

### 示例 2：专业正式的语调
```json
{
  "instructions": "Tone: 声音应该专业、正式，像新闻播报员一样。Pacing: 语速稍慢，清晰有力。Emotion: 保持中性、客观的情绪。Pronunciation: 字正腔圆，发音清晰。"
}
```

### 示例 3：戏剧化的语调
```json
{
  "instructions": "Tone: 声音应该精致、正式，充满戏剧性，让人想起20世纪初迷人的电台播音员。Pacing: 语速流畅，节奏稳定，既不过快也不拖沓，保持清晰和庄重。Emotion: 表达应该温暖、热情、欢迎，就像以最大的礼貌向尊贵的观众致辞。Inflection: 使用音调的轻柔起伏来保持参与度，为每个句子添加有趣而优雅的风格。"
}
```

### 示例 4：紧张悬疑的语调
```json
{
  "instructions": "Voice Affect: 低沉、安静、悬疑；传达紧张和阴谋。Tone: 严肃而神秘，始终保持不安的暗流。Pacing: 缓慢、慎重，在悬疑时刻后稍作停顿以增强戏剧性。Emotion: 克制但强烈——声音应该在关键的悬疑点微妙地颤抖或收紧。"
}
```

## 使用不同端口的请求

如果服务运行在不同的端口，修改 URL：

```bash
curl -X POST http://localhost:8080/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "测试文本",
    "voice": "男声1",
    "response_format": "wav"
  }' \
  --output output.wav
```

## 使用不同主机的请求

```bash
curl -X POST http://your-server-ip:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "测试文本",
    "voice": "男声1",
    "response_format": "wav"
  }' \
  --output output.wav
```

## 查看响应信息

添加 `-v` 参数查看详细信息：

```bash
curl -v -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "测试文本",
    "voice": "男声1",
    "response_format": "wav"
  }' \
  --output output.wav
```

## 错误处理示例

如果请求失败，检查错误信息：

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "index-tts",
    "input": "测试文本",
    "voice": "不存在的声音",
    "response_format": "wav"
  }' \
  -w "\nHTTP Status: %{http_code}\n" \
  --output output.wav
```

## SoulX 方言请求示例

> 说明：SoulX 方言需要 `model` 设置为 `"soulx"`，并在文本前添加方言标记。常用标记：
> - `<|Sichuan|>` 四川话
> - `<|Henan|>` 河南话
> - `<|Yue|>` 粤语  
> 参考音频可用 `voice` 提供路径或使用 `reference_audio`（base64）。`reference_text` 可提供方言提示文本。

### 1. 四川话基础请求

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "soulx",
    "input": "<|Sichuan|>各位《巴适得板》的听众些，大家好噻！我是你们主持人晶晶。",
    "voice": "女生_新闻联播",
    "dialect": "sichuan",
    "dialect_prompt": "<|Sichuan|>要得要得！前头几个耍洋盘，我后脚就背起铺盖卷去景德镇耍泥巴，巴适得喊老天爷！",
    "response_format": "wav"
  }' \
  --output output_sichuan.wav
```

### 2. 河南话基础请求

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "soulx",
    "input": "<|Henan|>哎，大家好啊，[laughter],欢迎收听咱这一期嘞《瞎聊呗，就这么说》[breathing]，我是恁嘞老朋友，燕子。",
    "voice": "男声1",
    "dialect": "henan",
    "response_format": "wav"
  }' \
  --output output_henan.wav
```

<|laughter|>, <|sigh|>, <|breathing|>, <|coughing|>, <|throat_clearing|>

### 3. 粤语基础请求

```bash
curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "soulx",
    "input": "<|Yue|>你今日係咪去咗街市買餸啊？我見到個魚檔啲海魚幾新鮮，不如聽日一齊去睇下？",
    "voice": "example/audios/female_mandarin.wav",
    "dialect": "yue",
    "dialect_prompt": "<|Yue|>真係冇讲错啊！攀山滑雪嘅语言专家几巴闭，都唔及我听日拖成副身家去景德镇玩泥巴，呢铺真系发哂白日梦咯！",
    "response_format": "wav"
  }' \
  --output output_yue.wav
```

### 4. 使用自定义参考音频（四川话）

```bash
# 将参考音频编码为 base64
REFERENCE_AUDIO_B64=$(base64 -i example/audios/female_mandarin.wav | tr -d '\n')

curl -X POST http://localhost:9000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"soulx\",
    \"input\": \"<|Sichuan|>就是得嘛！李老倌，我前些天带个外地朋友切人民公园鹤鸣茶社坐了一哈。\",
    \"voice\": \"default\",
    \"reference_audio\": \"${REFERENCE_AUDIO_B64}\",
    \"dialect\": \"sichuan\",
    \"dialect_prompt\": \"<|Sichuan|>要得要得！前头几个耍洋盘，我后脚就背起铺盖卷去景德镇耍泥巴，巴适得喊老天爷！\",
    \"response_format\": \"wav\"
  }" \
  --output output_sichuan_custom.wav
```

### 5. 注意事项（SoulX 方言）
- `model` 必须为 `"soulx"`
- 文本前必须添加正确的方言标记（如 `<|Sichuan|>`），标记与文本之间不留空格
- 建议提供 `dialect_prompt`，包含方言标记和示例文本，能提升方言效果
- 参考音频可通过 `voice` 指定文件路径，或用 `reference_audio`（base64）

## Python 脚本示例

如果需要使用 Python 发送请求：

```python
import requests
import base64

# 基本请求
response = requests.post(
    "http://localhost:9000/v1/audio/speech",
    json={
        "model": "index-tts",
        "input": "你好，这是一个测试文本。",
        "voice": "男声1",
        "response_format": "wav"
    }
)

if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("音频已保存到 output.wav")
else:
    print(f"错误: {response.status_code}")
    print(response.text)

# 带参考音频的请求
with open("example/男声1.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    "http://localhost:9000/v1/audio/speech",
    json={
        "model": "index-tts",
        "input": "这是使用自定义参考音频生成的语音。",
        "voice": "男声1",
        "reference_audio": audio_data,
        "response_format": "wav"
    }
)

if response.status_code == 200:
    with open("output_custom.wav", "wb") as f:
        f.write(response.content)
    print("音频已保存到 output_custom.wav")
```

## 注意事项

1. **模型名称**：必须使用 `"index-tts"` 作为 model 参数
2. **音频格式**：推荐使用 `"wav"` 格式，因为 IndexTTS 原生输出 WAV
3. **参考音频**：如果提供 `reference_audio`，必须是 base64 编码的音频文件
4. **声音文件**：确保对应的声音文件存在于 `src/llm/example/` 目录下
5. **服务状态**：确保服务已启动并运行在指定端口

