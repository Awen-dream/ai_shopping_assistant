from PIL import Image
import numpy as np

class ImageSearchAgent:
    """
    简单示例：将上传图片向量化，与商品向量比对
    """
    def __init__(self, product_embeddings, product_list):
        self.index = product_embeddings  # faiss IndexFlatL2
        self.products = product_list

    def search_by_image(self, img_path, topk=5):
        img_vec = self.image_to_vector(img_path)
        D, I = self.index.search(np.array([img_vec]), topk)
        return [self.products[i] for i in I[0]]

    def image_to_vector(self, img_path):
        # 简化示例，实际可使用 CLIP / OpenCLIP
        img = Image.open(img_path).resize((224,224)).convert("RGB")
        arr = np.array(img).flatten()[:512]  # 简化成512维
        return arr / np.linalg.norm(arr)