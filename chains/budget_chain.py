from langchain_openai import ChatOpenAI          # 新路径
from langchain_classic.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class BudgetPlan(BaseModel):
    accommodation: int = Field(description="住宿费用（元）")
    restaurant:    int = Field(description="餐饮费用（元）")
    transport:     int = Field(description="市内交通费用（元）")
    attraction:    int = Field(description="门票费用（元）")
    contingency: int = Field(description="备用金（元）")
    reason: str = Field(description="一句话理由")

parser = PydanticOutputParser(pydantic_object=BudgetPlan)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是资深旅行规划师，根据城市、人数、天数、总预算，给出合理分配并一句话解释。"),
    ("user", """出发地：{departure}，目的地：{destination}，成人{adults} 儿童{children}，{start_date} 至 {end_date}，总预算 {budget} 元。请严格按以下格式返回：{format_instructions}"""),
])

llm = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",
    api_key='sk-50a7224452114cac95ff0998ea6dbc15',
    base_url='https://api.deepseek.com'
)

budget_chain = prompt | llm | parser