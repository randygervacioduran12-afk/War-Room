def build_adapter_prompt(adapter_key: str, goal: str) -> str:
  return f"Adapter={adapter_key}\nGoal={goal}\nOperate within adapter constraints."