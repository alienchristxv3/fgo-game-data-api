from typing import Any, Iterable, Mapping, Optional, TypeVar, Union

from ..data.custom_mappings import (
    TRANSLATION_FILE_NAMES,
    TRANSLATION_OVERRIDE,
    TRANSLATIONS,
)
from ..schemas.basic import BasicCommandCode, BasicEquip, BasicServant
from ..schemas.common import Language, NiceTrait
from ..schemas.enums import TRAIT_NAME, Trait
from ..schemas.nice import NiceCommandCode, NiceEquip, NiceServant


TValue = TypeVar("TValue")
TLookup = TypeVar("TLookup")


def get_translation(
    language: Language,
    string: str,
    override_file: Optional[TRANSLATION_FILE_NAMES] = None,
    override_id: Optional[str] = None,
) -> str:
    if language == Language.en:
        if (
            override_file
            and override_id
            and override_id in TRANSLATION_OVERRIDE[override_file]
        ):
            return TRANSLATION_OVERRIDE[override_file][override_id]

        return TRANSLATIONS.get(string, string)

    return string


def get_safe(input_dict: Mapping[Any, TValue], key: TLookup) -> Union[TValue, TLookup]:
    """
    A dict getter that returns the lookup key if it's not found in the dict.
    """
    return input_dict.get(key, key)


def get_nice_trait(individuality: int) -> NiceTrait:
    """Return the corresponding NiceTrait object given the individuality"""
    if individuality >= 0:
        return NiceTrait(
            id=individuality, name=TRAIT_NAME.get(individuality, Trait.unknown)
        )

    return NiceTrait(
        id=-individuality,
        name=TRAIT_NAME.get(-individuality, Trait.unknown),
        negative=True,
    )


def get_traits_list(input_idv: Iterable[int]) -> list[NiceTrait]:
    """
    Return the corresponding list NiceTrait objects given the individuality list
    """
    return [get_nice_trait(individuality) for individuality in input_idv]


THasColNo = TypeVar(
    "THasColNo",
    BasicServant,
    BasicEquip,
    BasicCommandCode,
    NiceServant,
    NiceEquip,
    NiceCommandCode,
)


def sort_by_collection_no(input_list: Iterable[THasColNo]) -> list[THasColNo]:
    """
    Return given list of basic svt objects sorted by their collectionNo attribute
    """
    return sorted(input_list, key=lambda x: x.collectionNo)


def get_lang_en(svt: THasColNo) -> THasColNo:
    """
    Returns given svt Pydantic object with English name
    """
    lang_en_svt = svt.copy()
    lang_en_svt.name = get_safe(TRANSLATIONS, svt.name)
    return lang_en_svt


FORMATTING_BRACKETS = {"[g][o]": "", "[/o][/g]": "", " [{0}] ": " ", "[{0}]": ""}


def strip_formatting_brackets(detail_string: str) -> str:
    """Remove formatting codes such as [g][o] from detail string"""
    for k, v in FORMATTING_BRACKETS.items():
        detail_string = detail_string.replace(k, v)
    return detail_string


def nullable_to_string(nullable: Optional[str]) -> str:
    """Returns an empty string is the input is None"""
    if nullable is None:
        return ""
    else:
        return nullable
