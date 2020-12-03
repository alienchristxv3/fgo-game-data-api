from typing import List, Union

import orjson
import pytest
from fastapi import HTTPException

from app.data.common import Language, Region, ReverseDepth
from app.data.enums import FuncType
from app.data.nice import get_nice_servant_model, parse_dataVals
from app.data.schemas.basic import BasicEquip, BasicServant
from app.data.utils import sort_by_collection_no
from app.routers.utils import list_string_exclude


def test_parse_dataVals_add_state_6_items() -> None:
    result = parse_dataVals("[1000,3,3,300,1000,10]", FuncType.ADD_STATE, Region.NA)
    assert result == {
        "Rate": 1000,
        "Turn": 3,
        "Count": 3,
        "Value": 300,
        "UseRate": 1000,
        "Value2": 10,
    }


def test_parse_dataVals_class_drop_up_rate() -> None:
    result = parse_dataVals("[2,400,80017]", FuncType.CLASS_DROP_UP, Region.NA)
    result = {k: v for k, v in result.items() if "aa" not in k}
    assert result == {
        "EventId": 80017,
        "RateCount": 400,
    }


cases_datavals_fail_dict = {
    "test_dataVals_fail_str_dataVals_no_value": "[HideMiss]",
    "test_dataVals_fail_str_dataVals_str_value": "[HideMiss:123/abc]",
    "test_dataVals_fail_list_str": "[TargetList:123/abc]",
    "test_dataVals_fail_str_not_a_list": "[TargetList:abc]",
}


cases_datavals_fail = [
    pytest.param(value, id=key) for key, value in cases_datavals_fail_dict.items()
]


@pytest.mark.parametrize("dataVals", cases_datavals_fail)
def test_parse_datavals_fail_list_str(dataVals: str) -> None:
    with pytest.raises(HTTPException):
        parse_dataVals(dataVals, 1, Region.NA)


def test_reverseDepth_str_comparison() -> None:
    assert ReverseDepth.function >= "aaaaa"


def test_sort_by_collection_no() -> None:
    first_item = BasicEquip(
        id=9400010,
        collectionNo=1,
        name="Tenacity",
        type="servantEquip",
        rarity=1,
        atkMax=0,
        hpMax=300,
        face="https://assets.atlasacademy.io/GameData/NA/Faces/f_94000100.png",
    )
    second_item = BasicServant(
        id=100100,
        collectionNo=2,
        name="Altria Pendragon",
        type="normal",
        className="saber",
        rarity=5,
        atkMax=11221,
        hpMax=15150,
        face="https://assets.atlasacademy.io/GameData/NA/Faces/f_1001000.png",
    )
    third_item = BasicServant(
        id=202900,
        collectionNo=200,
        name="Asagami Fujino",
        type="normal",
        className="archer",
        rarity=4,
        atkMax=10299,
        hpMax=11025,
        face="https://assets.atlasacademy.io/GameData/NA/Faces/f_2029000.png",
    )
    input_data: List[Union[BasicServant, BasicEquip]] = [
        second_item,
        first_item,
        third_item,
    ]
    result = sort_by_collection_no(input_data)
    assert result == [first_item, second_item, third_item]


def test_list_exclude() -> None:
    test_data = get_nice_servant_model(Region.JP, 504500, Language.en)
    excluded_keys = {"profile"}
    json_data = list_string_exclude([test_data], exclude=excluded_keys)
    for key in excluded_keys:
        assert key not in orjson.loads(json_data)
