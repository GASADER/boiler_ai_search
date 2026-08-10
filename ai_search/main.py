# -*- coding: utf-8 -*-
from crewai import Crew, Process
from config.telemetry import init_telemetry
from agents.tech_agents import researcher, analyst, thai_writer
from tasks.tech_tasks import task_research, task_analysis, task_translate_and_format

def main():
    # 1. เปิดระบบ Tracking (Phoenix UI)
    init_telemetry()

    # 2. ตั้งคณะทำงาน Crew
    crew = Crew(
        agents=[researcher, analyst, thai_writer],
        tasks=[task_research, task_analysis],
        process=Process.sequential,
        verbose=True
    )

    print("\n=== STARTING MULTI-AGENT EXECUTION ===\n")
    result = crew.kickoff()
    print("\n=== FINAL OUTPUT ===\n")
    print(result)

if __name__ == "__main__":
    main()