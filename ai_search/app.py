# -*- coding: utf-8 -*-
import streamlit as st
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from ddgs import DDGS

# ==================== STREAMLIT UI CONFIG ====================
st.set_page_config(
    page_title="Dynamic CrewAI Research Assistant", page_icon="🤖", layout="wide"
)

st.title("🤖 Dynamic CrewAI Builder & Assistant")
st.caption("กำหนด Agent, LLM Config และสร้างระบบ Multi-Agent แบบกำหนดเองได้ผ่านหน้าเว็บ")

# ==================== SIDEBAR: LLM CONFIG ====================
st.sidebar.header("⚙️ LLM Configuration")
model_name = st.sidebar.text_input("Ollama Model", value="ollama/qwen2.5:7b")
base_url = st.sidebar.text_input("Base URL", value="http://localhost:11434")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)

@st.cache_resource
def get_llm(model: str, url: str, temp: float):
    return LLM(
        model=model,
        base_url=url,
        api_key="ollama",
        temperature=temp,
    )

ollama_llm = get_llm(model_name, base_url, temperature)

# ==================== TOOLS ====================
@tool("DuckDuckGo Search")
def web_search_tool(query: str) -> str:
    """Search information from the internet using English keywords."""
    try:
        results = list(DDGS().text(query=query, max_results=5))
        if not results:
            return "No results found."
        return "\n---\n".join(
            [f"Title: {r['title']}\nSnippet: {r['body']}" for r in results]
        )
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== DYNAMIC AGENTS MANAGEMENT ====================
if "custom_agents" not in st.session_state:
    st.session_state.custom_agents = [
        {
            "role": "Senior Tech Researcher",
            "goal": "Find detailed technical specifications and news about the given topic.",
            "backstory": "You are an expert technical researcher who excels at finding accurate news and benchmarks.",
            "use_tools": True,
            "task_desc": "Search for the latest benchmarks, features, or updates regarding '{topic}'.",
            "expected_output": "A summary of raw facts, benchmarks, and key points in English.",
        }
    ]

# ปุ่มสำหรับเพิ่ม Agent ใหม่
st.subheader("👥 จัดการคณะทำงาน (Agents Configuration)")

col_add, _ = st.columns([1, 4])
with col_add:
    if st.button("➕ เพิ่ม Agent ใหม่"):
        st.session_state.custom_agents.append({
            "role": f"Custom Agent {len(st.session_state.custom_agents) + 1}",
            "goal": "",
            "backstory": "",
            "use_tools": False,
            "task_desc": "ประมวลผลข้อมูลในส่วนที่เกี่ยวข้องกับ {{topic}}",
            "expected_output": "สรุปผลลัพธ์การประมวลผล",
        })
        st.rerun()

# แสดง Form แก้ไขรายละเอียดของแต่ละ Agent
for idx, agent_data in enumerate(st.session_state.custom_agents):
    with st.expander(f"📌 Agent {idx + 1}: {agent_data['role']}", expanded=True):
        col_role, col_tool, col_del = st.columns([3, 1, 1])
        
        with col_role:
            agent_data["role"] = st.text_input(f"Role/ตำแหน่ง", value=agent_data["role"], key=f"role_{idx}")
        with col_tool:
            agent_data["use_tools"] = st.checkbox("ใช้ Search Tool", value=agent_data["use_tools"], key=f"tool_{idx}")
        with col_del:
            st.write("") # จัดระยะแนวตั้ง
            if len(st.session_state.custom_agents) > 1 and st.button("🗑️ ลบ", key=f"del_{idx}"):
                st.session_state.custom_agents.pop(idx)
                st.rerun()

        agent_data["goal"] = st.text_area("Goal (เป้าหมาย)", value=agent_data["goal"], key=f"goal_{idx}", height=68)
        agent_data["backstory"] = st.text_area("Backstory (ปูพื้นหลัง)", value=agent_data["backstory"], key=f"backstory_{idx}", height=68)
        
        st.markdown("**📋 ภารกิจที่มอบหมาย (Task)**")
        agent_data["task_desc"] = st.text_area("Task Description (ใช้ {topic} เป็นตัวแปรแทนหัวข้อได้)", value=agent_data["task_desc"], key=f"task_{idx}", height=68)
        agent_data["expected_output"] = st.text_input("Expected Output (ผลลัพธ์ที่คาดหวัง)", value=agent_data["expected_output"], key=f"out_{idx}")

st.divider()

# ==================== USER INPUT & EXECUTION ====================
st.subheader("📌 ตั้งโจทย์การทำงาน")

topic_input = st.text_input(
    "หัวข้อที่ต้องการค้นหาและสรุป ({topic}):",
    value="Qwen 2.5 vs Llama 3",
    placeholder="เช่น Claude 3.5 Sonnet vs GPT-4o...",
)

if st.button("🚀 เริ่มทำงาน (Run Crew)", type="primary"):
    if not topic_input.strip():
        st.warning("กรุณากรอกหัวข้อก่อนเริ่มทำงานครับ")
    elif len(st.session_state.custom_agents) == 0:
        st.warning("กรุณาเพิ่มอย่างน้อย 1 Agent ก่อนเริ่มทำงานครับ")
    else:
        st.info(f"🔎 กำลังประมวลผลหัวข้อ: **{topic_input}** ด้วย {len(st.session_state.custom_agents)} Agents")

        crew_agents = []
        crew_tasks = []

        # สร้าง Agents และ Tasks แบบ Dynamic จาก Config บนหน้าเว็บ
        for agent_cfg in st.session_state.custom_agents:
            agent_instance = Agent(
                role=agent_cfg["role"],
                goal=agent_cfg["goal"],
                backstory=agent_cfg["backstory"],
                tools=[web_search_tool] if agent_cfg["use_tools"] else [],
                llm=ollama_llm,
                verbose=True,
            )
            crew_agents.append(agent_instance)

            # แทนค่า {topic} ลงใน Task Description
            formatted_task_desc = agent_cfg["task_desc"].replace("{topic}", topic_input)

            task_instance = Task(
                description=formatted_task_desc,
                expected_output=agent_cfg["expected_output"],
                agent=agent_instance,
            )
            crew_tasks.append(task_instance)

        # รวม Crew
        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=Process.sequential,
            verbose=True,
        )

        # แสดง Spinner ระหว่างรัน
        with st.spinner("🤖 คณะ Agent กำลังทำงานร่วมกันตามลำดับ..."):
            try:
                result = crew.kickoff()

                # แสดงผลลัพธ์
                st.success("✅ ประมวลผลเสร็จสิ้น!")
                st.markdown("### 📄 ผลลัพธ์จาก CrewAI")
                st.markdown(result)

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการทำงาน: {str(e)}")