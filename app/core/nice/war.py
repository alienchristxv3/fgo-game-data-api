from sqlalchemy.ext.asyncio import AsyncConnection

from ...config import Settings
from ...db.helpers import fetch
from ...schemas.common import Language, Region
from ...schemas.gameenums import (
    COND_TYPE_NAME,
    SPOT_OVERWRITE_TYPE_NAME,
    WAR_FLAG_NAME,
    WAR_OVERWRITE_TYPE_NAME,
    WAR_START_TYPE_NAME,
    WarEntityFlag,
    WarOverwriteType,
)
from ...schemas.nice import (
    AssetURL,
    NiceMap,
    NiceMapGimmick,
    NiceQuest,
    NiceSpot,
    NiceSpotAdd,
    NiceSpotRoad,
    NiceWar,
    NiceWarAdd,
    NiceWarQuestSelection,
)
from ...schemas.raw import (
    MstBgm,
    MstConstant,
    MstMap,
    MstMapGimmick,
    MstSpot,
    MstSpotAdd,
    MstSpotRoad,
    MstWar,
    MstWarAdd,
    MstWarQuestSelection,
    QuestEntity,
)
from .. import raw
from ..utils import fmt_url, get_flags, get_translation
from .base_script import get_script_url
from .bgm import get_nice_bgm
from .quest import get_nice_quest


settings = Settings()


def get_nice_spot_road(
    region: Region, spot_road: MstSpotRoad, war_asset_id: int
) -> NiceSpotRoad:
    return NiceSpotRoad(
        id=spot_road.id,
        warId=spot_road.warId,
        mapId=spot_road.mapId,
        image=fmt_url(
            AssetURL.spotRoadImg,
            base_url=settings.asset_url,
            region=region,
            war_asset_id=war_asset_id,
        ),
        srcSpotId=spot_road.srcSpotId,
        dstSpotId=spot_road.dstSpotId,
        dispCondType=COND_TYPE_NAME[spot_road.dispCondType],
        dispTargetId=spot_road.dispTargetId,
        dispTargetValue=spot_road.dispTargetValue,
        dispCondType2=COND_TYPE_NAME[spot_road.dispCondType2],
        dispTargetId2=spot_road.dispTargetId2,
        dispTargetValue2=spot_road.dispTargetValue2,
        activeCondType=COND_TYPE_NAME[spot_road.activeCondType],
        activeTargetId=spot_road.activeTargetId,
        activeTargetValue=spot_road.activeTargetValue,
    )


def get_nice_map_gimmick(
    region: Region, raw_map_gimmick: MstMapGimmick, war_asset_id: int
) -> NiceMapGimmick:
    return NiceMapGimmick(
        id=raw_map_gimmick.id,
        image=fmt_url(
            AssetURL.mapGimmickImg,
            base_url=settings.asset_url,
            region=region,
            war_asset_id=war_asset_id,
            gimmick_id=raw_map_gimmick.id,
        ),
        x=raw_map_gimmick.x,
        y=raw_map_gimmick.y,
        depthOffset=raw_map_gimmick.depthOffset,
        scale=raw_map_gimmick.scale,
        dispCondType=COND_TYPE_NAME[raw_map_gimmick.dispCondType],
        dispTargetId=raw_map_gimmick.dispTargetId,
        dispTargetValue=raw_map_gimmick.dispTargetValue,
        dispCondType2=COND_TYPE_NAME[raw_map_gimmick.dispCondType2],
        dispTargetId2=raw_map_gimmick.dispTargetId2,
        dispTargetValue2=raw_map_gimmick.dispTargetValue2,
        actionAnimTime=raw_map_gimmick.actionAnimTime,
        actionEffectId=raw_map_gimmick.actionEffectId,
        startedAt=raw_map_gimmick.startedAt,
        endedAt=raw_map_gimmick.endedAt,
    )


def get_nice_map(
    region: Region,
    raw_map: MstMap,
    bgms: list[MstBgm],
    gimmicks: list[MstMapGimmick],
    war_asset_id: int,
    lang: Language,
) -> NiceMap:
    base_settings = {"base_url": settings.asset_url, "region": region}

    bgm = get_nice_bgm(
        region, next(bgm for bgm in bgms if bgm.id == raw_map.bgmId), lang
    )

    return NiceMap(
        id=raw_map.id,
        mapImage=fmt_url(AssetURL.mapImg, **base_settings, map_id=raw_map.mapImageId)
        if raw_map.mapImageId != 0
        else None,
        mapImageW=raw_map.mapImageW,
        mapImageH=raw_map.mapImageH,
        mapGimmicks=[
            get_nice_map_gimmick(region, gimmick, war_asset_id) for gimmick in gimmicks
        ],
        headerImage=fmt_url(
            AssetURL.banner,
            **base_settings,
            banner=f"img_title_header_{raw_map.headerImageId}",
        )
        if raw_map.headerImageId != 0
        else None,
        bgm=bgm,
    )


def get_nice_war_add(
    region: Region, war_add: MstWarAdd, banner_template: str
) -> NiceWarAdd:
    banner_url = (
        fmt_url(
            AssetURL.banner,
            base_url=settings.asset_url,
            region=region,
            banner=banner_template.format(war_add.overwriteId),
        )
        if war_add.type == WarOverwriteType.BANNER
        else None
    )

    return NiceWarAdd(
        warId=war_add.warId,
        type=WAR_OVERWRITE_TYPE_NAME[war_add.type],
        priority=war_add.priority,
        overwriteId=war_add.overwriteId,
        overwriteStr=war_add.overwriteStr,
        overwriteBanner=banner_url,
        condType=COND_TYPE_NAME[war_add.condType],
        targetId=war_add.targetId,
        value=war_add.value,
        startedAt=war_add.startedAt,
        endedAt=war_add.endedAt,
    )


async def get_nice_war_quest_selection(
    conn: AsyncConnection,
    region: Region,
    quest_selection: MstWarQuestSelection,
    mstWar: MstWar,
    quests: list[QuestEntity],
    spots: list[MstSpot],
    lang: Language,
) -> NiceWarQuestSelection:
    banner_url = (
        fmt_url(
            AssetURL.eventUi,
            base_url=settings.asset_url,
            region=region,
            event=f"img_questboard_{quest_selection.shortCutBannerId}",
        )
        if quest_selection.shortCutBannerId != 0
        else None
    )
    quest = next(
        quest for quest in quests if quest.mstQuest.id == quest_selection.questId
    )
    spot = next(spot for spot in spots if spot.id == quest.mstQuest.spotId)
    return NiceWarQuestSelection(
        quest=NiceQuest.parse_obj(
            await get_nice_quest(conn, region, quest, lang, mstWar, spot)
        ),
        shortcutBanner=banner_url,
        priority=quest_selection.priority,
    )


def get_nice_spot_add(mstWarAdd: MstSpotAdd) -> NiceSpotAdd:
    return NiceSpotAdd(
        priority=mstWarAdd.priority,
        overrideType=SPOT_OVERWRITE_TYPE_NAME[mstWarAdd.overrideType],
        targetId=mstWarAdd.targetId,
        targetText="" if mstWarAdd.targetText is None else mstWarAdd.targetText,
        condType=COND_TYPE_NAME[mstWarAdd.condType],
        condTargetId=mstWarAdd.condTargetId,
        condNum=mstWarAdd.condNum,
    )


async def get_nice_spot(
    conn: AsyncConnection,
    region: Region,
    mstWar: MstWar,
    raw_spot: MstSpot,
    mst_spot_adds: list[MstSpotAdd],
    war_asset_id: int,
    quests: list[QuestEntity],
    lang: Language,
) -> NiceSpot:
    return NiceSpot(
        id=raw_spot.id,
        joinSpotIds=raw_spot.joinSpotIds,
        mapId=raw_spot.mapId,
        name=get_translation(lang, raw_spot.name),
        originalName=raw_spot.name,
        image=fmt_url(
            AssetURL.spotImg,
            base_url=settings.asset_url,
            region=region,
            war_asset_id=war_asset_id,
            spot_id=raw_spot.imageId,
        )
        if raw_spot.imageId != 0
        else None,
        x=raw_spot.x,
        y=raw_spot.y,
        imageOfsX=raw_spot.imageOfsX,
        imageOfsY=raw_spot.imageOfsY,
        nameOfsX=raw_spot.nameOfsX,
        nameOfsY=raw_spot.nameOfsY,
        questOfsX=raw_spot.questOfsX,
        questOfsY=raw_spot.questOfsY,
        nextOfsX=raw_spot.nextOfsX,
        nextOfsY=raw_spot.nextOfsY,
        closedMessage=raw_spot.closedMessage,
        spotAdds=[
            get_nice_spot_add(spot_add)
            for spot_add in mst_spot_adds
            if spot_add.spotId == raw_spot.id
        ],
        quests=[
            NiceQuest.parse_obj(
                await get_nice_quest(conn, region, quest, lang, mstWar, raw_spot)
            )
            for quest in quests
            if quest.mstQuest.spotId == raw_spot.id
        ],
    )


async def get_nice_war(
    conn: AsyncConnection, region: Region, war_id: int, lang: Language
) -> NiceWar:
    raw_war = await raw.get_war_entity(conn, war_id)

    base_settings = {"base_url": settings.asset_url, "region": region}
    war_asset_id = (
        raw_war.mstWar.assetId if raw_war.mstWar.assetId > 0 else raw_war.mstWar.id
    )

    if raw_war.mstWar.flag & WarEntityFlag.MAIN_SCENARIO != 0:
        last_war_id = await fetch.get_one(conn, MstConstant, "LAST_WAR_ID")
        if raw_war.mstWar.id > 10000 or (
            last_war_id and raw_war.mstWar.id <= last_war_id.value
        ):
            banner_template = "questboard_cap{:>03}"
            banner_id = raw_war.mstWar.bannerId
        else:
            banner_template = "questboard_cap_closed"
            banner_id = 0
    elif (
        raw_war.mstWar.flag & WarEntityFlag.IS_EVENT != 0
        and raw_war.mstWar.flag & WarEntityFlag.SUB_FOLDER == 0
        and raw_war.mstEvent
    ):
        banner_template = "event_war_{}"
        banner_id = raw_war.mstEvent.bannerId
    else:
        banner_template = "chaldea_category_{}"
        banner_id = raw_war.mstWar.bannerId

    banner_file = banner_template.format(banner_id)

    bgm = get_nice_bgm(
        region,
        next(bgm for bgm in raw_war.mstBgm if bgm.id == raw_war.mstWar.bgmId),
        lang,
    )

    return NiceWar(
        id=raw_war.mstWar.id,
        coordinates=raw_war.mstWar.coordinates,
        age=raw_war.mstWar.age,
        name=get_translation(lang, raw_war.mstWar.name),
        originalName=raw_war.mstWar.name,
        longName=get_translation(lang, raw_war.mstWar.longName),
        originalLongName=raw_war.mstWar.longName,
        flags=get_flags(raw_war.mstWar.flag, WAR_FLAG_NAME),
        banner=fmt_url(AssetURL.banner, **base_settings, banner=banner_file)
        if raw_war.mstWar.bannerId != 0
        else None,
        headerImage=fmt_url(
            AssetURL.banner,
            **base_settings,
            banner=f"img_title_header_{raw_war.mstWar.headerImageId}",
        )
        if raw_war.mstWar.headerImageId != 0
        else None,
        priority=raw_war.mstWar.priority,
        parentWarId=raw_war.mstWar.parentWarId,
        materialParentWarId=raw_war.mstWar.materialParentWarId,
        emptyMessage=raw_war.mstWar.emptyMessage,
        bgm=bgm,
        scriptId=raw_war.mstWar.scriptId,
        script=get_script_url(region, raw_war.mstWar.scriptId),
        startType=WAR_START_TYPE_NAME[raw_war.mstWar.startType],
        targetId=raw_war.mstWar.targetId,
        eventId=raw_war.mstWar.eventId,
        eventName=get_translation(lang, raw_war.mstWar.eventName),
        lastQuestId=raw_war.mstWar.lastQuestId,
        warAdds=[
            get_nice_war_add(region, war_add, banner_template)
            for war_add in raw_war.mstWarAdd
        ],
        maps=[
            get_nice_map(
                region,
                raw_map,
                raw_war.mstBgm,
                [
                    gimmick
                    for gimmick in raw_war.mstMapGimmick
                    if gimmick.mapId == raw_map.id
                ],
                war_asset_id,
                lang,
            )
            for raw_map in raw_war.mstMap
        ],
        spots=[
            await get_nice_spot(
                conn,
                region,
                raw_war.mstWar,
                raw_spot,
                raw_war.mstSpotAdd,
                war_asset_id,
                raw_war.mstQuest,
                lang,
            )
            for raw_spot in raw_war.mstSpot
            if raw_spot.warId == war_id
        ],
        spotRoads=[
            get_nice_spot_road(region, spot_road, war_asset_id)
            for spot_road in raw_war.mstSpotRoad
        ],
        questSelections=[
            await get_nice_war_quest_selection(
                conn,
                region,
                quest_selection,
                raw_war.mstWar,
                raw_war.mstQuest,
                raw_war.mstSpot,
                lang,
            )
            for quest_selection in raw_war.mstWarQuestSelection
        ],
    )
