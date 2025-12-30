# 中文方言支持方案设计文档

## 1. 背景与目标

参考 SoulX-Podcast 的方言实现机制，为当前 podcast 系统添加中文方言支持功能，使播客能够生成具有地方特色的对话内容。

### 1.1 SoulX 方言实现机制分析

SoulX-Podcast 通过以下机制实现方言支持：

1. **方言标记系统**：使用特殊标记 `<|Sichuan|>`, `<|Henan|>`, `<|Yue|>` 来标识方言类型
2. **方言提示文本（dialect_prompt）**：为每个说话人提供方言示例文本，用于激活方言生成能力
3. **文本处理流程**：
   - 在 prompt 阶段，将方言提示文本与普通提示文本结合
   - 在对话文本中，每句话前加上方言标记（如 `<|Sichuan|>`）
4. **模型要求**：需要使用专门的方言模型（如 `SoulX-Podcast-1.7B-dialect`）

### 1.2 当前系统架构

- **语言配置**：使用 `language` 字段（"中文" 或 "English"）控制语言
- **说话人配置**：通过 `SpeakerProfile` 配置说话人信息
- **文本生成**：使用 `transcript.jinja` 模板生成对话文本
- **TTS 支持**：支持多种 TTS 提供商（Kokoro, IndexTTS, SoulX）

## 2. 设计方案

### 2.1 语言与方言的层次结构

```
Language (语言)
├── English (英语)
└── Chinese (中文)
    ├── Mandarin (普通话) - 默认
    ├── Sichuanese (四川话) - <|Sichuan|>
    ├── Henanese (河南话) - <|Henan|>
    ├── Cantonese (粤语) - <|Yue|>
    └── [其他方言...]
```

### 2.2 核心设计原则

1. **向后兼容**：保持现有 "中文"/"English" 的简单配置方式
2. **渐进增强**：支持更细粒度的方言配置
3. **灵活配置**：支持全局方言设置和每个说话人的独立方言设置
4. **TTS 集成**：与 SoulX TTS 的方言功能无缝集成

## 3. 实现方案

### 3.1 数据结构扩展

#### 3.1.1 扩展 `Speaker` 模型

在 `src/podcast_creator/speakers.py` 中为 `Speaker` 添加方言字段：

```python
class Speaker(BaseModel):
    # ... 现有字段 ...
    
    dialect: Optional[str] = Field(
        default=None,
        description="方言类型，如 'sichuan', 'henan', 'yue'。如果为 None，则使用全局方言设置或默认普通话"
    )
    dialect_prompt: Optional[str] = Field(
        default=None,
        description="方言提示文本，用于激活方言生成。如果为 None，将使用默认的方言示例文本"
    )
```

#### 3.1.2 扩展 `PodcastState`

在 `src/podcast_creator/state.py` 中添加方言相关字段：

```python
class PodcastState(TypedDict):
    # ... 现有字段 ...
    
    # 方言配置
    dialect: Optional[str] = None  # 全局方言设置，如 'sichuan', 'henan', 'yue'
    dialect_prompts: Optional[Dict[str, str]] = None  # 每个说话人的方言提示文本
```

#### 3.1.3 扩展 `EpisodeProfile`

在 `src/podcast_creator/episodes.py` 中添加方言字段：

```python
class EpisodeProfile(BaseModel):
    # ... 现有字段 ...
    
    dialect: Optional[str] = Field(
        default=None,
        description="方言类型，如 'sichuan', 'henan', 'yue'。仅当 language='中文' 时有效"
    )
```

### 3.2 方言配置管理

#### 3.2.1 创建方言配置文件

创建 `src/resources/dialects_config.json`：

```json
{
  "dialects": {
    "sichuan": {
      "name": "四川话",
      "tag": "<|Sichuan|>",
      "description": "四川方言，具有独特的语音和词汇特点",
      "default_prompts": [
        "要得要得！前头几个耍洋盘，我后脚就背起铺盖卷去景德镇耍泥巴，巴适得喊老天爷！",
        "哎哟喂，这个搞反了噻！黑神话里头唱曲子的王二浪早八百年就在黄土高坡吼秦腔喽。"
      ],
      "example_texts": [
        "各位《巴适得板》的听众些，大家好噻！",
        "你硬是精灵完了嗦？这点儿小把戏还想麻到我！"
      ]
    },
    "henan": {
      "name": "河南话",
      "tag": "<|Henan|>",
      "description": "河南方言，中原官话的代表",
      "default_prompts": [
        "俺这不是怕恁路上不得劲儿嘛！那景德镇瓷泥可娇贵着哩，得先拿咱河南人这实诚劲儿给它揉透喽。",
        "恁这想法真闹挺！陕北民谣比黑神话早几百年都有了，咱可不兴这弄颠倒啊，中不？"
      ],
      "example_texts": [
        "哎，大家好啊，欢迎收听咱这一期嘞《瞎聊呗，就这么说》，我是恁嘞老朋友，燕子。",
        "恁咋这时候才来咧？俺搁这儿等得前心贴后心，肚里饥得咕咕叫唤！"
      ]
    },
    "yue": {
      "name": "粤语",
      "tag": "<|Yue|>",
      "description": "粤语（广东话），岭南地区的主要方言",
      "default_prompts": [
        "真係冇讲错啊！攀山滑雪嘅语言专家几巴闭，都唔及我听日拖成副身家去景德镇玩泥巴，呢铺真系发哂白日梦咯！",
        "咪搞错啊！陕北民谣响度唱咗几十年，黑神话边有咁大面啊？你估佢哋抄游戏咩！"
      ],
      "example_texts": [
        "各位听众大家好，欢迎收听我哋嘅节目。",
        "你今日食咗饭未啊？"
      ]
    }
  },
  "default_dialect": "mandarin"
}
```

#### 3.2.2 创建方言工具模块

创建 `src/podcast_creator/dialects.py`：

```python
"""
方言配置和工具模块
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field

class DialectConfig(BaseModel):
    """方言配置"""
    name: str = Field(..., description="方言名称")
    tag: str = Field(..., description="方言标记，如 <|Sichuan|>")
    description: str = Field(..., description="方言描述")
    default_prompts: List[str] = Field(default_factory=list, description="默认方言提示文本列表")
    example_texts: List[str] = Field(default_factory=list, description="示例文本列表")

class DialectsConfig(BaseModel):
    """方言配置集合"""
    dialects: Dict[str, DialectConfig] = Field(default_factory=dict)
    default_dialect: str = Field(default="mandarin", description="默认方言")

def load_dialects_config(config_path: Optional[Path] = None) -> DialectsConfig:
    """加载方言配置"""
    if config_path is None:
        # 默认路径
        current_dir = Path(__file__).parent.parent
        config_path = current_dir / "resources" / "dialects_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Dialects config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return DialectsConfig(**data)

def get_dialect_tag(dialect: Optional[str]) -> str:
    """获取方言标记"""
    if not dialect or dialect == "mandarin":
        return ""
    
    config = load_dialects_config()
    if dialect in config.dialects:
        return config.dialects[dialect].tag
    return ""

def get_dialect_prompt(dialect: Optional[str], speaker_index: int = 0) -> str:
    """获取方言提示文本"""
    if not dialect or dialect == "mandarin":
        return ""
    
    config = load_dialects_config()
    if dialect in config.dialects:
        prompts = config.dialects[dialect].default_prompts
        if prompts and speaker_index < len(prompts):
            return prompts[speaker_index]
        elif prompts:
            return prompts[0]
    return ""
```

### 3.3 文本生成模板修改

#### 3.3.1 修改 `transcript.jinja`

在 `src/resources/prompts/podcast/transcript.jinja` 中添加方言相关指令：

```jinja
{% if dialect and dialect != "mandarin" %}
IMPORTANT: This podcast should be generated in {{ dialect_name }} dialect ({{ dialect_tag }}).

DIALECT GENERATION GUIDELINES:
- Each dialogue must be prefixed with the dialect tag: {{ dialect_tag }}
- Use authentic {{ dialect_name }} vocabulary, expressions, and sentence patterns
- Maintain natural conversational flow while incorporating dialectal features
- The dialect should feel authentic and not forced

DIALECT EXAMPLES:
{% for example in dialect_examples %}
- {{ example }}
{% endfor %}

{% if dialect_prompts %}
DIALECT PROMPTS FOR SPEAKERS:
{% for speaker_name, prompt in dialect_prompts.items() %}
- {{ speaker_name }}: {{ prompt }}
{% endfor %}
{% endif %}

{% endif %}
```

### 3.4 TTS 集成

#### 3.4.1 扩展 `SoulXTTS` 类

修改 `src/llm/soulx_tts.py`，添加方言支持：

```python
@dataclass
class SoulXTTSParam:
    # ... 现有字段 ...
    
    dialect: Optional[str] = None  # 方言类型
    dialect_prompt: Optional[str] = None  # 方言提示文本

class SoulXTTS:
    # ... 现有代码 ...
    
    def generate_speech(self, param: SoulXTTSParam) -> np.ndarray:
        # ... 现有代码 ...
        
        # 处理方言
        use_dialect_prompt = False
        dialect_prompt_text_tokens_for_llm = []
        dialect_prefix = []
        
        if param.dialect and param.dialect != "mandarin":
            use_dialect_prompt = True
            dialect_prompt_text = param.dialect_prompt or get_dialect_prompt(param.dialect, 0)
            
            if dialect_prompt_text:
                # 编码方言提示文本
                dialect_prompt_text_with_tag = f"{get_dialect_tag(param.dialect)}{dialect_prompt_text}"
                dialect_prompt_tokens = self.dataset.text_tokenizer.encode(dialect_prompt_text_with_tag)
                dialect_prompt_text_tokens_for_llm = [dialect_prompt_tokens]
                
                # 设置方言前缀
                task_prefix = self.dataset.text_tokenizer.encode("<|podcast|>")
                dialect_prefix = [task_prefix, []]
        
        # ... 在 processed_data 中添加方言相关字段 ...
        processed_data = {
            # ... 现有字段 ...
            "use_dialect_prompt": use_dialect_prompt,
            "dialect_prompt_text_tokens_for_llm": dialect_prompt_text_tokens_for_llm if use_dialect_prompt else None,
            "dialect_prefix": dialect_prefix if use_dialect_prompt else None,
        }
```

#### 3.4.2 修改对话文本处理

在生成对话文本时，为每句话添加方言标记：

```python
def add_dialect_tags_to_transcript(transcript: List[Dialogue], dialect: Optional[str]) -> List[Dialogue]:
    """为对话文本添加方言标记"""
    if not dialect or dialect == "mandarin":
        return transcript
    
    dialect_tag = get_dialect_tag(dialect)
    if not dialect_tag:
        return transcript
    
    result = []
    for dialogue in transcript:
        # 在 dialogue 文本前添加方言标记
        tagged_dialogue = Dialogue(
            speaker=dialogue.speaker,
            dialogue=f"{dialect_tag}{dialogue.dialogue}",
            emotion=dialogue.emotion,
            speed=dialogue.speed
        )
        result.append(tagged_dialogue)
    
    return result
```

### 3.5 API 和配置接口

#### 3.5.1 扩展 `create_podcast` 函数

在 `src/podcast_creator/graph.py` 中添加方言参数：

```python
async def create_podcast(
    # ... 现有参数 ...
    dialect: Optional[str] = None,  # 方言类型
) -> Dict:
    # ... 现有代码 ...
    
    # 处理方言配置
    if language == "中文" or language == "chinese":
        # 从 episode_profile 获取方言，或使用传入的参数
        resolved_dialect = dialect or (episode_profile.dialect if episode_profile else None)
        
        # 如果没有指定方言，默认为普通话
        if not resolved_dialect:
            resolved_dialect = "mandarin"
    else:
        resolved_dialect = None
    
    # 将方言信息添加到 initial_state
    initial_state["dialect"] = resolved_dialect
```

#### 3.5.2 更新 Web UI

在 `src/server/app.py` 中添加方言选择器：

```python
# 在播客生成页面添加方言选择
if language == "中文":
    dialect = st.selectbox(
        "方言:",
        ["普通话", "四川话", "河南话", "粤语"],
        index=0
    )
    # 转换为内部标识
    dialect_map = {
        "普通话": "mandarin",
        "四川话": "sichuan",
        "河南话": "henan",
        "粤语": "yue"
    }
    resolved_dialect = dialect_map.get(dialect, "mandarin")
else:
    resolved_dialect = None
```

## 4. 实施步骤

### 阶段 1：基础架构（优先级：高）

1. ✅ 创建方言配置文件和工具模块
2. ✅ 扩展数据模型（Speaker, PodcastState, EpisodeProfile）
3. ✅ 实现方言标记和提示文本的获取函数

### 阶段 2：文本生成集成（优先级：高）

1. ✅ 修改 `transcript.jinja` 模板，添加方言生成指令
2. ✅ 在 `generate_transcript_node` 中处理方言配置
3. ✅ 实现对话文本的方言标记添加功能

### 阶段 3：TTS 集成（优先级：中）

1. ✅ 扩展 `SoulXTTS` 类支持方言参数
2. ✅ 在 TTS 调用时传递方言信息
3. ✅ 确保与 SoulX 方言模型的兼容性

### 阶段 4：UI 和配置（优先级：中）

1. ✅ 更新 Web UI 添加方言选择器
2. ✅ 更新配置文件格式
3. ✅ 添加方言示例和文档

### 阶段 5：测试和优化（优先级：低）

1. ✅ 测试各种方言的生成效果
2. ✅ 优化方言提示文本
3. ✅ 性能优化和错误处理

## 5. 使用示例

### 5.1 基本使用

```python
# 创建四川话播客
result = await create_podcast(
    content="...",
    briefing="...",
    language="中文",
    dialect="sichuan",
    # ... 其他参数
)
```

### 5.2 配置文件方式

```json
{
  "profiles": {
    "sichuan_podcast": {
      "speaker_config": "ai_researchers",
      "language": "中文",
      "dialect": "sichuan",
      "default_briefing": "..."
    }
  }
}
```

### 5.3 说话人级别方言

```json
{
  "speakers": [
    {
      "name": "主持人",
      "dialect": "mandarin",
      "dialect_prompt": null
    },
    {
      "name": "嘉宾",
      "dialect": "sichuan",
      "dialect_prompt": "<|Sichuan|>要得要得！..."
    }
  ]
}
```

## 6. 注意事项

1. **模型要求**：使用 SoulX 方言功能需要 `SoulX-Podcast-1.7B-dialect` 模型
2. **TTS 提供商**：目前仅 SoulX TTS 支持方言，其他 TTS 提供商将忽略方言设置
3. **文本质量**：方言文本的生成质量依赖于 LLM 对方言的理解能力
4. **向后兼容**：不指定方言时，系统默认使用普通话，保持向后兼容

## 7. 未来扩展

1. **更多方言**：支持更多中文方言（如东北话、上海话等）
2. **方言混合**：支持同一播客中不同说话人使用不同方言
3. **方言强度控制**：支持控制方言的"浓度"（从轻微到完全）
4. **自动方言检测**：根据内容主题自动推荐合适的方言
