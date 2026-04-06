import argparse
import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path


def random_id(prefix: str, length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_{''.join(random.choice(alphabet) for _ in range(length))}"


def build_review_text() -> str:
    words = [
        "great", "movie", "boring", "plot", "actor", "sound", "scene", "final",
        "good", "bad", "excellent", "slow", "dynamic", "visual", "music", "dialogue",
    ]
    size = random.randint(8, 20)
    return " ".join(random.choice(words) for _ in range(size))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=10000000)
    parser.add_argument("--output", type=str, default="scripts/ugc_benchmark_data.jsonl")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2026, 4, 1, 12, 0, 0)

    with output.open("w", encoding="utf-8", newline="\n") as file:
        for index in range(args.rows):
            user_id = random_id("user")
            movie_id = random_id("movie")
            created_at = (base_time + timedelta(seconds=index)).isoformat()

            row = {
                "bookmark": {
                    "id": random_id("bookmark"),
                    "user_id": user_id,
                    "movie_id": movie_id,
                    "created_at": created_at,
                    "updated_at": created_at,
                },
                "like": {
                    "id": random_id("like"),
                    "user_id": user_id,
                    "movie_id": movie_id,
                    "created_at": created_at,
                    "updated_at": created_at,
                },
                "review": {
                    "id": random_id("review"),
                    "user_id": user_id,
                    "movie_id": movie_id,
                    "text": build_review_text(),
                    "rating": random.randint(1, 10),
                    "created_at": created_at,
                    "updated_at": created_at,
                },
            }

            file.write(json.dumps(row, ensure_ascii=False))
            file.write("\n")

    print(output)


if __name__ == "__main__":
    main()