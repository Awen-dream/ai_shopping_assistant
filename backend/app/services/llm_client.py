import os
from openai import OpenAI
import yaml

# 读取配置文件中的 OpenAI Key
def load_openai_key(config_path: str = None) -> str:
    """
    优先从文件读取 API Key
    config_path: 配置文件路径，可选，默认从 backend/config/settings.yaml
    """
    if config_path is None:
        # 默认路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "../../config/settings.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    api_key = cfg.get("openai_api_key")
    if not api_key:
        raise ValueError("Missing 'openai_api_key' in config file")
    return api_key

# 创建 LLM 客户端
def get_llm_client() -> OpenAI:
    api_key = load_openai_key()
    client = OpenAI(api_key=api_key)
    return client


# 示例调用接口
if __name__ == "__main__":
    client = get_llm_client()
    # 示例 prompt
    prompt = "给我推荐三款性价比高的耳机"
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150
    )
    print(resp.choices[0].message.content)