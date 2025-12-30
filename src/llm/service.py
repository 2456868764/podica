import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Literal
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel
import os
import re
import uvicorn
import time
import numpy as np
import io
import logging
import sys
import asyncio
import base64
import tempfile
from pathlib import Path
from config import config
from transformers import TextStreamer

from tts import TTSFactory
from logger import logger  # 默认已配置好的 logger

app = FastAPI()

# logger 已经在 logger.py 模块导入时自动配置
# 默认输出到控制台和 logs/llm-service.log

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "llm-service"}

# 定义请求和响应的数据模型
class MessageContent(BaseModel):
    type: str
    text: str

class Message(BaseModel):
    role: str
    content: Union[str, List[MessageContent], Dict[str, str]]

    def get_text_content(self) -> str:
        """Extract text content from different message formats"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            # 合并所有文本内容
            return " ".join(
                item.text for item in self.content 
                if isinstance(item, MessageContent) and item.type == "text"
            )
        elif isinstance(self.content, dict):
            # 处理音频或其他类型的内容
            return self.content.get("text", "")
        return ""

class AudioConfig(BaseModel):
    voice: str  # ash, ballad, coral, sage, verse
    format: Literal["wav", "mp3", "flac", "opus", "pcm16"]

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    modalities: Optional[List[Literal["text", "audio"]]] = ["text"]
    audio: Optional[AudioConfig] = None
    n: Optional[int] = 1
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    max_completion_tokens: Optional[int] = None  # 新增参数

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict]
    usage: Dict[str, int]

# 添加新的请求模型用于嵌入
class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]
    encoding_format: str = "float"
    user: str = None

class EmbeddingResponse(BaseModel):
    object: str
    data: List[Dict]
    model: str
    usage: Dict[str, int]

# 添加新的请求模型用于TTS
class TTSRequest(BaseModel):
    model: str = "tts-1"  # tts-1 (speecht5) or tts-1-hd (chattts) or kokoro, index-tts, soulx
    input: str
    voice: str = "alloy"  # OpenAI voices: alloy, echo, fable, onyx, nova, shimmer
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"]] = "mp3"
    speed: Optional[float] = 1.0
    instructions: Optional[str] = None  # Instructions or style parameter for TTS
    reference_audio: Optional[str] = None  # Base64 encoded audio file for voice cloning (IndexTTS, SoulX)
    reference_text: Optional[str] = None  # Optional reference text for voice cloning (SoulX)
    dialect: Optional[str] = None  # Chinese dialect (e.g., "mandarin", "cantonese", "sichuanese", "henanese")
    dialect_prompt: Optional[str] = None  # Dialect prompt text for TTS model

# 全局变量存储模型和tokenizer
model = None
tokenizer = None

# 添加嵌入模型的全局变量
embedding_model = None
embedding_tokenizer = None

# 添加TTS模型的全局变量
tts = None

def load_tts():
    global tts
    if tts is None:
        tts  = TTSFactory.get_tts(config.TTS_PROVIDER)
        tts.load_model()

def load_model(model_path: str):
    global model, tokenizer
    logger.info(f"Loading chat model from {model_path}")
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        logger.info("Chat tokenizer loaded successfully")

    if model is None:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True,
        )
        model.to(config.DEVICE)
        logger.info("Chat model loaded successfully")

def load_embedding_model(model_path: str = "maidalun1020/bce-embedding-base_v1"):
    """Load the embedding model"""
    global embedding_model, embedding_tokenizer
    logger.info(f"Loading embedding model from {model_path}")
    if embedding_model is None:
        embedding_model = AutoModel.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        embedding_model.eval()
        logger.info("Embedding model loaded successfully")
    if embedding_tokenizer is None:
        embedding_tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        logger.info("Embedding tokenizer loaded successfully")

def format_messages(messages: List[Message]) -> List[Dict]:
    """Format messages into Qwen chat format"""
    formatted_messages = []
    for msg in messages:
        text_content = msg.get_text_content()
        formatted_messages.append({
            "role": msg.role,
            "content": text_content
        })
    return formatted_messages

def get_embeddings(texts: Union[str, List[str]]) -> List[List[float]]:
    """Generate embeddings for input texts"""
    if isinstance(texts, str):
        texts = [texts]
    
    # 编码文本
    encoded_inputs = embedding_tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    
    # 生成嵌入
    with torch.no_grad():
        # 使用 embedding_model 而不是 model
        outputs = embedding_model(**encoded_inputs, return_dict=True)
        embeddings = outputs.last_hidden_state[:, 0]  # cls pooler
        embeddings = embeddings / embeddings.norm(dim=1, keepdim=True)  # normalize
        
    return embeddings.tolist()


@app.on_event("startup")
async def startup_event():
    #logger.info("Starting to load LLM model")
    # 加载聊天模型
    #load_model(config.CHAT_MODEL_PATH)
    # 加载嵌入模型
    # logger.info("Starting to load embedding model")
    # load_embedding_model(config.EMBEDDING_MODEL_PATH)
    # 加载TTS模型   
    logger.info("Starting to load TTS model")
    load_tts()
    logger.info("All models loaded successfully")

async def stream_generator(
    input_ids: torch.Tensor,
    model_name: str,
    max_new_tokens: Optional[int] = None,
    temperature: float = 0.7
):
    try:
        # 使用非流式生成，但逐个token返回
        outputs = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens or 512,
            temperature=temperature,
            do_sample=True,
            return_dict_in_generate=True,
            output_scores=True
        )
        
        generated_tokens = outputs.sequences[0][len(input_ids[0]):]
        
        # 逐个token输出
        current_text = ""
        for token in generated_tokens:
            # 解码单个token
            new_text = tokenizer.decode([token], skip_special_tokens=True)
            if not new_text.strip():
                continue
                
            chunk = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "delta": {"content": new_text},
                    "index": 0,
                    "finish_reason": None
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            current_text += new_text
            
            # 添加适当的延迟以模拟流式效果
            await asyncio.sleep(0.02)
            
        # 发送结束标记
        final_chunk = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_name,
            "choices": [{
                "delta": {},
                "index": 0,
                "finish_reason": "stop"
            }]
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
                
    except Exception as e:
        error_chunk = {
            "error": str(e)
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

# 添加音频处理函数
def generate_audio_response(text: str, config: AudioConfig) -> StreamingResponse:
    """Generate audio response with the specified configuration"""
    try:
        logger.info(f"Converting text to audio with voice: {config.voice}")
        audio_data, mime_type = tts.generate_speech(
            text,
            voice=config.voice,
            output_format=config.format
        )
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="response.{config.format}"'
            }
        )
    except Exception as e:
        logger.error(f"Error generating audio response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 添加时间计算函数
def log_time(start_time: float, api_name: str):
    """Log API execution time"""
    end_time = time.time()
    execution_time = end_time - start_time
    logger.info(f"{api_name} execution time: {execution_time:.2f} seconds")

# 修改 chat_completions 函数
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    start_time = time.time()
    try:
        logger.info(f"Request===================================================")
        logger.info(f"Received chat request for model: {request.model}")
        logger.info(f"Request: {request}")
        logger.info(f"=========================================================")
        # audio is not supported yet
        if "audio" in request.modalities:
            raise HTTPException(
                status_code=400,
                detail="Audio output is not supported in streaming mode"
            )

        # 使用 max_completion_tokens 如果提供了的话
        max_tokens = request.max_completion_tokens or request.max_tokens or 512
        # Format messages into prompt
        formatted_messages = format_messages(request.messages)

        tokenized_chat = tokenizer.apply_chat_template(formatted_messages, tokenize=True, add_generation_prompt=True,return_tensors="pt",
                                                enable_thinking=False )
        
        # 设置生成参数
        outputs = model.generate(
            tokenized_chat.to(model.device), 
            max_new_tokens=max_tokens,
            do_sample=True,
            top_k=20,
            top_p=0.8,
            repetition_penalty=1.05,
            temperature=request.temperature or 0.7
        )
        
        response = tokenizer.decode(outputs[0])
        
        # 计算token数量
        input_length = len(tokenized_chat[0])
        output_length = len(outputs[0]) - input_length
        
        chat_response = ChatResponse(
            id=f"chatcmpl-{int(time.time())}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }] * request.n,
            usage={
                "prompt_tokens": input_length,
                "completion_tokens": output_length,
                "total_tokens": input_length + output_length
            }
        )
        log_time(start_time, "chat_completions")
        return chat_response
                
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
        log_time(start_time, "chat_completions (error)")
        raise HTTPException(status_code=500, detail=str(e))

# 添加嵌入接口
@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    start_time = time.time()
    try:
        logger.info(f"Received embedding request for model: {request.model}")
        # 生成嵌入
        embeddings = get_embeddings(request.input)
        
        # 计算token数量
        if isinstance(request.input, str):
            input_tokens = len(embedding_tokenizer.encode(request.input))
            total_tokens = input_tokens
            texts = [request.input]
            logger.info(f"Processing single text with {input_tokens} tokens")
        else:
            input_tokens = sum(len(embedding_tokenizer.encode(text)) for text in request.input)
            total_tokens = input_tokens
            texts = request.input
            logger.info(f"Processing {len(texts)} texts with total {input_tokens} tokens")
        
        # 准备响应
        response_data = [
            {
                "object": "embedding",
                "embedding": embedding,
                "index": i
            }
            for i, embedding in enumerate(embeddings)
        ]
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        response = EmbeddingResponse(
            object="list",
            data=response_data,
            model=request.model,
            usage={
                "prompt_tokens": input_tokens,
                "total_tokens": total_tokens
            }
        )
        log_time(start_time, "create_embeddings")
        return response
        
    except Exception as e:
        logger.error(f"Error in embedding generation: {str(e)}", exc_info=True)
        log_time(start_time, "create_embeddings (error)")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数：处理 base64 编码的音频
def save_base64_audio(base64_audio: str, suffix: str = ".wav") -> str:
    """Save base64 encoded audio to temporary file and return path"""
    try:
        # Decode base64
        audio_bytes = base64.b64decode(base64_audio)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(audio_bytes)
        temp_file.close()
        
        logger.info(f"Saved base64 audio to temporary file: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logger.error(f"Error decoding base64 audio: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid base64 audio: {str(e)}")

# 添加TTS接口
@app.post("/v1/audio/speech")
async def create_speech(request: TTSRequest):
    start_time = time.time()
    temp_audio_file = None
    try:
        dialect = request.dialect if request.dialect else None
        dialect_prompt = request.dialect_prompt if request.dialect_prompt else None
      
        logger.info(f"Received TTS request for model: {request.model}")
        logger.info(f"Received TTS request: input={request.input[:50]}..., voice={request.voice}, instructions={request.instructions}, dialect={dialect}")
        
        # 处理 base64 编码的参考音频
        reference_audio_path = None
        if request.reference_audio:
            try:
                reference_audio_path = save_base64_audio(request.reference_audio)
                temp_audio_file = reference_audio_path
                logger.info(f"Using custom reference audio from base64")
            except Exception as e:
                logger.error(f"Failed to process reference audio: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid reference_audio: {str(e)}")
        
        # 生成音频并获取正确的 MIME 类型
        audio_data, mime_type = tts.generate_speech(
            request.input, 
            request.voice,
            output_format=request.response_format,
            instructions=request.instructions,
            reference_audio=reference_audio_path,
            reference_text=request.reference_text,
            speed=request.speed,
            dialect=dialect,
            dialect_prompt=dialect_prompt
        )
        
        logger.info(f"Speech generated successfully in {request.response_format} format")
        
        response = StreamingResponse(
            io.BytesIO(audio_data),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="speech.{request.response_format}"'
            }
        )
        log_time(start_time, "create_speech")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in speech generation: {str(e)}", exc_info=True)
        log_time(start_time, "create_speech (error)")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary audio file
        if temp_audio_file and os.path.exists(temp_audio_file):
            try:
                os.unlink(temp_audio_file)
                logger.info(f"Cleaned up temporary audio file: {temp_audio_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_audio_file}: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Starting server on http://{config.HOST}:{config.PORT}")
    uvicorn.run("service:app", host=config.HOST, port=config.PORT)
