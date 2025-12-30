import asyncio
import os
import re
from pathlib import Path
from typing import Dict, List, Union

# from esperanto import AIFactory
from .factory import CustomAIFactory as AIFactory
from langchain_core.runnables import RunnableConfig
from loguru import logger


from .core import (
    clean_thinking_content,
    combine_audio_files,
    create_validated_transcript_parser,
    get_outline_prompter,
    get_transcript_prompter,
    outline_parser,
)
from .emotions import EmotionConfig
from .speed import SpeedConfig
from .state import PodcastState


async def content_transform_node(state: PodcastState, config: RunnableConfig) -> Dict:
    """处理内容中的问答，如果内容包含问题则调用大模型进行回答
    如果内容长度大于10000，则根据briefing对内容进行摘要处理"""
    logger.info(f"Content transform state keys: {state.keys()}")
    logger.info("检查内容是否需要问答处理或摘要处理")
    
    configurable = config.get("configurable", {})
    qa_provider = configurable.get("qa_provider", "openai")
    qa_model_name = configurable.get("qa_model", "gpt-4o-mini")
    
    content = state["content"]
    processed_content = content
    briefing = state.get("briefing", "")
    
    # 创建问答模型
    qa_model = AIFactory.create_language(
        qa_provider,
        qa_model_name,
        config={"max_tokens": 2000},
    ).to_langchain()
    
    # 构建判断提示词
    judge_prompt = """
    请判断以下内容是否需要问答处理或信息补充。如果内容包含以下任一情况，请回答"需要"，否则回答"不需要"：
    1. 包含明确的问题（如疑问句、问号结尾等）
    2. 要求讨论或解释某个话题
    3. 内容不完整，需要更多背景信息才能理解
    4. 包含需要最新信息更新的内容（如近期事件、人物状态等）
    
    内容：
    {content}
    
    你的判断（只回答"需要"或"不需要"）：
    """
    
    # 构建摘要提示词
    summary_prompt = """
    请根据以下播客简介，对提供的内容进行摘要处理，提取与简介主题最相关的信息。
    
    播客简介：
    {briefing}
    
    内容：
    {content}
    
    请生成一个精炼的摘要，保留与播客主题最相关的关键信息，摘要长度最多不超过2000字。
    摘要应该保持原文的核心观点和关键事实，同时与播客简介中描述的主题高度相关。
    """
    
    # 处理内容
    if isinstance(content, str):
        # 判断是否需要摘要处理
        if len(content.strip()) > 5000:
            logger.info(f"内容长度为{len(content.strip())}，需要进行摘要处理")
            
            # 构建摘要提示词
            prompt_text = summary_prompt.format(briefing=briefing, content=content)
            logger.info("调用大模型进行摘要处理")
            summary_response = await qa_model.ainvoke(prompt_text)
            processed_content = summary_response
            logger.info(f"摘要处理完成，摘要长度：{len(summary_response.content)}")
            return {"content": processed_content}
        
        # 判断是否需要问答处理
        if len(content.strip()) >= 500:
            print(f"内容长度为{len(content.strip())}，不需要问答处理")
            return {"content": processed_content}
        
        judge_text = judge_prompt.format(content=content)
        judge_response = await qa_model.ainvoke(judge_text)
        
        if "需要" in judge_response.content:
            logger.info("大模型判断内容需要问答处理")
            
            # 构建问答提示词
            qa_prompt = """
            你是一个专业的问答助手。请对以下内容进行回答和补充：
            
            {content}
            
            请提供详细、准确、全面的回答。如果内容包含多个问题，请逐一回答。
            如果内容是关于某个话题的讨论要求，请提供该话题的背景信息、关键点和讨论方向。
            如果内容涉及近期事件或人物状态，请提供最新相关信息。
            """
            
            prompt_text = qa_prompt.format(content=content)
            logger.info(f"调用大模型进行问答处理，提示词：{prompt_text}")
            qa_response = await qa_model.ainvoke(prompt_text)
            processed_content = qa_response
        else:
            logger.info("大模型判断内容不需要问答处理")
    
    elif isinstance(content, list):
        processed_items = []
        for item in content:
            if isinstance(item, str):
                # 判断是否需要摘要处理
                if len(item.strip()) > 5000:
                    logger.info(f"列表项长度为{len(item.strip())}，需要进行摘要处理")
                    
                    # 构建摘要提示词
                    prompt_text = summary_prompt.format(briefing=briefing, content=item)
                    logger.info("调用大模型进行摘要处理")
                    summary_response = await qa_model.ainvoke(prompt_text)
                    processed_items.append(summary_response)
                    logger.info(f"摘要处理完成，摘要长度：{len(summary_response.content)}")
                    continue
                
                # 判断是否需要问答处理
                if len(item.strip()) >= 500:
                    print(f"内容长度为{len(item.strip())}，不需要问答处理")
                    processed_items.append(item)
                    continue

                judge_text = judge_prompt.format(content=item)
                judge_response = await qa_model.ainvoke(judge_text)
                
                if "需要" in judge_response.content:
                    logger.info("大模型判断列表项需要问答处理")
                    
                    # 构建问答提示词
                    qa_prompt = """
                    你是一个专业的问答助手。请对以下内容进行回答和补充：
                    
                    {content}
                    
                    请提供详细、准确、全面的回答。如果内容包含多个问题，请逐一回答。
                    如果内容是关于某个话题的讨论要求，请提供该话题的背景信息、关键点和讨论方向。
                    如果内容涉及近期事件或人物状态，请提供最新相关信息。
                    """
                    
                    prompt_text = qa_prompt.format(content=item)
                    logger.info(f"调用大模型进行问答处理，提示词：{prompt_text}")
                    qa_response = await qa_model.ainvoke(prompt_text)
                    processed_items.append(qa_response)
                else:
                    logger.info("大模型判断列表项不需要问答处理")
                    processed_items.append(item)
            else:
                processed_items.append(item)
        processed_content = processed_items
    
    return {"content": processed_content}


async def generate_outline_node(state: PodcastState, config: RunnableConfig) -> Dict:
    """Generate podcast outline from content and briefing"""
    logger.info(f"Generate outline state keys: {state.keys()}")
    logger.info("Starting outline generation")

    configurable = config.get("configurable", {})
    outline_provider = configurable.get("outline_provider", "openai")
    outline_model_name = configurable.get("outline_model", "gpt-4o-mini")

    # Create outline model
    outline_model = AIFactory.create_language(
        outline_provider,
        outline_model_name,
        config={"max_tokens": 3000, "structured": {"type": "json"}},
    ).to_langchain()

    # Generate outline
    outline_prompt = get_outline_prompter()
    outline_prompt_text = outline_prompt.render(
        {
            "briefing": state["briefing"],
            "num_segments": state["num_segments"],
            "context": state["content"],
            # language
            "language": state["language"],
            "speakers": state["speaker_profile"].speakers
            if state["speaker_profile"]
            else [],
        }
    )
    # print(f"outline_prompt_text:=========\n {outline_prompt_text}\n=================")
    # 重试三次，直到无异常返回
    for attempt in range(3):
        try:
            outline_preview = await outline_model.ainvoke(outline_prompt_text)
            outline_preview.content = clean_thinking_content(outline_preview.content)
            outline_result = outline_parser.invoke(outline_preview.content)
            break  # 成功则跳出循环
        except Exception as e:
            logger.warning(f"Outline 解析失败（第 {attempt + 1} 次）：{e}")
            if attempt == 2:  # 最后一次仍失败，则抛出异常
                raise RuntimeError(f"Outline 解析三次均失败 {e}") from e
            # 短暂等待后重试
            await asyncio.sleep(1)

    logger.info(f"Generated outline with {len(outline_result.segments)} segments")
    # exit()
    return {"outline": outline_result}


async def generate_transcript_node(state: PodcastState, config: RunnableConfig) -> Dict:
    """Generate conversational transcript from outline"""
    logger.info(f"Generate transcript state keys: {state.keys()}")
    logger.info("Starting transcript generation")

    assert state.get("outline") is not None, "outline must be provided"
    assert state.get("speaker_profile") is not None, "speaker_profile must be provided"

    configurable = config.get("configurable", {})
    transcript_provider: str = configurable.get("transcript_provider", "openai")
    transcript_model_name: str = configurable.get("transcript_model", "gpt-4o-mini")

    # Create transcript model
    transcript_model = AIFactory.create_language(
        transcript_provider,
        transcript_model_name,
        config={"max_tokens": 5000, "structured": {"type": "json"}},
    ).to_langchain()

    # Create validated transcript parser
    speaker_profile = state["speaker_profile"]
    assert speaker_profile is not None, "speaker_profile must be provided"
    speaker_names = speaker_profile.get_speaker_names()
    
    # Load emotions config
    emotions_config = state["emotions_config"]
    assert emotions_config is not None, "emotions_config must be provided"
    emotions_names = emotions_config.get_emotions_names()
    emotions = emotions_config.get_all_emotions()
    # speed names
    speed_config = state["speed_config"]
    assert speed_config is not None, "speed_config must be provided"
    speed_names = speed_config.get_speed_names()

    # Generate transcript for each segment
    outline = state["outline"]
    language = state["language"]
    assert outline is not None, "outline must be provided"
    assert language is not None, "language must be provided"

    # Validate transcript
    validated_transcript_parser = create_validated_transcript_parser(speaker_names, emotions_names, speed_names)

    # Get TTS capability for voice tags support
    tts_provider = speaker_profile.tts_provider
    tts_model = speaker_profile.tts_model
    supports_voice_tags = False
    available_voice_tags = []
    
    try:
        from .factory import CustomAIFactory
        # Try to get TTS capability
        try:
            tts_instance = CustomAIFactory.create_text_to_speech(tts_provider, tts_model)
            if hasattr(tts_instance, 'capability'):
                capability = tts_instance.capability
                supports_voice_tags = capability.supports_voice_tags
                available_voice_tags = capability.available_voice_tags or []
                logger.info(f"TTS provider {tts_provider} supports_voice_tags: {supports_voice_tags}, available_voice_tags: {available_voice_tags}")
        except Exception as e:
            logger.warning(f"Failed to get TTS capability for {tts_provider}: {e}")
    except Exception as e:
        logger.warning(f"Failed to import TTS factory: {e}")

    transcript = []
    for i, segment in enumerate(outline.segments):
        logger.info(
            f"Generating transcript for segment {i + 1}/{len(outline.segments)}: {segment.name}"
        )

        is_final = i == len(outline.segments) - 1
        is_first = i == 0
        is_middle = not is_first and not is_final
        turns = 2 if segment.size == "short" else 5 if segment.size == "medium" else 8

        # Get dialect from state
        dialect = state.get("dialect")
        
        data = {
            "briefing": state["briefing"],
            "outline": outline,
            "context": state["content"],
            "segment": segment,
            "is_final": is_final,
            "is_first": is_first,
            "is_middle": is_middle,
            "turns": turns,
            # language
            "language": language,
            "dialect": dialect,  # Add dialect to template data
            "speakers": speaker_profile.speakers,
            "speaker_names": speaker_names,
            "emotions": emotions,
            "emotions_names": emotions_names,
            "speed_names": speed_names,
            # voice tags support
            "supports_voice_tags": supports_voice_tags,
            "available_voice_tags": available_voice_tags,
            # "transcript": transcript,
        }

        transcript_prompt = get_transcript_prompter()
        transcript_prompt_rendered = transcript_prompt.render(data)
        # print(f"transcript_prompt_rendered:=========\n {transcript_prompt_rendered}\n=================")
        # 重试三次，直到无异常返回
        for attempt in range(3):
            try:
                transcript_preview = await transcript_model.ainvoke(transcript_prompt_rendered)
                transcript_preview.content = clean_thinking_content(transcript_preview.content)
                result = validated_transcript_parser.invoke(transcript_preview.content)
                logger.info(f"Generated {len(result.transcript)} dialogue segments, {result.transcript}")
                transcript.extend(result.transcript)
                break  # 成功则跳出循环
            except Exception as e:
                logger.warning(f"Transcript 解析失败（第 {attempt + 1} 次）：{e}")
                if attempt == 2:  # 最后一次仍失败，则抛出异常
                    raise RuntimeError("Transcript 解析三次均失败") from e
                # 短暂等待后重试
                await asyncio.sleep(1)

    logger.info(f"Generated transcript with {len(transcript)} dialogue segments")
    return {"transcript": transcript}


def route_audio_generation(state: PodcastState, config: RunnableConfig) -> str:
    """Route to sequential batch processing of audio generation"""
    transcript = state["transcript"]
    total_segments = len(transcript)

    logger.info(
        f"Routing {total_segments} dialogue segments for sequential batch processing"
    )

    # Return node name for sequential processing
    return "generate_all_audio"

async def generate_all_audio_node(state: PodcastState, config: RunnableConfig) -> Dict:
    """Generate all audio clips using sequential batches to respect API limits"""
    transcript = state["transcript"]
    output_dir = state["output_dir"]
    total_segments = len(transcript)
    emotions_config = state["emotions_config"]
    speed_config = state["speed_config"]
    
    # Get batch size from environment variable, default to 5
    batch_size = int(os.getenv("TTS_BATCH_SIZE", "5"))
    logger.info(f"Using TTS batch size: {batch_size}")

    assert state.get("speaker_profile") is not None, "speaker_profile must be provided"

    # Get TTS configuration from speaker profile
    speaker_profile = state["speaker_profile"]
    assert speaker_profile is not None, "speaker_profile must be provided"
    tts_provider = speaker_profile.tts_provider
    tts_model = speaker_profile.tts_model
    voices = speaker_profile.get_voice_mapping()
    custom_voices = speaker_profile.get_custom_voice_mapping()
    
    # Get dialect from state
    dialect = state.get("dialect")

    logger.info(
        f"Generating {total_segments} audio clips in sequential batches of {batch_size}"
    )

    all_clip_paths = []

    # Process in sequential batches
    for batch_start in range(0, total_segments, batch_size):
        batch_end = min(batch_start + batch_size, total_segments)
        batch_number = batch_start // batch_size + 1
        total_batches = (total_segments + batch_size - 1) // batch_size

        logger.info(
            f"Processing batch {batch_number}/{total_batches} (clips {batch_start}-{batch_end - 1})"
        )

        # Create tasks for this batch
        batch_tasks = []
        for i in range(batch_start, batch_end):
            dialogue_info = {
                "dialogue": transcript[i],
                "index": i,
                "output_dir": output_dir,
                "tts_provider": tts_provider,
                "tts_model": tts_model,
                "voices": voices,
                "custom_voices": custom_voices,
                "speaker_profile": speaker_profile,
                "dialect": dialect,  # Pass dialect to audio generation
            }
            task = generate_single_audio_clip(dialogue_info, emotions_config, speed_config)
            batch_tasks.append(task)

        # Process this batch concurrently (but wait before next batch)
        batch_clip_paths = await asyncio.gather(*batch_tasks)
        all_clip_paths.extend(batch_clip_paths)

        logger.info(f"Completed batch {batch_number}/{total_batches}")

        # Small delay between batches to be extra safe with API limits
        if batch_end < total_segments:
            await asyncio.sleep(1)

    logger.info(f"Generated all {len(all_clip_paths)} audio clips")

    return {"audio_clips": all_clip_paths}


async def generate_single_audio_clip(dialogue_info: Dict, emotions_config: EmotionConfig, speed_config: SpeedConfig) -> Path:
    """Generate a single audio clip with emotion and custom voice support"""
    dialogue = dialogue_info["dialogue"]
    index = dialogue_info["index"]
    output_dir = dialogue_info["output_dir"]
    tts_provider = dialogue_info["tts_provider"]
    tts_model_name = dialogue_info["tts_model"]
    voices = dialogue_info["voices"]
    custom_voices = dialogue_info.get("custom_voices", {})
    speaker_profile = dialogue_info.get("speaker_profile")

    logger.info(f"Generating audio clip {index:04d} for {dialogue.speaker}")

    # Create clips directory
    clips_dir = output_dir / "clips"
    clips_dir.mkdir(exist_ok=True, parents=True)

    # Generate filename
    filename = f"{index:04d}.mp3"
    clip_path = clips_dir / filename

    # Create TTS model
    tts_model = AIFactory.create_text_to_speech(tts_provider, tts_model_name)
    
    # Prepare TTS parameters
    tts_kwargs = {}
    
    # Add emotion/instructions if dialogue has emotion
    if hasattr(dialogue, 'emotion') and dialogue.emotion:
        # Use emotion description directly as instructions
        tts_kwargs["instructions"] = dialogue.emotion
        logger.debug(f"Using emotion instructions: {dialogue.emotion}")
    
    # Add custom voice (reference_audio) if speaker has custom voice
    speaker_name = dialogue.speaker
    if speaker_name in custom_voices and custom_voices[speaker_name]:
        custom_voice_path = custom_voices[speaker_name]
        # Check if it's a file path
        if isinstance(custom_voice_path, str):
            voice_path = Path(custom_voice_path)
            if voice_path.exists():
                # Read file and convert to base64
                import base64
                with open(voice_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                tts_kwargs["reference_audio"] = b64_data
                logger.debug(f"Loaded and encoded custom voice file as base64: {custom_voice_path}")
            else:
                # Might be base64 encoded, pass as is
                tts_kwargs["reference_audio"] = custom_voice_path
                logger.debug(f"Using custom voice (base64 or path): {custom_voice_path}")
        else:
            tts_kwargs["reference_audio"] = custom_voice_path
    
    # Get voice ID for this speaker
    voice_id = voices.get(speaker_name, "default")
    
    # If using custom voice, check if voice_id should be "custom"
    if speaker_name in custom_voices and custom_voices[speaker_name]:
        # Some TTS providers require voice_id to be "custom" when using reference_audio
        if voice_id == "custom":
            voice_id = "custom"
        # For providers that support reference_audio with any voice_id, keep the original voice_id
    
    # Add dialect parameters if provided
    dialect = dialogue_info.get("dialect")
    if dialect:
        tts_kwargs["dialect"] = dialect
        logger.debug(f"Using dialect: {dialect} for audio generation")
    
    # print(f"tts_kwargs: {tts_kwargs}")
    # Generate audio with retry logic (5 attempts)
    for attempt in range(5):
        try:
            await tts_model.agenerate_speech(
                text=dialogue.dialogue,
                voice=voice_id,
                output_file=clip_path,
                **tts_kwargs
            )
            logger.info(f"Generated audio clip: {clip_path}")
            break  # 成功则跳出循环
        except Exception as e:
            logger.warning(f"Audio generation failed for clip {index:04d} (attempt {attempt + 1}/5): {e}")
            if attempt == 4:  # 最后一次仍失败，则抛出异常
                logger.error(f"Audio generation failed after 5 attempts for clip {index:04d}")
                raise RuntimeError(f"Audio generation failed after 5 attempts for clip {index:04d}: {e}") from e
            # 短暂等待后重试
            await asyncio.sleep(3)

    return clip_path


async def combine_audio_node(state: PodcastState, config: RunnableConfig) -> Dict:
    """Combine all audio clips into final podcast episode"""
    logger.info("Starting audio combination")

    clips_dir = state["output_dir"] / "clips"
    audio_dir = state["output_dir"] / "audio"

    # Combine audio files
    result = await combine_audio_files(
        clips_dir, f"{state['episode_name']}.mp3", audio_dir
    )

    final_path = Path(result["combined_audio_path"])
    logger.info(f"Combined audio saved to: {final_path}")

    return {"final_output_file_path": final_path}
    return {"final_output_file_path": final_path}
