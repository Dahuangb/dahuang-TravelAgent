# 平台信息增强功能说明

## 功能概述

`platform_info_tool.py` 用于通过Web搜索获取携程、马蜂窝、大众点评、小红书等平台的评价信息，以补充百度地图API返回的信息不足问题。

## 当前实现状态

目前工具框架已创建，但需要配置实际的Web搜索功能。有两种实现方式：

### 方式1：使用MCP（推荐）

如果您有配置携程、马蜂窝、大众点评、小红书等平台的MCP服务器，可以：

1. 在 `platform_info_tool.py` 中导入MCP工具
2. 替换 `_run` 方法中的搜索逻辑，直接调用MCP API

示例代码：
```python
# 假设有MCP工具可用
from mcp import ctrip_search, dianping_search, xiaohongshu_search

def _run(self, name: str, city: str, poi_type: str):
    # 调用MCP工具
    ctrip_info = ctrip_search(name, city)
    dianping_info = dianping_search(name, city)
    # ... 处理结果
```

### 方式2：使用Web搜索工具

如果您的环境中有 `web_search` 工具可用，可以：

1. 在 `platform_info_tool.py` 中取消注释相关代码
2. 确保 `web_search` 工具已正确配置

修改 `_run` 方法：
```python
# 取消注释这部分代码
for platform, query in queries.items():
    search_results = web_search(query)  # 调用web_search工具
    enhanced_info[platform] = self._parse_search_results(search_results, platform)
```

## 数据结构

工具返回的数据结构：
```python
{
    "携程": {
        "rating": 4.5,  # 评分
        "review_count": 1234,  # 评价数量
        "summary": "用户评价摘要...",  # 评价摘要
        "key_points": ["推荐", "必去"]  # 关键词
    },
    "马蜂窝": {...},
    "大众点评": {...},
    "小红书": {...},
    "enhanced_description": "综合描述...",
    "recommended_tags": ["标签1", "标签2"]
}
```

## 使用建议

1. **性能优化**：目前只为Top-3景点/餐厅获取平台信息，避免API调用过多
2. **容错处理**：如果平台信息获取失败，不影响主流程，会使用原有描述
3. **异步处理**：可以考虑将平台信息获取改为异步，提升响应速度

## 下一步改进

1. 配置实际的MCP服务器或Web搜索工具
2. 优化搜索结果解析逻辑
3. 添加缓存机制，避免重复搜索
4. 支持更多平台（如去哪儿、途牛等）









