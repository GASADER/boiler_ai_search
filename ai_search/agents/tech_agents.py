# -*- coding: utf-8 -*-
from crewai import Agent, LLM
from tools.search_tools import web_search_tool

# กำหนด Ollama LLM
ollama_llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    api_key="ollama",
    temperature=0.2
)

# Agent 1: ค้นหาข้อมูล
researcher = Agent(
    role="Senior Tech Researcher",
    goal="Find detailed technical specifications and updates comparing Qwen 2.5 and Llama 3.",
    backstory="You are an expert technical researcher who excels at finding accurate technical benchmarks and capabilities.",
    tools=[web_search_tool],
    llm=ollama_llm,
)

# Agent 2: วิเคราะห์
analyst = Agent(
    role="AI Technical Analyst",
    goal="Analyze raw data to compare pros, cons, performance, and best use cases.",
    backstory="You are a clear-thinking systems analyst who turns raw search data into structured comparisons.",
    llm=ollama_llm,
)

# Agent 3: เรียบเรียงภาษาไทย
thai_writer = Agent(
    role="บรรณาธิการข่าวไอทีภาษาไทย",
    goal="แปลและเรียบเรียงเนื้อหาการเปรียบเทียบเป็นภาษาไทยที่อ่านง่ายและถูกต้อง",
    backstory=(
        "คุณเป็นบรรณาธิการข่าวไอทีมืออาชีพ "
        "คุณรับเนื้อหาภาษาอังกฤษมาแปลและเรียบเรียงเป็นภาษาไทยที่สละสลวย "
        "CRITICAL RULE: ตอบเป็นภาษาไทยเท่านั้น ห้ามมีภาษาจีนหลุดมาโดยเด็ดขาด"
    ),
    llm=ollama_llm,
)