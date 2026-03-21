import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None


class ImageSearchAgent:
    """
    简单示例：将上传图片向量化，与商品向量比对
    """
    def __init__(self, product_embeddings, product_list):
        self.index = product_embeddings  # faiss IndexFlatL2
        self.products = product_list

    def search_by_image(self, img_path, topk=5):
        if not self.products:
            return []

        if self.index is None:
            return [product.copy() for product in self.products[:topk]]

        try:
            img_vec = self.image_to_vector(img_path, dim=getattr(self.index, "d", 512))
            if img_vec is None:
                return [product.copy() for product in self.products[:topk]]

            _, indices = self.index.search(np.array([img_vec], dtype="float32"), min(topk, len(self.products)))
            return [self.products[i].copy() for i in indices[0] if 0 <= i < len(self.products)]
        except Exception:
            return [product.copy() for product in self.products[:topk]]

    def image_to_vector(self, img_path, dim=512):
        if Image is None:
            return None

        img = Image.open(img_path).resize((224, 224)).convert("RGB")
        arr = np.array(img, dtype="float32").flatten()

        if arr.size < dim:
            arr = np.pad(arr, (0, dim - arr.size))
        else:
            arr = arr[:dim]

        norm = np.linalg.norm(arr)
        if norm == 0:
            return None

        return arr / norm
