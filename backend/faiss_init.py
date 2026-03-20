import json

import faiss
import numpy as np

# 读取商品示例数据
with open("backend/data/sample_products.json", "r") as f:
    products = json.load(f)

# 随机生成向量（模拟商品 embedding）
d = 128  # 向量维度
vectors = np.random.random((len(products), d)).astype("float32")

# 初始化 FAISS 索引
index = faiss.IndexFlatL2(d)
index.add(vectors)

# 保存索引
faiss.write_index(index, "backend/data/product_index.faiss")
print(f"FAISS index built with {len(products)} products.")