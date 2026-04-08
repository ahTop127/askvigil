import asyncio
import os
import sys
from tortoise import Tortoise
from dotenv import load_dotenv

# 1. 路径和环境变量配置 (和你之前的导入脚本一样)
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.append(project_root)

app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)
if os.path.exists(env_path):
    load_dotenv(env_path)

from app.core.database import TORTOISE_ORM
from app.models.open_data import OpenDataSet

# 2. 引入 AI 模型
from sentence_transformers import SentenceTransformer


async def generate_and_update_embeddings():
    print("正在加载 AI 嵌入模型 (首次运行会自动下载模型权重，请耐心等待)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("连接数据库...")
    await Tortoise.init(config=TORTOISE_ORM)

    # 3. 找出所有还没有生成向量的数据 (对于 6 万条数据，我们分批处理，防内存爆炸)
    batch_size = 1000
    offset = 0

    # 获取总数
    total_count = await OpenDataSet.filter(text_embedding__isnull=True).count()
    print(f"发现 {total_count} 条数据需要生成向量。")

    while True:
        # 获取一批数据
        records = (
            await OpenDataSet.filter(text_embedding__isnull=True)
            .limit(batch_size)
            .offset(0)
        )

        if not records:
            break

        print(f"正在处理接下来 {len(records)} 条数据...")

        # 提取需要向量化的文本 (如果你有处理为空的情况，可以加个判断)
        texts = [record.clean_text if record.clean_text else "" for record in records]

        # 4. 魔法发生的地方：批量将文本转为向量！
        embeddings = model.encode(texts)

        # 5. 更新回数据库
        for idx, record in enumerate(records):
            record.text_embedding = embeddings[idx].tolist()

        # 批量保存
        await OpenDataSet.bulk_update(
            records, fields=["text_embedding"], batch_size=500
        )

        offset += len(records)
        print(f"进度: {offset} / {total_count}")

    print("所有向量生成完毕！你的数据库现在拥有了 AI 检索的能力！")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(generate_and_update_embeddings())
