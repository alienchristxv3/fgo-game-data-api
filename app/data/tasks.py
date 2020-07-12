import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from git import Repo

from ..config import Settings
from ..routers.utils import list_string
from .basic import get_basic_svt
from .common import Region
from .enums import TRAIT_NAME
from .gamedata import masters, region_path, update_gamedata
from .nice import (
    get_nice_command_code,
    get_nice_equip_model,
    get_nice_item,
    get_nice_mystic_code,
    get_nice_servant_model,
)
from .schemas.base import BaseModelORJson
from .schemas.nice import Language


settings = Settings()
logger = logging.getLogger()


file_path = Path(__file__).resolve()
export_path = file_path.parents[2] / "export"


def dump_normal(region: Region, file_name: str, data: Any):  # pragma: no cover
    file_name = file_name + ".json"
    with open(export_path / region.value / file_name, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False)


def dump_orjson(
    region: Region, file_name: str, data: Iterable[BaseModelORJson]
):  # pragma: no cover
    file_name = file_name + ".json"
    with open(export_path / region.value / file_name, "w", encoding="utf-8") as fp:
        fp.write(list_string(data))


def dump(region: Region, file_name: str, data: Any):  # pragma: no cover
    if isinstance(data, list) and isinstance(data[0], BaseModelORJson):
        dump_orjson(region, file_name, data)
    else:
        dump_normal(region, file_name, data)


def sort_by_collection_no(input_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(input_list, key=lambda x: x["collectionNo"])


def generate_exports():  # pragma: no cover
    if settings.export_all_nice:
        for region in region_path:
            start_time = time.perf_counter()
            logger.info(f"Exporting {region} data …")
            all_equip_data = [
                get_nice_equip_model(region, item_id)
                for item_id in masters[region].mstSvtEquipCollectionNo.values()
            ]
            all_servant_data = [
                get_nice_servant_model(region, item_id)
                for item_id in masters[region].mstSvtServantCollectionNo.values()
            ]
            all_item_data = [
                get_nice_item(region, item_id) for item_id in masters[region].mstItemId
            ]
            all_mc_data = [
                get_nice_mystic_code(region, item_id)
                for item_id in masters[region].mstEquipId
            ]
            all_cc_data = [
                get_nice_command_code(region, item_id)
                for item_id in masters[region].mstCommandCodeId
            ]
            all_basic_servant_data = sort_by_collection_no(
                [
                    get_basic_svt(region, item_id)
                    for item_id in masters[region].mstSvtServantCollectionNo.values()
                ]
            )
            all_basic_equip_data = sort_by_collection_no(
                [
                    get_basic_svt(region, item_id)
                    for item_id in masters[region].mstSvtEquipCollectionNo.values()
                ]
            )

            output_files = {
                "nice_trait": TRAIT_NAME,
                "nice_command_code": all_cc_data,
                "nice_item": all_item_data,
                "nice_servant": all_servant_data,
                "nice_equip": all_equip_data,
                "nice_mystic_code": all_mc_data,
                "basic_servant": all_basic_servant_data,
                "basic_equip": all_basic_equip_data,
            }

            for file_name, data in output_files.items():
                dump(region, file_name, data)

            if region == Region.JP:
                all_basic_servant_en = sort_by_collection_no(
                    [
                        get_basic_svt(region, item_id, Language.en)
                        for item_id in masters[
                            region
                        ].mstSvtServantCollectionNo.values()
                    ]
                )

                dump_normal(region, "basic_servant_lang_en", all_basic_servant_en)

            run_time = time.perf_counter() - start_time
            logger.info(f"Finished exporting {region} data in {run_time:.4f}s.")


generate_exports()


repo_info = {}


def update_repo_info():
    for region, gamedata in region_path.items():
        if (gamedata.parent / ".git").exists():
            repo = Repo(gamedata.parent)
            latest_commit = repo.commit()
            repo_info[region] = {
                "hash": latest_commit.hexsha[:6],  # type: ignore
                "timestamp": latest_commit.committed_date,  # type: ignore
            }


update_repo_info()


def pull_and_update():  # pragma: no cover
    logger.info(f"Sleeping {settings.github_webhook_sleep} seconds …")
    time.sleep(settings.github_webhook_sleep)
    for region, gamedata in region_path.items():
        if (gamedata.parent / ".git").exists():
            repo = Repo(gamedata.parent)
            for fetch_info in repo.remotes[0].pull():  # type: ignore
                commit_hash = fetch_info.commit.hexsha[:6]
                logger.info(f"Updated {fetch_info.ref} to {commit_hash}")
                repo_info[region] = {
                    "hash": commit_hash,
                    "timestamp": fetch_info.committed_date,
                }
    update_gamedata()
    generate_exports()
    update_repo_info()
