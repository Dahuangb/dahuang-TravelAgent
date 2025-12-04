from langchain_openai import ChatOpenAI
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class SelectedAttraction(BaseModel):
    name: str = Field(description="景点名称")
    reason: str = Field(description="选择理由")

class SelectedRestaurant(BaseModel):
    name: str = Field(description="餐厅名称")
    meal_type: str = Field(description="用餐类型：午餐或晚餐")
    reason: str = Field(description="选择理由")

class DayPlanSelection(BaseModel):
    morning_attraction: SelectedAttraction = Field(description="上午景点")
    lunch: SelectedRestaurant = Field(description="午餐餐厅")
    afternoon_attraction: SelectedAttraction = Field(description="下午景点")
    dinner: SelectedRestaurant = Field(description="晚餐餐厅")
    overall_reason: str = Field(description="整体行程安排理由")

parser = PydanticOutputParser(pydantic_object=DayPlanSelection)

def create_day_plan_prompt(day: int, destination: str, personal_requirements: str, 
                          avail_attractions: List[dict], avail_restaurants: List[dict],
                          hotel_name: str, adults: int, children: int):
    """创建每日行程规划的提示词"""
    
    # 格式化景点列表
    attractions_text = "\n".join([
        f"- {attr['name']} (评分: {attr.get('评分', 'N/A')}, 门票: {attr.get('门票', '免费')}, 距离: {attr.get('距离(米)', 0)}米)"
        for attr in avail_attractions[:15]  # 限制数量避免token过多
    ])
    
    # 格式化餐厅列表
    restaurants_text = "\n".join([
        f"- {rest['name']} (评分: {rest.get('评分', 'N/A')}, 人均: {rest.get('人均(元)', 'N/A')}, 菜系: {rest.get('菜系/标签', 'N/A')}, 距离: {rest.get('距离(米)', 0)}米)"
        for rest in avail_restaurants[:15]  # 限制数量避免token过多
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是资深旅行规划师，擅长根据用户需求、景点特色、餐厅口碑、距离等因素，为游客规划合理的每日行程。

请从提供的景点和餐厅列表中，为第{day}天的行程选择：
1. 一个上午景点（适合上午游览）
2. 一个午餐餐厅（12:00左右用餐）
3. 一个下午景点（适合下午游览）
4. 一个晚餐餐厅（18:00左右用餐）

选择原则：
- 考虑景点类型和游览时间（上午/下午）
- 考虑餐厅位置与景点的距离，避免来回奔波
- 考虑用户个性化需求
- 考虑评分和口碑
- 考虑价格合理性
- 确保行程流畅，不走回头路

请为每个选择提供理由，并给出整体行程安排的理由。"""),
        ("user", """目的地：{destination}
第{day}天行程规划

个性化需求：{personal_requirements}
入住酒店：{hotel_name}
人数：{adults}成人 {children}儿童

可选景点列表：
{attractions_text}

可选餐厅列表：
{restaurants_text}

请严格按以下格式返回：{format_instructions}""")
    ])
    
    return prompt

llm = ChatOpenAI(
    temperature=0.7,  # 稍微提高温度以获得更多创意
    model="deepseek-chat",
    api_key='sk-50a7224452114cac95ff0998ea6dbc15',
    base_url='https://api.deepseek.com'
)

def plan_day_with_llm(day: int, destination: str, personal_requirements: str,
                     avail_attractions: List[dict], avail_restaurants: List[dict],
                     hotel_name: str, adults: int, children: int):
    """使用大模型规划一天的行程"""
    
    prompt = create_day_plan_prompt(day, destination, personal_requirements,
                                   avail_attractions, avail_restaurants,
                                   hotel_name, adults, children)
    
    chain = prompt | llm | parser
    
    result = chain.invoke({
        "day": day,
        "destination": destination,
        "personal_requirements": personal_requirements or "无特殊要求",
        "attractions_text": "\n".join([
            f"- {attr['name']} (评分: {attr.get('评分', 'N/A')}, 门票: {attr.get('门票', '免费')}, 距离: {attr.get('距离(米)', 0)}米)"
            for attr in avail_attractions[:15]
        ]),
        "restaurants_text": "\n".join([
            f"- {rest['name']} (评分: {rest.get('评分', 'N/A')}, 人均: {rest.get('人均(元)', 'N/A')}, 菜系: {rest.get('菜系/标签', 'N/A')}, 距离: {rest.get('距离(米)', 0)}米)"
            for rest in avail_restaurants[:15]
        ]),
        "hotel_name": hotel_name,
        "adults": adults,
        "children": children,
        "format_instructions": parser.get_format_instructions()
    })
    
    return result









