"""
core/agent.py — JavisAgent v2
- CLI mode: run(task) → plain string response from Local LLM
- Web mode: run(task) → dict {"task_id": ..., "description": ...} for workflow engine

The web dashboard (/run endpoint) reads task_id from the response dict to kick off
the WorkflowEngine in a background thread. CLI (main.py) gets the plain string.
"""
from core.local_llm import local_llm


class JavisAgent:

    def __init__(self, mode: str = "auto"):
        """
        mode:
          "auto"   → detect from context (default)
          "cli"    → always return plain string
          "web"    → always return dict with task_id
        """
        self.llm = local_llm
        self.mode = mode

    def _llm_response(self, task: str) -> str:
        prompt = (
            "You are a helpful AI assistant. Answer the user's request clearly and in detail.\n\n"
            f"Task: {task}\n\nResponse:"
        )
        response = self.llm.ask(prompt)
        if response is None:
            return "Error: Ollama is not running. Start it with: ollama serve"
        return response

    def run(self, task: str) -> "str | dict":
        """
        Run a task.
        Returns str in CLI mode, dict with task_id in web mode.
        Web mode submits to TaskQueue so the workflow engine can track progress.
        """
        if self.mode == "cli":
            return self._llm_response(task)

        # Web / auto mode → submit to TaskQueue, return task_id for server.py
        try:
            from core.task_queue import global_task_queue
            task_id = global_task_queue.submit_task(task)
            # Run LLM in background and store result
            import threading

            def _run():
                result = self._llm_response(task)
                global_task_queue.tasks[task_id]["status"] = "completed"
                global_task_queue.tasks[task_id]["result"] = result
                global_task_queue.log(task_id, "LLM response received.")

            threading.Thread(target=_run, daemon=True).start()
            return {"task_id": task_id, "description": task, "status": "running"}

        except Exception:
            # Fallback to plain string if TaskQueue unavailable
            return self._llm_response(task)

    def run_and_save(self, task: str) -> str:
        """Run task (CLI mode) and save result as a report file."""
        from tools.report_tool import create_report
        content = self._llm_response(task)
        topic = "_".join(task.split()[:4]).lower()
        return create_report(topic, content)


# Global singleton — web mode by default (server.py uses this)
jarvis = JavisAgent(mode="web")
