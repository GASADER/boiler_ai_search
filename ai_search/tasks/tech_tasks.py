# -*- coding: utf-8 -*-
from crewai import Task
from agents.tech_agents import researcher, analyst, thai_writer

task_research = Task(
    description="Search for the latest benchmark and features comparing 'Qwen 2.5 vs Llama 3'.",
    expected_output="A bulleted list of raw facts, benchmarks, and architectural differences in English.",
    agent=researcher
)

task_analysis = Task(
    description="Based on the research findings, create a structured Pros and Cons comparison between Qwen 2.5 and Llama 3.",
    expected_output="A structured breakdown of Pros, Cons, and Key Differences in English.",
    agent=analyst
)

task_translate_and_format = Task(
    description="แปลบทวิเคราะห์เปรียบเทียบ Qwen 2.5 vs Llama 3 ทั้งหมดเป็นภาษาไทย และจัดฟอร์แมตให้น่าอ่าน",
    expected_output="บทความเปรียบเทียบข้อดีข้อเสียเป็นภาษาไทยล้วนอย่างสละสลวย",
    agent=thai_writer
)