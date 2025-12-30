"""
方言工具模块
用于处理中文方言的标记、提示文本等
"""
import re
from typing import Optional, Dict, List
from pathlib import Path
import json
import os

# 方言标记映射
DIALECT_TAGS = {
    "sichuan": "<|Sichuan|>",
    "sichuanese": "<|Sichuan|>",  # 别名
    "henan": "<|Henan|>",
    "henanese": "<|Henan|>",  # 别名
    "yue": "<|Yue|>",
    "yueyu": "<|Yue|>",  # 别名
    "cantonese": "<|Yue|>",  # 别名
    "shanghainese": "<|Shanghai|>",  # 上海话（如果支持）
    "mandarin": "",  # 普通话无标记
    "chinese": "",  # 默认中文为普通话
}

# 支持的方言列表
SUPPORTED_DIALECTS = ["mandarin", "sichuan", "sichuanese", "henan", "henanese", "yue", "cantonese", "shanghainese"]

def get_dialect_tag(dialect: Optional[str]) -> str:
    """
    获取方言标记
    
    Args:
        dialect: 方言名称，如 "sichuan", "henan", "yue", "mandarin"
    
    Returns:
        方言标记字符串，如 "<|Sichuan|>", "<|Henan|>", "<|Yue|>"，普通话返回空字符串
    """
    if not dialect:
        return ""
    
    dialect_lower = dialect.lower().strip()
    return DIALECT_TAGS.get(dialect_lower, "")

def add_dialect_tag_to_text(text: str, dialect: Optional[str]) -> str:
    """
    为文本添加方言标记
    
    Args:
        text: 原始文本
        dialect: 方言名称
    
    Returns:
        添加了方言标记的文本
    """
    if not dialect or dialect.lower() == "mandarin":
        return text
    
    dialect_tag = get_dialect_tag(dialect)
    if not dialect_tag:
        return text
    
    # 如果文本已经包含方言标记，不重复添加
    if text.startswith(dialect_tag):
        return text
    
    # 移除文本开头的其他方言标记（如果存在）
    for tag in DIALECT_TAGS.values():
        if tag and text.startswith(tag):
            text = text[len(tag):].lstrip()
            break
    
    # 添加新的方言标记
    return f"{dialect_tag}{text}"

def remove_dialect_tag(text: str) -> str:
    """
    移除文本中的方言标记
    
    Args:
        text: 包含方言标记的文本
    
    Returns:
        移除方言标记后的文本
    """
    for tag in DIALECT_TAGS.values():
        if tag and text.startswith(tag):
            return text[len(tag):].lstrip()
    return text

def detect_dialect_from_text(text: str) -> Optional[str]:
    """
    从文本中检测方言类型
    
    Args:
        text: 包含方言标记的文本
    
    Returns:
        方言名称，如果未检测到则返回 None
    """
    for dialect, tag in DIALECT_TAGS.items():
        if tag and text.startswith(tag):
            return dialect
    return None

def get_default_dialect_prompt(dialect: Optional[str], speaker_index: int = 0) -> str:
    """
    获取默认的方言提示文本
    
    Args:
        dialect: 方言名称
        speaker_index: 说话人索引（用于选择不同的提示文本）
    
    Returns:
        方言提示文本（包含方言标记）
    """
    if not dialect or dialect.lower() == "mandarin":
        return ""
    
    dialect_lower = dialect.lower().strip()
    
    # 规范化方言名称（处理别名）
    normalized_dialect = normalize_dialect_name(dialect_lower) or dialect_lower
    
    # 默认方言提示文本（使用 SoulX 格式）
    default_prompts = {
        "sichuan": [
            "<|Sichuan|>要得要得！前头几个耍洋盘，我后脚就背起铺盖卷去景德镇耍泥巴，巴适得喊老天爷！",
            "<|Sichuan|>哎哟喂，这个搞反了噻！黑神话里头唱曲子的王二浪早八百年就在黄土高坡吼秦腔喽，游戏组专门跑切录的原汤原水，听得人汗毛儿都立起来！"
        ],
        "henan": [
            "<|Henan|>俺这不是怕恁路上不得劲儿嘛！那景德镇瓷泥可娇贵着哩，得先拿咱河南人这实诚劲儿给它揉透喽。",
            "<|Henan|>恁这想法真闹挺！陕北民谣比黑神话早几百年都有了，咱可不兴这弄颠倒啊，中不？恁这想法真闹挺！那陕北民谣在黄土高坡响了几百年，咋能说是跟黑神话学的咧？咱得把这事儿捋直喽，中不中！"
        ],
        "yue": [
            "<|Yue|>真係冇讲错啊！攀山滑雪嘅语言专家几巴闭，都唔及我听日拖成副身家去景德镇玩泥巴，呢铺真系发哂白日梦咯！",
            "<|Yue|>咪搞错啊！陕北民谣响度唱咗几十年，黑神话边有咁大面啊？你估佢哋抄游戏咩！"
        ],
        "shanghai": [
            "<|Shanghai|>侬讲得对个！阿拉上海人做事体就是噶认真，勿会得马虎个。",
            "<|Shanghai|>覅瞎讲八讲！这个事体阿拉老早就晓得勒，勿是现在才晓得个。"
        ]
    }
    
    prompts = default_prompts.get(normalized_dialect, [])
    if prompts and speaker_index < len(prompts):
        return prompts[speaker_index]
    elif prompts:
        return prompts[0]
    
    return ""

def load_dialect_prompts_from_file(dialect: str, file_path: Optional[Path] = None) -> List[str]:
    """
    从文件加载方言提示文本列表
    
    Args:
        dialect: 方言名称
        file_path: 文件路径（可选）
    
    Returns:
        方言提示文本列表
    """
    if file_path is None:
        # 默认路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dialect_file_map = {
            "sichuan": "SoulX-Podcast-main/example/dialect_prompt/sichuan.txt",
            "henan": "SoulX-Podcast-main/example/dialect_prompt/henan.txt",
            "yue": "SoulX-Podcast-main/example/dialect_prompt/yueyu.txt",
            "yueyu": "SoulX-Podcast-main/example/dialect_prompt/yueyu.txt",
        }
        
        dialect_lower = dialect.lower().strip()
        if dialect_lower in dialect_file_map:
            file_path = current_dir / dialect_file_map[dialect_lower]
        else:
            return []
    
    if not file_path.exists():
        return []
    
    prompts = []
    dialect_tag = get_dialect_tag(dialect)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    # 如果行不包含方言标记，添加它
                    if dialect_tag and not line.startswith(dialect_tag):
                        line = f"{dialect_tag}{line}"
                    prompts.append(line)
    except Exception as e:
        import logging
        logger = logging.getLogger("llm-service")
        logger.warning(f"Failed to load dialect prompts from {file_path}: {e}")
    
    return prompts

def is_dialect_supported(dialect: Optional[str]) -> bool:
    """
    检查方言是否受支持
    
    Args:
        dialect: 方言名称
    
    Returns:
        是否支持该方言
    """
    if not dialect:
        return False
    
    dialect_lower = dialect.lower().strip()
    return dialect_lower in SUPPORTED_DIALECTS or dialect_lower in DIALECT_TAGS

def normalize_dialect_name(dialect: Optional[str]) -> Optional[str]:
    """
    规范化方言名称
    
    Args:
        dialect: 方言名称
    
    Returns:
        规范化后的方言名称（用于 SoulX 的格式：sichuan, henan, yue）
    """
    if not dialect:
        return None
    
    dialect_lower = dialect.lower().strip()
    
    # 别名映射到 SoulX 格式
    alias_map = {
        "yueyu": "yue",
        "cantonese": "yue",
        "chinese": "mandarin",
        "sichuanese": "sichuan",  # 映射到 SoulX 格式
        "henanese": "henan",  # 映射到 SoulX 格式
        # "shanghainese": "shanghai",  # 映射到 SoulX 格式
        # "shanghai": "shanghai",  # 映射到 SoulX 格式
    }
    
    normalized = alias_map.get(dialect_lower, dialect_lower)
    
    # 如果规范化后的名称不在支持的列表中，返回原始值（让调用者处理）
    return normalized
