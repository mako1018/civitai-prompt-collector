from collector import CivitaiPromptCollector

c = CivitaiPromptCollector(db_path="test_collect.db")
print(c.collect_for_models({"test": None}, max_per_model=1))
