import pandas as pd
from pathlib import Path

# 1. 动态获取项目根目录 (backend 目录)
# __file__ 指代当前脚本 sample_data.py 的位置
# .parent 退回一层到 scripts/
# .parent 再退回一层到 app/
# .parent 再退回一层到 backend/
base_dir = Path(__file__).resolve().parent.parent

# 2. 拼接出输入和输出的绝对路径
input_file = base_dir / "resources" / "ready_for_db.csv"
output_file = base_dir / "resources" / "ready_for_db_small.csv"

print(f"正在读取文件: {input_file}")

# 3. 读取原始 CSV 文件
df = pd.read_csv(input_file)

# 4. 随机抽取 1000 条数据 (random_state=42 保证每次运行抽取的都是同一批)
df_small = df.sample(n=1000, random_state=42)

# 5. 保存为新的 CSV 文件
df_small.to_csv(output_file, index=False)

print(f"抽取完成！小文件已保存至: {output_file}")
