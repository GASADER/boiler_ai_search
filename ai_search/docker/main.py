import os
import socket
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from duckduckgo_search import DDGS

def get_ollama_base_url():
    """เช็กอัตโนมัติว่ารันอยู่ใน Docker หรือบนเครื่อง Mac"""
    # 1. เช็กว่ามีการส่ง Environment Variable มาหรือไม่
    env_url = os.getenv("OLLAMA_BASE_URL")
    if env_url:
        return env_url
    
    # 2. ลองทดสอบว่า host.docker.internal มีตัวตนอยู่ไหม (ถ้ารันใน Docker จะเจอ)
    try:
        socket.gethostbyname("host.docker.internal")
        return "http://host.docker.internal:11434"
    except socket.gaierror:
        # ถ้ารันบนเครื่อง Mac โดยตรง จะตกมาที่นี่ ให้ใช้ localhost
        return "http://localhost:11434"

# ดึง URL อัตโนมัติ
OLLAMA_URL = get_ollama_base_url()
print(f" Connecting to Ollama at: {OLLAMA_URL}")

# สร้าง LLM Object
ollama_llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url=OLLAMA_URL,
    api_key="ollama"  # ใส่เพื่อป้องกันไม่ให้ CrewAI วิ่งไปหา OpenAI
)

@tool("DuckDuckGo Search")
def web_search_tool(query: str) -> str:
    """ค้นหาข้อมูลจากอินเทอร์เน็ต"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(keywords=query, backend="lite", max_results=5))
        if not results:
            return "ไม่พบข้อมูล"
        return "\n---\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
    except Exception as e:
        return f"Search Error: {str(e)}"

# สร้าง Agent
researcher = Agent(
    role="Sandboxed Researcher",
    goal="ค้นหาข้อมูลเทคโนโลยีล่าสุดและเซฟสรุปลงในโฟลเดอร์ที่ได้รับอนุญาต",
    backstory="คุณเป็นนักวิจัยที่ทำงานรวดเร็วและแม่นยำ",
    tools=[web_search_tool],
    verbose=True,
    llm=ollama_llm
)

task = Task(
    description="ค้นหาข่าวสั้นๆ เกี่ยวกับ 'Docker container for AI' และสรุปเป็นภาษาไทย 3 ข้อ",
    expected_output="สรุปภาษาไทย 3 ข้อ",
    agent=researcher
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    process=Process.sequential
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n=== FINAL RESULT ===")
    print(result)