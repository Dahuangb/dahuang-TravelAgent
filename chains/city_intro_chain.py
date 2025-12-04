from langchain_openai import ChatOpenAI
from langchain_classic.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位资深的旅游文化专家，擅长用简洁优美的语言介绍城市。"),
    ("user", """请为城市"{city}"写一段简介，要求：
1. 介绍地理位置（所在省份、地理位置特点）
2. 介绍文化底蕴（历史背景、文化特色）
3. 介绍著名景点（2-3个最具代表性的景点）
4. 介绍代表性美食（2-3种特色美食）

要求：总字数不超过200字，语言简洁优美，突出城市特色。直接输出简介内容，不要添加任何前缀或格式说明。"""),
])

llm = ChatOpenAI(
    temperature=0.7,  # 稍微提高温度以获得更生动的描述
    model="deepseek-chat",
    api_key='sk-50a7224452114cac95ff0998ea6dbc15',
    base_url='https://api.deepseek.com'
)

city_intro_chain = prompt | llm

def get_city_introduction(city: str) -> str:
    """获取城市简介"""
    try:
        result = city_intro_chain.invoke({"city": city})
        # 提取内容（去除可能的格式标记）
        content = result.content.strip()
        # 如果内容超过200字，截取前200字
        if len(content) > 200:
            content = content[:200] + "..."
        return content
    except Exception as e:
        return f"无法生成城市简介：{str(e)}"



