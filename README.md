# AI Podcast - Podica Studio

## Project Overview

Podica Studio is an AI-driven all-in-one podcast creation solution that converts various text content into multi-character conversational podcast audio. The system utilizes Large Language Models (LLM) for content analysis, structuring, and dialogue generation, and converts text into natural and fluent speech dialogues through Text-to-Speech (TTS) technology.

## Key Features

- **Multi-source Content Input**: Supports multiple content sources to flexibly adapt to different content requirements.
  - **Direct Text Input**
  - **File Upload** Supports PDF, DOCX, TXT, etc.
  - **Website URL** Automatically extracts URL content

- **Automated Workflow**: Based on the LangGraph workflow engine, implements a fully automated process from content input to audio output, including content conversion, outline generation, transcript generation, audio generation, and audio synthesis.
  - **Complete Podcast Structure**: Generated audio meets the basic requirements of podcasts, including opening, topics, and conclusion.
  - **Intelligent Content Processing**: Automatically performs content Q&A completion and summarization to ensure the quality and completeness of input content, providing high-quality materials for podcast generation.
  - **Intelligent Outline Generation**: Based on input content and user instructions, automatically generates structured podcast outlines containing multiple segments, each with clear themes and descriptions.
  - **Multi-character Dialogue Generation**: Supports 1-4 speakers participating in conversations simultaneously, each with unique background stories, personality traits, and speaking styles, creating an authentic multi-person conversation atmosphere.


- **Highly Humanized Speech Synthesis**: Voice timbre and intonation are highly humanized, avoiding mechanical, rigid, or flat expressionless delivery.
  - **Voice Cloning** 
  - **Chinese Dialect Support**: Supports multiple Chinese dialect generation, including Cantonese, Sichuanese, Henanese, Shanghainese, etc.
  - **Emotion Control** Supports dialogue emotion control instructions
  - **Voice Tags Support**: Supports embedding voice tags (such as [laughter], [sigh], [breathing], etc.) in dialogues to enhance the naturalness and authenticity of conversations, making generated podcasts more vivid.


- **Flexible Configuration System**:
  - **Speakers Profile**: Configurable speaker voice characteristics, including TTS service provider, voice ID, background story, personality traits, etc.
  - **Episode Profile**: Configurable podcast generation parameters, including Speakers Profile used, LLM model, number of segments, language, dialect, custom instructions, etc.

- **Multi-model Support**: Users can flexibly choose according to their needs.
  - **Integrated Multiple LLM Models** Tencent Hunyuan, OpenAI, Qwen, DeepSeek, etc.
  - **Integrated Multiple TTS Services** Eleven Labs, OpenAI TTS, Qwen TTS, Kokoro TTS, IndexTTS2, SoulX TTS, V3API, LaoZhang),
  - **TTS Capability**: Intelligently detects TTS provider capabilities, including supported languages, dialects, voice tags, voice cloning, etc., automatically adapting to available features.

## Expected Project Impact

**Economic Benefits:**
1. **Cost Reduction**: Traditional podcast production requires professional teams (hosts, editors, post-production), which is costly. This system can reduce production costs by more than 80%, shortening single-episode production time from days to minutes.
2. **Efficiency Improvement**: Automated workflows significantly improve content production efficiency, supporting batch generation to meet large-scale content needs.
3. **Business Model Innovation**: Provides new content monetization channels for content platforms, educational institutions, and enterprises, creating new business value.

**Social Benefits:**
1. **Content Democratization**: Lowers the barrier to podcast creation, enabling more creators to participate in audio content creation and enriching the content ecosystem.
2. **Cultural Heritage**: Supports multi-language and multi-character dialogues, contributing to diverse expression and dissemination of cultural content.

![](./docs/images/feature.png)



## Overall Architecture

The system consists of the following main components:

1. **Multi-source Content Upload**: Supports content acquisition from files, websites, and direct text input.

2. **Intelligent Podcast Generator**: Core component responsible for content analysis, structuring, script generation, and multi-character voice synthesis.

3. **Podcast Template System**: Provides customizable templates, including podcast name, content instructions, character settings, voice styles, etc.

4. **Model Management System**: Integrates multiple LLM and TTS providers, including Tencent Hunyuan, Qwen, DeepSeek, and other LLMs, as well as OpenAI TTS, Eleven Labs, Kokoro TTS, IndexTTS2, Soulx TTS, and other models.

Technology Stack

- **Backend Framework**: Python base libraries + streamlit
- **LLM Integration**: Tencent Hunyuan, Qwen, DeepSeek, Ernie, OpenAI, etc.
- **TTS Services**: ElevenLabs, OpenAI TTS, Kokoro TTS, Qwen TTS, IndexTTS2, SoulX TTS, etc.
- **Workflow Engine**: LangGraph
- **Template System**: Jinja2

## Deployment Instructions

### Manual Installation and Startup of Podica Studio 

*** conda Environment Setup ***

```
conda create --name=podcast python=3.12
conda activate podcast
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r src/requirements.txt
```
*** Configure .env ***

```
cp src/server/.env.exmaple src/server/.env
Modify and configure .env environment variables
```

*** Start Podica Studio with streamlit ***

```
streamlit run src/server/app.py
```



### Docker Deployment

Build Configuration:
Alibaba Cloud: ecs.c9i.2xlarge 
CPU: 8 vCPU  Intel(R) Xeon(R) 6982P-C 
Memory: 16 GiB 


***docker-compose.yaml***, located in docs/docker directory 
```
services:
  kokoro:
    image: registry.cn-hangzhou.aliyuncs.com/2456868764/kokoro-tts:1.0.1
    ports:
      - "9000:9000"
    pull_policy: always
  podcast-studio:
    image: registry.cn-hangzhou.aliyuncs.com/2456868764/podcast-studio:1.0.2
    ports:
      - "8501:8501"
    environment:
        - ERNIE_API_KEY=bce-XXX
        - KOKORO_BASE_URL=http://kokoro:9000/v1
        - V3API_BASE_URL=https://api.gpt.ge/v1/
        - V3API_API_KEY=sk-xxx
    depends_on:
      - kokoro
    pull_policy: always
networks:
  default:
    driver: bridge
```

***Configuration***

Configure environment variables in docker-compose.yaml, including:

- KOKORO_BASE_URL: Kokoro TTS service URL, default value is http://kokoro:9000/v1, using the `hexgrad/Kokoro-82M-v1.1-zh` model to provide TTS service for testing.
- ERNIE_API_KEY: ERNIE API key
- V3API_API_KEY: v3api API key (for OpenAI TTS service), visit `https://api.v3.cm/` to register and obtain API key.

***Startup***

```bash
docker compose up -d
```

**Access**

- Podica Studio Management Portal: http://localhost:8501 to enter the Podica Studio management interface for configuring podcast templates, uploading content, and generating podcasts.

- Podica Studio Introduction and Usage Video
  [Podica Studio Introduction and Usage Video](./docs/voices/podica.mp4)


### Open Source TTS Model Deployment

** TTS Model Build GPU Configuration**:
- Image PyTorch  2.8.0
- Python  3.12(ubuntu22.04)
- CUDA  12.8
- GPU: RTX 4090(24GB) * 1
- CPU: 16 vCPU Intel(R) Xeon(R) Gold 6430
- Memory: 120GB
- Disk: System Disk: 30 GB
- Data Disk: 100GB SSD


In the src/llm directory:

** Kokoro TTS **
```
# download model
huggingface-cli download --resume-download hexgrad/Kokoro-82M-v1.1-zh  --local-dir ./models/hexgrad/Kokoro-82M-v1.1-zh
# install python 
conda create --name=kokoro python=3.12
conda activate kokoro
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements_kokoro.txt
# startup
TTS_PROVIDER=kokoro python service.py
```

** Index TTS Model**
```
# download model
huggingface-cli download --resume-download IndexTeam/IndexTTS-2  --local-dir ./checkpoints/IndexTeam/IndexTTS-2
# install python 
conda create --name=indextts python=3.12
conda activate indextts
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements_indextts.txt
# startup
TTS_PROVIDER=index-tts python service.py
```

** Soulx TTS Model**
```
# download model
huggingface-cli download --resume-download Soul-AILab/SoulX-Podcast-1.7B-dialect --local-dir ./pretrained_models/SoulX-Podcast-1.7B-dialect
# install python 
conda create --name=soulx python=3.12
conda activate soulx
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements_soulx.txt
# startup
TTS_PROVIDER=soulx python service.py
```


# Core Workflow

## Workflow Engine Driven

The core process of podcast generation is driven by the LangGraph workflow engine, including the following steps:
1. **Multi-source Content** Obtain original text content
   - Supports file upload (PDF, DOCX, TXT, etc.)
   - Supports website URL extraction
   - Supports direct text input
2.  **Content Processing**: Preliminary analysis and processing of input content   
   - Content Q&A and completion
   - Content summarization
3. **Outline Generation**: Generate podcast outline based on content, containing multiple segments
   - User instructions 
   - Episode Profile configuration 
   - LLM model configuration
4. **Transcript Generation**: Generate multi-character transcript based on outline
   - Outline
   - Episode Profile configuration 
   - LLM model configuration
5. **Audio Generation**: Convert transcript to speech segments
   - SpeakerProfile configuration 
   - TTS service configuration
6. **Audio Synthesis**: Merge all speech segments into a complete podcast


![Workflow Diagram](docs/images/workflow.png)


Workflow definition:

```python
# Define workflow graph
workflow = StateGraph(PodcastState)

# Add nodes
workflow.add_node("content_transform", content_transform_node)
workflow.add_node("generate_outline", generate_outline_node)
workflow.add_node("generate_transcript", generate_transcript_node)
workflow.add_node("generate_all_audio", generate_all_audio_node)
workflow.add_node("combine_audio", combine_audio_node)

# Define edges
workflow.add_edge(START, "content_transform")
workflow.add_edge("content_transform", "generate_outline")
workflow.add_edge("generate_outline", "generate_transcript")
workflow.add_conditional_edges(
  "generate_transcript", route_audio_generation, ["generate_all_audio"]
)
workflow.add_edge("generate_all_audio", "combine_audio")
workflow.add_edge("combine_audio", END)

graph = workflow.compile()
```

## Speakers Profile

Speakers Profile defines the voice characteristics of each speaker, including voice ID, background story, personality traits, etc.
  - name: profile name
  - tts_provider: TTS service provider, e.g., elevenlabs, qwen, openai, kokoro, indexTTS2, etc.
  - tts_model: TTS model name, varies according to tts_provider, e.g., tts-1
  - speakers: Speaker list, can contain 1-4 speakers, each speaker contains the following fields
    - name: Speaker name
    - voice_id: Voice ID, used to identify different voice models or service provider voices.
    - backstory: Background story describing the speaker's background, experience, professional field, etc.
    - personality: Personality traits, including speaking style, emotional expression, interaction methods, etc.

![Speakers Profile](docs/images/img2.png)

```json
{
      "tts_provider": "v3api",
      "tts_model": "tts-1",
      "speakers": [
        {
          "name": "Alexandra Hayes",
          "voice_id": "nova",
          "backstory": "Senior business analyst with MBA from Wharton. Specializes in technology market analysis and strategic consulting.",
          "personality": "Strategic thinker, data-driven, focuses on practical business implications and market trends"
        },
        {
          "name": "David Kim",
          "voice_id": "onyx",
          "backstory": "Former startup founder turned venture capitalist. Has invested in 50+ technology companies over the past decade.",
          "personality": "Pragmatic, entrepreneurial, excellent at identifying opportunities and potential challenges"
        },
        {
          "name": "Lisa Thompson",
          "voice_id": "shimmer",
          "backstory": "Chief Technology Officer with 20 years in enterprise software. Expert in technology adoption and digital transformation.",
          "personality": "Implementation-focused, practical, bridges the gap between technical possibilities and business realities"
        }
      ]
}

```

## Episode Profile

Episode Profile defines the generation configuration for each podcast, including the Speakers Profile used, LLM model, number of segments, etc.
  - name: profile name
  - speaker_config: Speakers Profile name, references the configured Speakers Profile
  - outline_model: Outline generation model, e.g., hunyuan-large
  - transcript_model: Transcript generation model, e.g., hunyuan-large
  - outline_provider: Outline generation model provider, e.g., tencent, etc.
  - transcript_provider: Transcript generation model provider, e.g., tencent, etc.
  - num_segments: Number of segments, default value is 4
  - language: Podcast language, e.g., Chinese, English, etc.
  - dialect: Chinese dialect (optional), e.g., mandarin (Mandarin), cantonese (Cantonese), sichuanese (Sichuanese), henanese (Henanese), shanghainese (Shanghainese). Only effective when language is "Chinese". Dialect options will be dynamically displayed based on the selected TTS provider's capability.
  - default_briefing: Custom Prompt instructions for podcast generation

![Episode Profile](docs/images/img3.png)  

```json
 {
      "speaker_config": "business_analysts",
      "outline_model": "hunyuan-large",
      "outline_provider": "tencent",
      "transcript_model": "hunyuan-large",
      "transcript_provider": "tencent",
      "num_segments": 4,
      "language": "中文",
      "dialect": "mandarin",
      "default_briefing": "Provide a comprehensive business analysis covering market implications, strategic considerations, and practical business applications. Focus on actionable insights and real-world impact."
}
```


## Outline

outline defines the structure of the podcast, including the number of segments and the theme of each segment.
  - segments: Segment list, each segment contains the following fields
    - name: Segment name
    - description: Segment description
    - size: Segment length, optional values are short, medium, long, default value is short

### Outline Generation Example

```json
{
    "segments": [
        {
            "name": "单身也可以很精彩",
            "description": "郭德纲以其丰富的人生经历和对社会现象的独到见解，谈论现代社会中单身的状态，结合自己的观察和感悟，分析单身生活的多彩与可能性，并与听众探讨在追求幸福的路上，单身到底是不是一种值得骄傲的选择。",
            "size": "medium"
        },
        {
            "name": "从甄嬛到现代女性：爱情与婚姻观的演变",
            "description": "借助甄嬛这一角色的成长经历作为引子，探讨在古代宫廷背景下女性对爱情与婚姻的期待与挣扎，并对比现代都市女性如何在追求自我价值实现的同时处理爱情与婚姻的关系。通过古今对比，引发听众对自身情感观的反思，并讨论理想爱情的定义及其在现实生活中的应用。",
            "size": "long"
        }
    ]
}
```

### Outline Generation Prompt

````
You are an AI assistant specialized in creating podcast outlines. Your task is to create a detailed outline for a podcast episode based on a provided briefing. The outline you create will be used to generate the podcast transcript.

Here is the briefing for the podcast episode:
<briefing>
{{ briefing }}
</briefing>

The user has provided content to be used as the context for this podcast episode:
<context>
{% if context is string %}
{{ context }}
{% else %}
{% for item in context %}
<content_piece>
{{ item }}
</content_piece>
{% endfor %}
{% endif %}
</context>

The podcast will feature the following speakers:
<speakers>
{% for speaker in speakers %}
- **{{ speaker.name }}**: {{ speaker.backstory }}
  Personality: {{ speaker.personality }}
{% endfor %}
</speakers>

Please create an outline based on this briefing. Your outline should consist of {{ num_segments }} main segments for the podcast episode, along with a description of each segment. Follow these guidelines:

1. Read the briefing carefully and identify the main topics and themes.
2. **CRITICAL: You MUST create EXACTLY {{ num_segments }} distinct segments - no more, no less.** Each segment should cover a portion of the briefing scope.
3. For each segment, provide a clear and concise name that reflects its content.
4. Write a detailed description for each segment, explaining what will be discussed and provide suggestions of topics according to the context given. The writer will use your suggestion to design the dialogs.
5. Consider the speaker personalities and backstories when planning segments - match content to speaker expertise.
6. Ensure that the segments flow logically from one to the next.
7. This is a whole podcast so no need to reintroduce speakers or topics on each segment. Segments are just markers for us to know to change the topics, nothing else. 
8. Include an introduction segment at the beginning and a conclusion or wrap-up segment at the end.

Format your outline using the following structure:

```json
{
    "segments": [
        {
            "name": "[Segment Name]",
            "description": "[Description of the segment content]",
            "size": "short"
        },
        {
            "name": "[Segment Name]",
            "description": "[Description of the segment content]",
            "size": "medium"
        },
        {
            "name": "[Segment Name]",
            "description": "[Description of the segment content]",
            "size": "long"
        },
    ...
    ]
}
```

Formatting instructions:
{{ format_instructions }}

Additional tips:
- Do not return ```json in your response. Return purely the JSON object in Json compatible format
- **MANDATORY: Create EXACTLY {{ num_segments }} segments. Count them before submitting. The segments array MUST contain precisely {{ num_segments }} items.**
- Make sure the segment names are catchy and informative.
- In the descriptions, include key points or questions that will be addressed in each segment.
- Consider the target audience mentioned in the briefing when crafting your outline.
- If the briefing mentions a guest, include segments for introducing the guest and featuring their expertise.
- The size of the segment should be short, medium or long. Think about the content of the segment and how important it is to the episode.
- IMPORTANT: You MUST return complete JSON format with the outer "segments" key. Your response MUST start with {"segments": and end with }
- CRITICAL: The return format must strictly follow: {"segments": [...]} and not just the array itself
- Each segment must have 'name', 'description' and 'size' keys
- Must output in {{ language }}
- **FINAL REMINDER: Your JSON response MUST contain EXACTLY {{ num_segments }} segments in the array. Verify the count!**


Please provide your outline now, following the format and guidelines provided above. Remember: EXACTLY {{ num_segments }} segments are required.

````

## Transcript

Transcript defines the dialogue content of the podcast, each dialogue contains the speaker's name and their dialogue.
- speaker: Speaker name, references the speaker in the configured Speakers Profile
- dialogue: Speaker's dialogue content (supports dialects and voice tags)
- emotion: Speaker's tone and emotion category (dynamically generated emotion description)

### Dialect Support

When the `dialect` field is set in Episode Profile (non-mandarin), the generated dialogue content will use the specified dialect:
- **Cantonese (cantonese)**: Uses Cantonese vocabulary such as "我哋", "係", "唔", etc.
- **Sichuanese (sichuanese)**: Uses Sichuanese vocabulary such as "要得", "巴适", "噻", etc.
- **Henanese (henanese)**: Uses Henanese vocabulary such as "恁", "中不中", "得劲儿", etc.
- **Shanghainese (shanghainese)**: Uses Shanghainese vocabulary such as "侬", "阿拉", "覅", etc.

### Voice Tags

Supported TTS providers (such as SoulX) can embed voice tags in dialogues to enhance naturalness:
- `[laughter]` - Laughter
- `[sigh]` - Sigh
- `[breathing]` - Breathing sound
- `[coughing]` - Cough
- `[throat_clearing]` - Throat clearing

Voice tags are automatically embedded into dialogue text, making the generated speech more natural and authentic.

### 1. Transcript Generation Example


```json
[
  {
    "speaker": "郭德纲",
    "dialogue": "大家好，欢迎来到《娱乐头条》，我係郭德纲。今日我想同大家倾一倾，关于单身嘅话题。你哋知唔知，喺我眼中，单身唔係一种缺陷，而係一种选择。[breathing]单身嘅生活，其实可以好精彩。[laughter]我哋现代社会，啲人成日催婚，好似单身就低人一等咁。[sigh]但其实，单身可以让人更专注于自己嘅生活同事业。",
    "emotion": "带着轻松的语气表达对单身看法的支持"
  },
  {
    "speaker": "甄嬛",
    "dialogue": "郭老师，你说得好有道理。[breathing]喺我看来，无论古代定现代，女性都应该有选择自己生活方式嘅权利。[coughing]以前喺宮中，我为了生存同复仇，不得不争斗。但系，如果可以重来，我希望我能够更自由地选择我想要嘅爱情同婚姻。",
    "emotion": "用平和的语气表达对女性自主权的支持"
  },
  {
    "speaker": "郭德纲",
    "dialogue": "说得好，甄嬛姑娘。[laughter]其实，我见过好多单身嘅朋友，佢哋生活得好好，有自己的事业，有啲兴趣爱好，仲有好多时间去旅行，去体验生活。[breathing]单身唔係终点，而是一个过程，一个让你更加了解自己，发现生活更多可能性嘅过程。",
    "emotion": "带着赞赏的语气认同甄嬛的观点，并补充单身的积极面"
  },
  ...
]
```

### 2. Transcript Generation Prompt

````
You are an AI assistant specialized in creating podcast transcripts. 
Your task is to generate a transcript for a specific segment of a podcast episode based on a provided briefing and outline. 
The transcript will be used to generate podcast audio. Follow these instructions carefully:

{% if dialect and dialect != "mandarin" %}
{% set dialect_names = {
    "cantonese": "粤语",
    "sichuanese": "四川话", 
    "henanese": "河南话",
    "shanghainese": "上海话"
} %}
{% set dialect_display = dialect_names.get(dialect, dialect) %}
CRITICAL: All dialogue MUST be written in {{ dialect_display }} dialect, NOT standard Mandarin. Use authentic {{ dialect_display }} vocabulary and expressions.

Example (Dialogue in {{ dialect_display }}):
{% if dialect == "cantonese" %}
"你今日係咪去咗街市買餸啊？我見到個魚檔啲海魚幾新鮮，不如聽日一齊去睇下？
今朝早起身個天陰陰濕濕，仲以為會落雨，點知出到街又出太陽，真係估佢唔到！
阿媽煲咗成三個鐘嘅蓮藕湯，你飲多碗啦，唔好嘥咗佢心機呀！
呢排公司個冷氣凍到震，我帶多件外套返工先得，如果唔係實凍親！
呢間茶餐廳嘅奶茶真係正，茶味濃奶又滑，我每個禮拜都要嚟飲三次！
你套戲睇完未呀？我等到頸都長埋，快啲傳返個檔案俾我啦！"
{% elif dialect == "sichuanese" %}
"你咋个恁么摸嘛！搞快点儿撒，电影都要开场喽，等得花儿都谢完咯，再慢点儿怕连票都白买了！
今天这个回锅肉才叫安逸惨了，色香味硬是全占完，吃起满嘴香，巴适得我都想喊天！
你莫紧到在那塌塌旋来旋去的嘛，赶紧过来搭把手，屋头都乱成鸡窝了，看起都心烦！
他那个娃儿一天到黑费得不得了，不是爬树掏鸟窝就是撵到狗跑，简直就是个 "费头子"，管都管不住！
你看你穿得周吴郑王的，是不是要切相亲哦？搞得这么抻展，生怕别个看不上你嗦！"
{% elif dialect == "henanese" %}
"俺说恁这衣裳在哪儿买的呀？瞅着可真排场，赶明儿俺也去扯一块布做一身中不中？
恁咋这时候才来咧？俺搁这儿等得前心贴后心，肚里饥得咕咕叫唤！
这碗烩面做得真得劲儿！恁赶紧尝尝啥味儿，香得嘞，一口下去美咋啦！
俺夜个黑喽碰见个老熟人，拽住俺喷空儿喷到半夜，困得俺眼皮直打架！"
{% elif dialect == "shanghainese" %}
"今朝天气邪气好，阿拉到外滩去白相相好伐？侬看黄浦江浪向船来船往，对过陆家嘴嗰高楼大厦全部侪勒嗨太阳底下闪闪发光。
哎呦，交关漂亮啊！等歇吾伲去城隍庙买点五香豆搭梨膏糖吃吃，再到小笼馒头店门口排队，热烘烘嗰南翔小笼，一咬一包汤，鲜得眉毛也要落脱哉！"
{% endif %}

{% endif %}
First, review the briefing for the podcast episode:
<briefing>
{{ briefing }}
</briefing>

The user has provided content to be used as the context for this podcast episode:
<context>
{% if context is string %}
{{ context }}
{% else %}
{% for item in context %}
<content_piece>
{{ item }}
</content_piece>
{% endfor %}
{% endif %}
</context>

IMPORTANT: The context above is ONLY reference material. Names mentioned in the context ("分享嘉宾", etc.) are NOT speakers in this podcast. They are just part of the source material.

The podcast features the following speakers:
<speakers>
{% for speaker in speakers %}
- **{{ speaker.name }}**: {{ speaker.backstory }}
  Personality: {{ speaker.personality }}
{% endfor %}
</speakers>

EMOTION GENERATION:
For each dialogue, dynamically generate an emotion description based on these 8 dimensions: 高兴(Joy), 愤怒(Anger), 悲伤(Sadness), 害怕(Fear), 厌恶(Disgust), 忧郁(Melancholy), 惊讶(Surprise), 平静(Calm).

Process:
1. Analyze the dialogue content, speaker personality, and conversational context
2. Identify the primary emotional dimension(s) from the 8 dimensions above
3. Generate a descriptive emotion text that includes voice characteristics (tone, pace, intensity)
4. CRITICAL: The emotion description MUST be output in {{ language }} (same language as the dialogue)

Examples (if language is Chinese): "带着喜悦和热情地说着", "用坚定的语气表达轻微的愤怒", "用低沉的声音传达深深的悲伤", "带着惊讶的兴奋说着", "用深思的停顿传达平静的反思"
Examples (if language is English): "speaking with joy and enthusiasm", "expressing mild anger with a firm tone", "conveying deep sadness with a somber voice", "speaking with surprised excitement", "conveying calm reflection with thoughtful pauses"

Guidelines:
- Create descriptive phrases (not single words) that guide voice synthesis
- Match emotion intensity to dialogue content
- Vary emotions naturally throughout the conversation
- Use "speaking calmly" or "neutral tone" only for purely informational content
- CRITICAL: Emotion descriptions must be in {{ language }}, matching the language of the dialogue

{% if supports_voice_tags and available_voice_tags %}
VOICE TAGS (Paralinguistic Controls):
The TTS provider supports voice tags for adding natural paralinguistic elements to dialogue. You MUST embed these tags directly in the dialogue text to enhance realism and make conversations more natural.

CRITICAL: You MUST ONLY use voice tags from the following approved list. DO NOT create or use any voice tags that are not in this list.

Approved voice tags list (ONLY use these):
{% for tag in available_voice_tags %}
- {{ tag }}
{% endfor %}

Usage guidelines:
- IMPORTANT: You MUST use voice tags FREQUENTLY throughout the dialogue to make conversations more natural and realistic
- Aim to include at least 2-3 voice tags per dialogue turn when appropriate
- Place tags at natural positions in the dialogue:
  * After expressions of amusement or humor: "[laughter]，这真是太有趣了！"
  * When showing hesitation or thinking: "让我想想[breathing]...我觉得可以这样处理。"
  * When expressing frustration or relief: "[sigh]，我觉得这个问题比较复杂。"
  * During natural pauses or transitions: "这个嘛[throat_clearing]，我们需要考虑一下。"
  * When showing physical reactions: "[coughing]，让我重新解释一下。"
- Use voice tags to enhance emotional expression and make dialogue feel more human
- Voice tags should complement the emotion and context, making conversations feel more authentic
- Examples of natural voice tag usage:
  * "[laughter]，你这话说得太对了！不过[breathing]，我觉得还有一点需要补充..."
  * "[sigh]，这个问题确实比较复杂。让我想想[breathing]...我觉得可以这样处理[laughter]。"
  * "这个嘛[throat_clearing]，我们需要从多个角度来考虑。首先[breathing]..."
{% endif %}

Next, examine the outline produced by our director:
<outline>
{{ outline }}
</outline>

{% if transcript %}
Here is the current transcript so far:
<transcript>
{{ transcript }}
</transcript>
{% endif %}

{% if is_final %}
This is the final segment of the podcast. Make sure to wrap up the conversation and provide a conclusion.
{% endif %}

You will focus on creating the dialogue for the following segment ONLY: 
<segment>
{{ segment }}
</segment>

Follow these format requirements strictly:
   - Use the actual speaker names ({{ speaker_names|join(', ') }}) to denote speakers.
   - The "emotion" for each dialogue MUST be a dynamically generated descriptive text based on the 8-dimension framework (高兴/愤怒/悲伤/害怕/厌恶/忧郁/惊讶/平静).
   - Analyze dialogue content, speaker personality, and context → Identify emotional dimension → Generate descriptive emotion text with voice characteristics
   - CRITICAL: The emotion description MUST be output in {{ language }} (standard Chinese or English){% if dialect and dialect != "mandarin" %}, but the dialogue itself MUST be in {{ dialect_display }} dialect{% endif %}
   - Examples (if language is Chinese): "带着喜悦和热情地说着", "用坚定的语气表达轻微的愤怒", "用低沉的声音传达深深的悲伤"
   - Examples (if language is English): "speaking with joy and enthusiasm", "expressing mild anger with a firm tone", "conveying deep sadness with a somber voice"
   - Choose which speaker should speak based on their personality, backstory, and the content being discussed.
   - Stick to the segment, do not go further than what's requested. Other agents will do the rest of the podcast.
   - The transcript must have at least {{ turns }} turns of messages between the speakers.
   - Each speaker should contribute meaningfully based on their expertise and personality.
   
```json
{
    "transcript": [
        {
            "speaker": "[Actual Speaker Name]",
            "dialogue": "[Speaker's dialogue based on their personality and expertise{% if dialect and dialect != "mandarin" %}. CRITICAL: This dialogue MUST be written entirely in {{ dialect_display }} dialect using authentic {{ dialect_display }} vocabulary, expressions, and sentence patterns. DO NOT use standard Mandarin.{% endif %}{% if supports_voice_tags and available_voice_tags %}. You MUST frequently embed voice tags from the approved list ({{ available_voice_tags|join(', ') }}) naturally throughout the dialogue to enhance realism. Use 2-5 voice tags per dialogue turn when appropriate. ONLY use tags from the approved list.{% endif %}]",
            "emotion": "[Dynamically generated emotion description based on 8-dimension framework, MUST be in {{ language }}. Examples (Chinese): '带着喜悦和热情地说着', '用坚定的语气表达轻微的愤怒', '用低沉的声音传达深深的悲伤'. Examples (English): 'speaking with joy and enthusiasm', 'expressing mild anger with a firm tone', 'conveying deep sadness with a somber voice']"
        },
    ...
    ]
}
```

Formatting instructions:
{{ format_instructions}}

Guidelines for creating the transcript:
   - Do not return ```json in your response. Return purely the JSON object in Json compatible format
   - Ensure the conversation flows naturally and covers all points in the outline.
{% if dialect and dialect != "mandarin" %}
   - CRITICAL: The dialogue itself MUST be written entirely in **{{ dialect_display }} dialect** using authentic {{ dialect_display }} vocabulary, expressions, and sentence patterns. DO NOT use standard Mandarin.
{% else %}
   - CRITICAL: Must output in {{ language }} - this applies to BOTH the "dialogue" field AND the "emotion" field. All text output must be in {{ language }}.
{% endif %}
   - CRITICAL: The "emotion" field MUST be output in {{ language }}
   - Content expression must be clear, highly conversational, and conform to podcast script format and content requirements. Use everyday conversational tone, avoid formal writing and academic language.
   - Character interactions must be highly humanized with authentic dialogue patterns:
     * Use exclamations (like "wow", "hmm", "ah", etc.) to express emotions
     * Include natural reactions (showing surprise, agreement, confusion, etc.)
     * Ensure natural topic flow with interactions and responses like real human conversations
     * Use appropriate verbal tics and tone words to enhance authenticity
{% if supports_voice_tags and available_voice_tags %}
     * CRITICAL: You MUST frequently embed voice tags from the approved list ({{ available_voice_tags|join(', ') }}) in dialogue to make conversations more natural
     * Use voice tags generously - aim for 2-5 voice tags per dialogue turn when contextually appropriate
     * Voice tags make conversations feel more human and realistic - use them to enhance emotional expression, show thinking pauses, add natural reactions
     * ONLY use voice tags from the approved list above - DO NOT invent new tags
{% endif %}
   - Content quality requirements:
     * Basic information must be accurate and reasonable
     * Content must have depth and value, not remaining superficial
     * While comprehensively presenting the original content, elevate it to make it richer and more interesting
   - Avoid long monologues; keep exchanges between speakers balanced.
   - Use appropriate transitions between topics.
   - Ensure each speaker's dialogue style matches their personality and expertise.
   - Strategically choose speakers based on who would naturally contribute to each topic.
   - This is a whole podcast so no need to reintroduce speakers or topics on each segment. Segments are just markers for us to know to change the topics, nothing else. 
   - IMPORTANT: You MUST return complete JSON format with the outer "transcript" key. Your response MUST start with {"transcript": and end with }
   - CRITICAL: You MUST ONLY use the EXACT speaker names as provided here: {{ speaker_names|join(', ') }}
   - DO NOT use generic terms like "主持人", "嘉宾", "记者" etc. - use the exact names from the list above
   - For each dialogue entry, the "speaker" field MUST be one of these exact names: {{ speaker_names|join(', ') }}
   - CRITICAL: For each dialogue entry, the "emotion" field MUST be a dynamically generated descriptive text based on the 8-dimension framework (高兴/愤怒/悲伤/害怕/厌恶/忧郁/惊讶/平静)
   - Generate descriptive emotion phrases with voice characteristics based on dialogue content, speaker personality, and context
   - CRITICAL: The return format must strictly follow: {"transcript": [...]} and not just the array itself
   - Each dialogue item MUST have exactly four keys: 'speaker', 'dialogue', 'emotion', and 'speed' (no nested objects)
   - CRITICAL: Do not nest JSON objects inside the dialogue field. The dialogue field must contain only text.

When you're ready, provide the transcript. 
Remember, you are creating a realistic podcast conversation based on the given information. 
Make it informative, engaging, and natural-sounding while adhering to the format requirements.
````


# Test Podcast Generation

## 1. After 20 Years of Operation, Yakult Closes Shanghai Factory (4 Speakers, OpenAI TTS Generated)

- [Yakult Podcast Example](./docs/voices/yangleduo.mp3)


## 2. Lei Jun: The World Will Silently Reward Diligent and Honest People (3 Speakers, OpenAI TTS Generated)
- [Lei Jun Podcast Example](./docs/voices/leijun.mp3)

## 3. Who Won the Magnolia Awards? (1 Speaker, OpenAI TTS Generated)

- [Magnolia Podcast Example](./docs/voices/white.mp3) 

## 4. Higress Agent Gateway Plugin Development Challenge Competition (2 Speakers, Kokoro TTS Generated)

- [Higress Agent Podcast Example](./docs/voices/higress.mp3) 

## 5. Voice Cloning (Guo Degang + Zhen Huan) + Cantonese + Voice Tags (2 Speakers, Soulx TTS Generated)

- [Soulx TTS Podcast Example](./docs/voices/demooo0.mp3)


# Podica Studio PPT and Video Introduction
- [Podica Studio Introduction and Usage Video Bilibili](https://www.bilibili.com/video/BV1xvmYBsELS)








