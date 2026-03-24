from ...agents.image_search_agent import ImageSearchAgent


def create_image_search_agent(product_embeddings, product_list):
    return ImageSearchAgent(product_embeddings, product_list)


def search_products_by_image(image_agent, image_path: str, topk: int = 5):
    return image_agent.search_by_image(image_path, topk=topk)
