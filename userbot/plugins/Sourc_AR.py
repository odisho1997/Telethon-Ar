import time
from platform import python_version

from telethon import version

from . import ALIVE_NAME, StartTime, catversion, get_readable_time, mention, reply_id

DEFAULTUSER = ALIVE_NAME or "I𝐐𝐓𝐇𝐎𝐍⁦♡⁩"
CAT_IMG = Config.ALIVE_PIC or "https://telegra.ph/file/1d335e1edc99d0288cf3c.jpg"
CUSTOM_ALIVE_TEXT = Config.CUSTOM_ALIVE_TEXT or "⇝ 𝗪َ𝗘𝗟َِ𝗖𝗢𝗠َِ𝙀َِ 𝗧𝗢 𝗧𝗘𝗟𝗘𝗧𝗛𝗢𝗡 𝗔َِ𝗥َِ𝗔𝗕َِ𝗦 ⇜"
EMOJI = Config.CUSTOM_ALIVE_EMOJI or "𖠕"


@bot.on(admin_cmd(outgoing=True, pattern="alive$"))
@bot.on(sudo_cmd(pattern="alive$", allow_sudo=True))
async def amireallyalive(alive):
    if alive.fwd_from:
        return
    reply_to_id = await reply_id(alive)
    uptime = await get_readable_time((time.time() - StartTime))
    _, check_sgnirts = check_data_base_heal_th()
    if CAT_IMG:
        cat_caption = f"**{CUSTOM_ALIVE_TEXT}**\n"
        cat_caption += f"**{EMOJI} قاعدة البيانات :**『 `{check_sgnirts}`』\n"
        cat_caption += f"**{EMOJI} نسخة تليثون :** 『`{version.__version__}』\n`"
        cat_caption += f"**{EMOJI} نسخـة العـرب :** 『`{catversion}`』\n"
        cat_caption += f"**{EMOJI} نسخة البايثون :**『 `{python_version()}』\n`"
        cat_caption += f"**{EMOJI} الوقت :**『 `{uptime}』\n`"
        cat_caption += f"**{EMOJI} المنشئ:**『 {mention}』\n"
        cat_caption += f"**Ξ**  **[𝖲𝗈𝗎𝗋𝖼𝖾]**(t.me/M4_STORY)  𖠕 .\n"
        await alive.client.send_file(
            alive.chat_id, CAT_IMG, caption=cat_caption, reply_to=reply_to_id
        )
        await alive.delete()
    else:
        await edit_or_reply(
            alive,
             f"**{CUSTOM_ALIVE_TEXT}**\n"
        f"**{EMOJI} قاعدة البيانات 『** `1.0.0`』\n"
        f"**{EMOJI} اصدار التليثون  『** `1.0.0`』\n`"
        f"**{EMOJI} اصدار تليثون العرب 『** `1.0.0`』\n"
        f"**{EMOJI} اصدار البايثون 『** `1.0.0`』\n`"
        f"**{EMOJI} مدة التشغيل 『** `{uptime}』\n`"
        f"**{EMOJI} المستخدم 『** {mention}』\n",
        )


def check_data_base_heal_th():
    # https://stackoverflow.com/a/41961968
    is_database_working = False
    output = "لم يتم تعيين قاعدة بيانات"
    if not Config.DB_URI:
        return is_database_working, output
    from userbot.plugins.sql_helper import SESSION

    try:
        # to check database we will execute raw query
        SESSION.execute("SELECT 1")
    except Exception as e:
        output = f"❌ {str(e)}"
        is_database_working = False
    else:
        output = "تعمل بنجاح"
        is_database_working = True
    return is_database_working, output


CMD_HELP.update(
    {
        "alive": "**Plugin :** `alive`\
      \n\n  •  **Syntax : **`.alive` \
      \n  •  **Function : **__status of bot will be showed__\
      \n\n  •  **Syntax : **`.` \
      \n  •  **Function : **__inline status of bot will be shown.__\
      \nSet `ALIVE_PIC` var for media in alive message"
    }
)
