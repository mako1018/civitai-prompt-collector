import os
import argparse
from collector import CivitaiPromptCollector

def main():
    parser = argparse.ArgumentParser(description="CivitAI Prompt Collector CLI")
    parser.add_argument("--model-id", help="モデルID（省略で全体）", default=None)
    parser.add_argument("--model-name", help="モデル名（表示用）", default=None)
    parser.add_argument("--max-items", type=int, default=5000, help="1モデルあたり最大件数")
    parser.add_argument("--no-show", action="store_true", help="可視化のウィンドウを表示しない")
    args = parser.parse_args()

    api_key = os.getenv("CIVITAI_API_KEY")
    collector = CivitaiPromptCollector(db_path="civitai_dataset.db", user_agent="CivitaiPromptCollector/1.0")
    if api_key:
        setattr(collector, "api_key", api_key)

    models = {args.model_name or "ALL_MODELS": args.model_id} if args.model_id or args.model_name else {"ALL_MODELS": None}
    results = collector.collect_for_models(models, max_per_model=args.max_items)
    print("収集結果:", results)

    collector.visualize_category_distribution(models_to_plot=list(models.keys()), normalize_percent=True, show=not args.no_show)

if __name__ == "__main__":
    main()
