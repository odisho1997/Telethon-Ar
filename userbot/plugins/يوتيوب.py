import asyncio
import io
import os
import pathlib
import re
import time
from datetime import datetime

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl import types
from telethon.utils import get_attributes
from youtube_dl import YoutubeDL
from youtube_dl.utils import (
    ContentTooShortError,
    DownloadError,
    ExtractorError,
    GeoRestrictedError,
    MaxDownloadsReached,
    PostProcessingError,
    UnavailableVideoError,
    XAttrMetadataError,
)

from ..helpers.utils import _format
from . import catub, edit_delete, edit_or_reply, hmention, progress, reply_id, ytsearch

plugin_category = "misc"

audio_opts = {
    "format": "bestaudio",
    "addmetadata": True,
    "key": "FFmpegMetadata",
    "writethumbnail": True,
    "prefer_ffmpeg": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }
    ],
    "outtmpl": "%(title)s.mp3",
    "quiet": True,
    "logtostderr": False,
}

video_opts = {
    "format": "best",
    "addmetadata": True,
    "key": "FFmpegMetadata",
    "writethumbnail": True,
    "prefer_ffmpeg": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    "outtmpl": "%(title)s.mp4",
    "logtostderr": False,
    "quiet": True,
}


async def ytdl_down(event, opts, url):
    try:
        await event.edit("** 𖠕 إحضار البيانـات ، يرجى الانتـظار **")
        with YoutubeDL(opts) as ytdl:
            ytdl_data = ytdl.extract_info(url)
    except DownloadError as DE:
        await event.edit(f"`{str(DE)}`")
        return
    except ContentTooShortError:
        await event.edit("𖠕 محـتوى التنزيـل كان قصيرًا جدًا جـاري الارسـال")
        return None
    except GeoRestrictedError:
        await event.edit(
            "**𖠕 الفيديـو غير متـاح من موقـعك الجغرافـي بسبب القيود الجغرافية التي يفرضهـا موقع الويب**"
        )
        return None
    except MaxDownloadsReached:
        await event.edit("**𖠕 تم الوصـول إلى الحـد الأقـصى لعدد التـنزيـلات**")
        return None
    except PostProcessingError:
        await event.edit("**𖠕 حـدث خـطأ أثناء معالجـة ما بعد**")
        return None
    except UnavailableVideoError:
        await event.edit("**𖠕 الوسـائـط غير متوفـرة بالتنسـيق المطـلوب**")
        return None
    except XAttrMetadataError as XAME:
        await event.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
        return None
    except ExtractorError:
        await event.edit("**𖠕 حـدث خـطأ أثناء معالجـة ما بعد**")
        return None
    except Exception as e:
        await event.edit(f"**خطا : **\n__{str(e)}__")
        return None
    return ytdl_data


async def fix_attributes(
    path, info_dict: dict, supports_streaming: bool = False, round_message: bool = False
) -> list:
    """Avoid multiple instances of an attribute."""
    new_attributes = []
    video = False
    audio = False

    uploader = info_dict.get("uploader", "Unknown artist")
    duration = int(info_dict.get("duration", 0))
    suffix = path.suffix[1:]
    if supports_streaming and suffix != "mp4":
        supports_streaming = False

    attributes, mime_type = get_attributes(path)
    if suffix == "mp3":
        title = str(info_dict.get("title", info_dict.get("id", "Unknown title")))
        audio = types.DocumentAttributeAudio(duration, None, title, uploader)
    elif suffix == "mp4":
        width = int(info_dict.get("width", 0))
        height = int(info_dict.get("height", 0))
        for attr in attributes:
            if isinstance(attr, types.DocumentAttributeVideo):
                duration = duration or attr.duration
                width = width or attr.w
                height = height or attr.h
                break
        video = types.DocumentAttributeVideo(
            duration, width, height, round_message, supports_streaming
        )

    if audio and isinstance(audio, types.DocumentAttributeAudio):
        new_attributes.append(audio)
    if video and isinstance(video, types.DocumentAttributeVideo):
        new_attributes.append(video)

    for attr in attributes:
        if (
            isinstance(attr, types.DocumentAttributeAudio)
            and not audio
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not video
            or not isinstance(attr, types.DocumentAttributeAudio)
            and not isinstance(attr, types.DocumentAttributeVideo)
        ):
            new_attributes.append(attr)
    return new_attributes, mime_type


async def _get_file_name(path: pathlib.Path, full: bool = True) -> str:
    return str(path.absolute()) if full else path.stem + path.suffix


@catub.cat_cmd(
    pattern="yta(?: |$)(.*)",
    command=("yta", plugin_category),
    info={
        "header": "To download audio from many sites like Youtube",
        "description": "downloads the audio from the given link (Suports the all sites which support youtube-dl)",
        "examples": [
            "{tr}yta <reply to link>",
            "{tr}yta <link>",
        ],
    },
)
async def download_audio(event):
    """To download audio from YouTube and many other sites."""
    url = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not url and rmsg:
        myString = rmsg.text
        url = re.search("(?P<url>https?://[^\s]+)", myString).group("url")
    if not url:
        return await edit_or_reply(event, "قم بوضع الامر بجانبه رابط الفيديو")
    catevent = await edit_or_reply(event, "𖠕 ... جـاري تحميل ..")
    reply_to_id = await reply_id(event)
    ytdl_data = await ytdl_down(catevent, audio_opts, url)
    if ytdl_data is None:
        return
    await catevent.edit(
        f"`Preparing to upload song:`\
        \n**{ytdl_data['title']}**\
        \nby *{ytdl_data['uploader']}*"
    )
    f = pathlib.Path(f"{ytdl_data['title']}.mp3".replace("|", "_"))
    catthumb = pathlib.Path(f"{ytdl_data['title']}.mp3.jpg".replace("|", "_"))
    if not os.path.exists(catthumb):
        catthumb = pathlib.Path(f"{ytdl_data['title']}.mp3.webp".replace("|", "_"))
    if not os.path.exists(catthumb):
        catthumb = None
    c_time = time.time()
    ul = io.open(f, "rb")
    uploaded = await event.client.fast_upload_file(
        file=ul,
        progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
            progress(d, t, catevent, c_time, "upload", file_name=f)
        ),
    )
    ul.close()
    attributes, mime_type = await fix_attributes(f, ytdl_data, supports_streaming=True)
    media = types.InputMediaUploadedDocument(
        file=uploaded,
        mime_type=mime_type,
        attributes=attributes,
        thumb=await event.client.upload_file(catthumb) if catthumb else None,
    )
    await event.client.send_file(
        event.chat_id,
        file=media,
        reply_to=reply_to_id,
        caption=ytdl_data["title"],
        supports_streaming=True,
        force_document=False,
    )
    os.remove(f)
    if catthumb:
        os.remove(catthumb)
    await catevent.delete()


@catub.cat_cmd(
    pattern="ytv(?: |$)(.*)",
    command=("ytv", plugin_category),
    info={
        "header": "للتحميل عبر رابط يوتيوب",
        "description": "تحميل عبر رابط يوتيوب بواسطه مكتبه youtube-dl",
        "examples": [
            "{tr}ytv <reply to link>",
            "{tr}ytv <link>",
        ],
    },
)
async def download_video(event):
    """To download video from YouTube and many other sites."""
    url = event.pattern_match.group(1)
    rmsg = await event.get_reply_message()
    if not url and rmsg:
        myString = rmsg.text
        url = re.search("(?P<url>https?://[^\s]+)", myString).group("url")
    if not url:
        return await edit_or_reply(event, "قم بوضع الامر بجانبه رابط الفيديو")
    catevent = await edit_or_reply(event, "جاري التحميل")
    reply_to_id = await reply_id(event)
    ytdl_data = await ytdl_down(catevent, video_opts, url)
    if ytdl_down is None:
        return
    f = pathlib.Path(f"{ytdl_data['title']}.mp4".replace("|", "_"))
    catthumb = pathlib.Path(f"{ytdl_data['title']}.jpg".replace("|", "_"))
    if not os.path.exists(catthumb):
        catthumb = pathlib.Path(f"{ytdl_data['title']}.webp".replace("|", "_"))
    if not os.path.exists(catthumb):
        catthumb = None
    await catevent.edit(
        f"`Preparing to upload video:`\
        \n**{ytdl_data['title']}**\
        \nby *{ytdl_data['uploader']}*"
    )
    ul = io.open(f, "rb")
    c_time = time.time()
    attributes, mime_type = await fix_attributes(f, ytdl_data, supports_streaming=True)
    uploaded = await event.client.fast_upload_file(
        file=ul,
        progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
            progress(d, t, catevent, c_time, "upload", file_name=f)
        ),
    )
    ul.close()
    media = types.InputMediaUploadedDocument(
        file=uploaded,
        mime_type=mime_type,
        attributes=attributes,
        thumb=await event.client.upload_file(catthumb) if catthumb else None,
    )
    await event.client.send_file(
        event.chat_id,
        file=media,
        reply_to=reply_to_id,
        caption=ytdl_data["title"],
    )
    os.remove(f)
    if catthumb:
        os.remove(catthumb)
    await event.delete()


@catub.cat_cmd(
    pattern="yts(?: |$)(\d*)? ?(.*)",
    command=("yts", plugin_category),
    info={
        "header": "للبحث في اليوتيوب",
        "description": "للتحميل والبحث من  يوتيوب خلال ثواني قليله",
        "examples": [
            "{tr}yts <query>",
            "{tr}yts <1-9> <query>",
        ],
    },
)
async def yt_search(event):
    "Youtube search command"
    if event.is_reply and not event.pattern_match.group(2):
        query = await event.get_reply_message()
        query = str(query.message)
    else:
        query = str(event.pattern_match.group(2))
    if not query:
        return await edit_delete(
            event, "**𖠕 الـرد على رسالـة أو تمريـر استعـلام للبحـث**"
        )
    video_q = await edit_or_reply(event, "**𖠕 جـاري البـحث...**")
    if event.pattern_match.group(1) != "":
        lim = int(event.pattern_match.group(1))
        if lim <= 0:
            lim = int(10)
    else:
        lim = int(10)
    try:
        full_response = await ytsearch(query, limit=lim)
    except Exception as e:
        return await edit_delete(video_q, str(e), time=10, parse_mode=_format.parse_pre)
    reply_text = f"**•  Search Query:**\n`{query}`\n\n**•  Results:**\n{full_response}"
    await edit_or_reply(video_q, reply_text)


@catub.cat_cmd(
    pattern="insta (.*)",
    command=("insta", plugin_category),
    info={
        "header": "للتحميل من الانستجرام صوره او فيديو",
        "description": "ملاحظة يتم تنزيل صور / مقاطع فيديو الملف الشخصي العامة فقط.",
        "examples": [
            "{tr}insta <link>",
        ],
    },
)
async def kakashi(event):
    "For downloading instagram media"
    chat = "@instasavegrambot"
    link = event.pattern_match.group(1)
    if "www.instagram.com" not in link:
        await edit_or_reply(
            event, "ضع الامر بجانبه رابط الفديو او الصوره من الانستا"
        )
    else:
        start = datetime.now()
        catevent = await edit_or_reply(event, "جاري التحميل أنتضر")
    async with event.client.conversation(chat) as conv:
        try:
            msg_start = await conv.send_message("/start")
            response = await conv.get_response()
            msg = await conv.send_message(link)
            video = await conv.get_response()
            details = await conv.get_response()
            await event.client.send_read_acknowledge(conv.chat_id)
        except YouBlockedUserError:
            await catevent.edit("**خطا:** `افتح الحضر من البوت` @instasavegrambot `قم محاوله مره اخرى!`")
            return
        await catevent.delete()
        cat = await event.client.send_file(
            event.chat_id,
            video,
        )
        end = datetime.now()
        ms = (end - start).seconds
        await cat.edit(
            f"<b><i>➥ هذا الفديو الخاص بك خلال {ms} ثانية </i></b>\n<b><i>➥ الرفع بواسطة :- {hmention}</i></b>",
            parse_mode="html",
        )
    await event.client.delete_messages(
        conv.chat_id, [msg_start.id, response.id, msg.id, video.id, details.id]
    )
