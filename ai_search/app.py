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
st.caption(
    "กำหนด Agents, Shortcuts พร้อมระบบ Manager Control Flow สำหรับคำถามเพิ่มเติม"
)

# ==================== SHORTCUTS DICTIONARY ====================
SHORTCUT_DATA = {
    "Format": {
        "/ELI5": "อธิบายเรื่องซับซ้อนให้เข้าใจง่ายเหมือนอธิบายเด็ก 5 ขวบ",
        "/TLDR": "สรุปเนื้อหายาวให้เหลือประเด็นสำคัญสั้นๆ ไม่กี่บรรทัด",
        "/JSON Only": "ให้ออกผลลัพธ์เป็นโครงสร้าง JSON เท่านั้น ห้ามมีข้อความอื่น",
        "/Table Only": "จัดกลุ่มคำตอบเป็นตาราง Markdown เท่านั้น ห้ามมีเนื้อหาบรรยาย",
        "/Bullets Only": "ตอบเป็นรายการข้อๆ เว้นคำเกริ่นและบทสรุป",
        "/CHECKLIST": "เปลี่ยนคำตอบให้อยู่ในรูปแบบรายการสิ่งที่ต้องทำ (Checklist)",
        "/BRIEFLY": "บังคับให้ตอบแบบสั้น กระชับ รวบรัดที่สุด",
        "/SCHEMA": "สร้างโครงสร้างหัวข้อ หรือแบบจำลองข้อมูล (Data Model)",
    },
    "Reasoning": {
        "/CoT": "Chain of Thought - คิดและแสดงขั้นตอนอย่างเป็นลำดับก่อนให้คำตอบ",
        "/ToT": "Tree of Thoughts - จำลองทางเลือกความคิดหลายทาง ประเมินข้อดีข้อเสีย",
        "/ReAct": "Reason + Action - แสดงกระบวนการคิด การกระทำ และสังเกตผลทีละสเต็ป",
        "/DELIBERATE THINKING": "ใช้กระบวนการคิดวิเคราะห์อย่างละเอียดและรอบคอบมากขึ้น",
        "/FIRST PRINCIPLES": "รื้อถอนและวิเคราะห์ปัญหาจากหลักการพื้นฐานที่แท้จริง",
    },
    "Guardrail": {
        "/No Yapping": "ตอบเฉพาะเนื้อหาเน้นๆ ห้ามทักทาย เกริ่นนำ หรือสรุปเยิ่นเย้อ",
        "/Context-Only": "ตอบจากข้อมูลที่ป้อนให้เท่านั้น ห้ามใช้ความรู้ภายนอก",
        "/Fact-Check": "ตรวจสอบความถูกต้องของข้อมูลพร้อมระบุแหล่งอ้างอิง",
        "/Devil's Advocate": "สวมบทบาทเป็นฝ่ายคัดค้าน เพื่อหาข้อบกพร่องหรือจุดอ่อน",
        "/EVAL-SELF": "ให้ AI ประเมินและวิจารณ์จุดอ่อนในคำตอบของตัวเองอย่างตรงไปตรงมา",
    },
    "Analysis & Content": {
        "/SWOT": "วิเคราะห์ จุดแข็ง จุดอ่อน โอกาส และอุปสรรค",
        "/EXEC SUMMARY": "สรุปภาพรวมสำหรับผู้บริหารแบบสั้นและเห็นประเด็นสำคัญชัดเจน",
        "/COMPARE": "นำสิ่งของหรือแนวคิดตั้งแต่ 2 สิ่งขึ้นไปมาเปรียบเทียบกันข้างๆ",
        "/MULTI-PERSPECTIVE": "แสดงความคิดเห็นและวิเคราะห์จากหลากหลายมุมมอง",
    },
}

ALL_SHORTCUT_OPTIONS = []
for cat, shortcuts in SHORTCUT_DATA.items():
    for sc, desc in shortcuts.items():
        ALL_SHORTCUT_OPTIONS.append(f"{sc} - {desc}")

# ==================== SESSION STATE INIT ====================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_context" not in st.session_state:
    st.session_state.last_context = ""

# ==================== SIDEBAR: LLM CONFIG ====================
st.sidebar.header("⚙️ LLM Configuration")
model_name = st.sidebar.text_input("Ollama Model", value="ollama/qwen2.5:7b")
base_url = st.sidebar.text_input("Base URL", value="http://localhost:11434")
temperature = st.sidebar.slider(
    "Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1
)


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
            "shortcuts": [
                "/Fact-Check - ตรวจสอบความถูกต้องของข้อมูลพร้อมระบุแหล่งอ้างอิง"
            ],
            "task_desc": "Search for the latest benchmarks, features, or updates regarding '{topic}'.",
            "expected_output": "A summary of raw facts, benchmarks, and key points in English.",
        },
        {
            "role": "บรรณาธิการข่าวไอทีภาษาไทย",
            "goal": "แปลและเรียบเรียงเนื้อหาการเปรียบเทียบหรือข่าวสารเป็นภาษาไทยที่อ่านง่ายและถูกต้อง",
            "backstory": "คุณเป็นบรรณาธิการข่าวไอทีมืออาชีพ คุณรับเนื้อหามาแปลและเรียบเรียงเป็นภาษาไทยที่สละสลวย",
            "use_tools": False,
            "shortcuts": [
                "/ELI5 - อธิบายเรื่องซับซ้อนให้เข้าใจง่ายเหมือนอธิบายเด็ก 5 ขวบ"
            ],
            "task_desc": "นำข้อมูลเกี่ยวกับ {topic} ทั้งหมดมาแปลและเรียบเรียงสรุปเป็นภาษาไทย จัดรูปแบบด้วย Markdown ให้น่าอ่าน",
            "expected_output": "บทความสรุปภาษาไทยล้วนอย่างสละสลวย",
        },
    ]

st.subheader("👥 จัดการคณะทำงานหลัก (Main Crew Agents)")

col_add, _ = st.columns([1, 4])
with col_add:
    if st.button("➕ เพิ่ม Agent ใหม่"):
        st.session_state.custom_agents.append(
            {
                "role": f"Custom Agent {len(st.session_state.custom_agents) + 1}",
                "goal": "",
                "backstory": "",
                "use_tools": False,
                "shortcuts": [],
                "task_desc": "ประมวลผลข้อมูลในส่วนที่เกี่ยวข้องกับ {topic}",
                "expected_output": "สรุปผลลัพธ์การประมวลผล",
            }
        )
        st.rerun()

for idx, agent_data in enumerate(st.session_state.custom_agents):
    with st.expander(f"📌 Agent {idx + 1}: {agent_data['role']}", expanded=True):
        col_role, col_tool, col_del = st.columns([3, 1, 1])

        with col_role:
            agent_data["role"] = st.text_input(
                f"Role/ตำแหน่ง", value=agent_data["role"], key=f"role_{idx}"
            )
        with col_tool:
            agent_data["use_tools"] = st.checkbox(
                "ใช้ Search Tool", value=agent_data["use_tools"], key=f"tool_{idx}"
            )
        with col_del:
            st.write("")
            if len(st.session_state.custom_agents) > 1 and st.button(
                "🗑️ ลบ", key=f"del_{idx}"
            ):
                st.session_state.custom_agents.pop(idx)
                st.rerun()

        agent_data["goal"] = st.text_area(
            "Goal (เป้าหมาย)", value=agent_data["goal"], key=f"goal_{idx}", height=68
        )
        agent_data["backstory"] = st.text_area(
            "Backstory (ปูพื้นหลัง)",
            value=agent_data["backstory"],
            key=f"backstory_{idx}",
            height=68,
        )

        agent_data["shortcuts"] = st.multiselect(
            "⚡ Select Prompt Shortcuts สำหรับ Agent นี้:",
            options=ALL_SHORTCUT_OPTIONS,
            default=agent_data.get("shortcuts", []),
            key=f"shortcuts_{idx}",
        )

        st.markdown("**📋 ภารกิจที่มอบหมาย (Task)**")
        agent_data["task_desc"] = st.text_area(
            "Task Description (ใช้ {topic} เป็นตัวแปรแทนหัวข้อได้)",
            value=agent_data["task_desc"],
            key=f"task_{idx}",
            height=68,
        )
        agent_data["expected_output"] = st.text_input(
            "Expected Output (ผลลัพธ์ที่คาดหวัง)",
            value=agent_data["expected_output"],
            key=f"out_{idx}",
        )

st.divider()

# ==================== USER INPUT & MAIN CREW EXECUTION ====================
st.subheader("📌 ตั้งโจทย์การทำงาน")

topic_input = st.text_input(
    "หัวข้อที่ต้องการค้นหาและสรุป ({topic}):",
    value="Qwen 2.5 vs Llama 3",
    placeholder="เช่น Claude 3.5 Sonnet vs GPT-4o...",
)

col_run, col_clear = st.columns([1, 4])
with col_run:
    run_button = st.button("🚀 เริ่มทำงาน (Run Crew)", type="primary")
with col_clear:
    if st.button("🧹 ล้างประวัติการสนทนา"):
        st.session_state.chat_history = []
        st.session_state.last_context = ""
        st.rerun()

if run_button:
    if not topic_input.strip():
        st.warning("กรุณากรอกหัวข้อก่อนเริ่มทำงานครับ")
    elif len(st.session_state.custom_agents) == 0:
        st.warning("กรุณาเพิ่มอย่างน้อย 1 Agent ก่อนเริ่มทำงานครับ")
    else:
        st.info(f"🔎 กำลังประมวลผลหัวข้อ: **{topic_input}**")

        crew_agents = []
        crew_tasks = []

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

            selected_codes = [
                sc.split(" - ")[0] for sc in agent_cfg.get("shortcuts", [])
            ]
            shortcut_str = " " + " ".join(selected_codes) if selected_codes else ""
            formatted_task_desc = (
                agent_cfg["task_desc"].replace("{topic}", topic_input) + shortcut_str
            )

            task_instance = Task(
                description=formatted_task_desc,
                expected_output=agent_cfg["expected_output"],
                agent=agent_instance,
            )
            crew_tasks.append(task_instance)

        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=Process.sequential,
            verbose=True,
        )

        with st.spinner("🤖 คณะ Agent กำลังทำงานร่วมกันตามลำดับ..."):
            try:
                result = str(crew.kickoff())
                st.session_state.last_context = result
                st.session_state.chat_history = [
                    {"role": "assistant", "content": result}
                ]
                st.success("✅ ประมวลผลเสร็จสิ้น!")

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการทำงาน: {str(e)}")

# ==================== FOLLOW-UP CHAT WITH MANAGER CONTROL ====================
if st.session_state.chat_history:
    st.divider()
    st.subheader("💬 สนทนา/ถามคำถามเพิ่มเติม (Follow-up Chat)")

    # แสดงประวัติการสนทนา
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if follow_up_input := st.chat_input("พิมพ์คำถามเพิ่มเติมตรงนี้..."):
        st.session_state.chat_history.append(
            {"role": "user", "content": follow_up_input}
        )
        with st.chat_message("user"):
            st.markdown(follow_up_input)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Manager Agent กำลังประเมิน Workflow..."):

                # ---------------- 1. MANAGER / CONTROLLER AGENT ----------------
                manager_agent = Agent(
                    role="Workflow Orchestrator",
                    goal="Analyze user request and decide whether external web search is needed or context is sufficient.",
                    backstory="You are a senior system controller. You evaluate user intent and delegate tasks appropriately.",
                    llm=ollama_llm,
                    verbose=True,
                )

                decision_task = Task(
                    description=(
                        f"คำถามของผู้ใช้: '{follow_up_input}'\n"
                        f"บริบทที่มีอยู่เดิม:\n{st.session_state.last_context[-1500:]}\n\n"
                        "วิเคราะห์ว่าคำถามนี้จำเป็นต้องค้นหาข้อมูลใหม่จากอินเทอร์เน็ตหรือไม่?\n"
                        "ตอบเพียงแค่ 'SEARCH_REQUIRED' หากเป็นข้อมูลใหม่/ข่าวสารที่ไม่มีในบริบท\n"
                        "หรือตอบ 'USE_CONTEXT' หากสามารถใช้ข้อมูลที่มีอยู่ตอบได้"
                    ),
                    expected_output="SEARCH_REQUIRED หรือ USE_CONTEXT เท่านั้น",
                    agent=manager_agent,
                )

                manager_crew = Crew(
                    agents=[manager_agent], tasks=[decision_task], verbose=True
                )
                decision = str(manager_crew.kickoff()).strip().upper()

                # ---------------- 2. SPECIALIZED FOLLOW-UP AGENT ----------------
                followup_agent = Agent(
                    role="Interactive Follow-up Specialist",
                    goal="Answer user follow-up questions accurately, clearly, and concisely in Thai.",
                    backstory="คุณคือผู้เชี่ยวชาญด้านการตอบคำถามซักถามเพิ่มเติม คุณเน้นการตอบตรงประเด็น เรียบเรียงสละสลวย และอ้างอิงข้อมูลที่ถูกต้อง",
                    llm=ollama_llm,
                    verbose=True,
                )

                tasks_for_response = []
                agents_for_response = []

                if "SEARCH_REQUIRED" in decision:
                    st.toast(
                        "🔍 Manager ตัดสินใจ: ต้องค้นหาข้อมูลเพิ่มเติม...", icon="ℹ️"
                    )

                    search_agent = Agent(
                        role="Search Specialist",
                        goal="Search for new specific information to answer the user's question.",
                        backstory="You search for precise and updated factual details.",
                        tools=[web_search_tool],
                        llm=ollama_llm,
                        verbose=True,
                    )

                    search_task = Task(
                        description=f"Search internet for information regarding: '{follow_up_input}'",
                        expected_output="Relevant snippets and facts found from web search.",
                        agent=search_agent,
                    )

                    answer_task = Task(
                        description=(
                            f"นำข้อมูลที่ค้นหาได้ใหม่มารวมกับบริบทเดิมเพื่อตอบคำถาม: '{follow_up_input}'\n"
                            "ตอบเป็นภาษาไทยให้อ่านง่าย สรุปตรงประเด็น"
                        ),
                        expected_output="คำตอบภาษาไทยที่ครอบคลุมข้อมูลใหม่",
                        agent=followup_agent,
                    )

                    agents_for_response = [search_agent, followup_agent]
                    tasks_for_response = [search_task, answer_task]

                else:
                    st.toast(
                        "⚡ Manager ตัดสินใจ: ตอบจากบริบทเดิมได้ทันที...", icon="⚡"
                    )

                    answer_task = Task(
                        description=(
                            f"บริบทที่มีอยู่:\n{st.session_state.last_context}\n\n"
                            f"คำถามเพิ่มเติม: '{follow_up_input}'\n\n"
                            "ตอบคำถามเพิ่มเติมข้างต้นโดยอ้างอิงจากบริบทที่มีอยู่อย่างเคร่งครัด ตอบเป็นภาษาไทย"
                        ),
                        expected_output="คำตอบภาษาไทยที่ชัดเจน ตรงประเด็น",
                        agent=followup_agent,
                    )

                    agents_for_response = [followup_agent]
                    tasks_for_response = [answer_task]

                # ---------------- 3. EXECUTE FOLLOW-UP CREW ----------------
                execution_crew = Crew(
                    agents=agents_for_response,
                    tasks=tasks_for_response,
                    process=Process.sequential,
                    verbose=True,
                )

                final_reply = str(execution_crew.kickoff())
                st.markdown(final_reply)

                st.session_state.chat_history.append(
                    {"role": "assistant", "content": final_reply}
                )
                st.session_state.last_context += (
                    f"\n\nQ: {follow_up_input}\nA: {final_reply}"
                )
