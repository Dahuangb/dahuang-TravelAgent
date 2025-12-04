# chains/recommend_chain.py
from typing import List, Set
from models.trip_schema import Attraction   # 确保路径与你项目一致

def reorder_after_feedback(items: List[Attraction],
                           likes: Set[str],
                           bans: Set[str]) -> List[Attraction]:
    """
    1. 过滤 bans
    2. likes 内的项目按原始顺序提到最前
    3. 返回新列表
    """
    # 空集保护
    if likes is None:
        likes = set()
    if bans is None:
        bans = set()

    # 1. 先踢掉被删除的
    filtered = [item for item in items if item.id not in bans]

    # 2. 把 likes 提到最前，且保持它们在原始列表里的相对顺序
    liked_items   = [item for item in filtered if item.id in likes]
    unliked_items = [item for item in filtered if item.id not in likes]

    return liked_items + unliked_items