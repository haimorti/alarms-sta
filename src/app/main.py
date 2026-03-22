from __future__ import annotations

import json
from dataclasses import asdict

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.utils.logging import configure_logging


def main() -> None:
    settings = AppSettings.from_env()
    configure_logging(settings.log_level)
    artifacts = bootstrap_application(settings)

    summary = {
        "project_root": str(artifacts.settings.project_root),
        "database_path": str(artifacts.settings.database_path),
        "raw_data_dir": str(artifacts.settings.raw_data_dir),
        "normalized_data_dir": str(artifacts.settings.normalized_data_dir),
        "poller": asdict(artifacts.poller_status),
        "archive_raw_payloads": artifacts.settings.polling.archive_raw_payloads,
        "matching_policy": asdict(artifacts.matching_policy),
        "scoring_thresholds": asdict(artifacts.scoring_thresholds),
        "seed_import_result": asdict(artifacts.seed_import_result),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
