# qwen-tts
- https://help.aliyun.com/zh/model-studio/qwen-tts?spm=a2ty_o06.30285417.0.0.32fcc921dpQPQO
- https://qwen.ai/blog?id=f50261eff44dfc0dcbade2baf1b527692bdca4cd&from=research.research-list
- Rate Limit: https://help.aliyun.com/zh/model-studio/rate-limit?spm=a2c4g.11186623.help-menu-2400256.d_0_0_3.3ee3407dnAbYVM

# 数据集
- https://github.com/Tencent-Hunyuan/Hunyuan-7B
- https://github.com/dbccccccc/ttsfm
- 
# voice provider
- https://openai.fm/
- https://elevenlabs.io/blog/eleven-v3-audio-tags-expressing-emotional-context-in-speech
- https://indextts.cn/
- https://github.com/nari-labs/dia2
- https://www.chatterbox.run/
- https://kyutai.org/tts
- https://github.com/Soul-AILab/SoulX-Podcast
- https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- https://elevenlabs.io/blog/v3-audiotags
- https://murf.ai/falcon
- https://nerdynav.com/open-source-ai-voice/
- https://www.resemble.ai/chatterbox/
- https://fish.audio/zh-CN/?fpr=nerdynav
- https://github.com/fishaudio/fish-speech
- https://inworld.ai/tts
- https://huggingface.co/spaces/TTS-AGI/TTS-Arena-V2
- https://www.minimax.io/audio



# free tpu cloud
- https://sites.research.google/trc/about/


# 第三方平台
- https://laozhang.ai/
- https://api.gpt.ge/

```
ssh -L 9000:127.0.0.1:9000 -p 38376 root@connect.nmb1.seetacloud.com
```

```
conda create --name=indextts python=3.12
conda activate indextts
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements_indextts.txt
pip install "huggingface_hub[cli]"  -i https://pypi.tuna.tsinghua.edu.cn/simple

huggingface-cli download --resume-download IndexTeam/IndexTTS-2  --local-dir ./checkpoints/IndexTeam/IndexTTS-2

conda create --name=soulx python=3.12


# base model
huggingface-cli download --resume-download Soul-AILab/SoulX-Podcast-1.7B --local-dir pretrained_models/SoulX-Podcast-1.7B

# dialectal model
huggingface-cli download --resume-download Soul-AILab/SoulX-Podcast-1.7B-dialect --local-dir ./pretrained_models/SoulX-Podcast-1.7B-dialect


```
