"""
Tutedude Course Video Downloader
- API: lmsapi.tutedude.com (accessToken cookie auth)
- Video URL: https://d44tj0kek3n57.cloudfront.net/transcoded/{tpStreamId}/video.m3u8
- Quality: best available up to 480p (no auth needed)
"""
import os
import asyncio
import aiohttp
import json
import time
import re

CLOUDFRONT_BASE = "https://d44tj0kek3n57.cloudfront.net/transcoded"
BABY_API = "https://baby.tutedude.com/api"
LMSAPI  = "https://lmsapi.tutedude.com/api"

# Credentials from env vars or hardcoded fallback
TUTEDUDE_EMAIL    = os.environ.get("TUTEDUDE_EMAIL", "gaurlekhanshu.1520@gmail.com")
TUTEDUDE_PASSWORD = os.environ.get("TUTEDUDE_PASSWORD", "Lekh@nshu1520")

_token_cache = {"token": None, "expires": 0}


async def get_access_token() -> str:
    """Login and return Bearer accessToken (cached 50 min)"""
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    headers = {"Content-Type": "application/json",
               "User-Agent": "Mozilla/5.0 Chrome/122",
               "Origin": "https://upskill.tutedude.com"}
    payload = {"email": TUTEDUDE_EMAIL, "password": TUTEDUDE_PASSWORD}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BABY_API}/auth/login", json=payload, headers=headers) as r:
            data = await r.json()
    token = data["data"]["accessToken"]
    _token_cache["token"] = token
    _token_cache["expires"] = time.time() + 50 * 60
    return token


async def get_course_lectures(course_slug: str) -> list:
    """Return list of {index, title, tpStreamId, section} for a course"""
    token = await get_access_token()
    headers = {
        "Cookie": f"accessToken={token}",
        "User-Agent": "Mozilla/5.0 Chrome/122",
        "Origin": "https://upskill.tutedude.com",
        "Referer": f"https://upskill.tutedude.com/course/lecture-{course_slug}",
    }
    async with aiohttp.ClientSession() as s:
        async with s.get(
            f"{LMSAPI}/courses/content?course={course_slug}", headers=headers
        ) as r:
            data = await r.json()

    if not data.get("success"):
        return []

    lectures = []
    idx = 0
    for section in data["data"].get("content", []):
        if section.get("type") != "section":
            continue
        sec_name = section.get("name", "")
        for lec in section.get("lectures", []):
            tp_id = lec.get("tpStreamId", "")
            if not tp_id:
                continue
            idx += 1
            lectures.append({
                "index": idx,
                "title": lec.get("name", lec.get("title", f"Lecture {idx}")),
                "tpStreamId": tp_id,
                "section": sec_name,
                "duration": lec.get("duration", 0),
            })
    return lectures


async def get_all_courses() -> list:
    """Return list of all available courses {courseName, slug, numberOfLectures}"""
    token = await get_access_token()
    headers = {
        "Cookie": f"accessToken={token}",
        "User-Agent": "Mozilla/5.0 Chrome/122",
        "Origin": "https://upskill.tutedude.com",
    }
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{LMSAPI}/courses/all-details", headers=headers) as r:
            data = await r.json()
    return data.get("data", [])


async def get_enrolled_courses() -> list:
    """Return only courses the user is enrolled in"""
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 Chrome/122",
    }
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{BABY_API}/users/me", headers=headers) as r:
            data = await r.json()
    return data.get("data", {}).get("courses", [])


def get_m3u8_url(tp_stream_id: str, quality: int = 480) -> str:
    """Build the direct HLS m3u8 URL for a TpStream video"""
    return f"{CLOUDFRONT_BASE}/{tp_stream_id}/video.m3u8"


async def download_lecture(tp_stream_id: str, output_path: str, quality: int = 480) -> str | None:
    """
    Download a lecture video via yt-dlp.
    Returns the downloaded file path or None on failure.
    """
    m3u8_url = get_m3u8_url(tp_stream_id)
    out_template = f"{output_path}/%(title)s.%(ext)s"

    cmd = [
        "yt-dlp",
        "-f", f"best[height<={quality}]/b[height<={quality}]/b",
        "--hls-prefer-ffmpeg",
        "--no-playlist",
        "-o", out_template,
        "--no-part",
        "-R", "3",
        "--fragment-retries", "10",
        m3u8_url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        # Find the downloaded file
        for f in os.listdir(output_path):
            fp = os.path.join(output_path, f)
            if os.path.isfile(fp) and f.endswith((".mp4", ".mkv", ".webm", ".ts")):
                return fp
    return None


def format_lecture_list(lectures: list, course_name: str = "") -> str:
    """Format lecture list for Telegram message"""
    lines = [f"📚 <b>{course_name}</b>" if course_name else "📚 <b>Course Lectures</b>",
             f"<i>Total: {len(lectures)} lectures</i>\n"]
    current_section = None
    for lec in lectures:
        if lec["section"] != current_section:
            current_section = lec["section"]
            lines.append(f"\n<b>📂 {current_section}</b>")
        title = lec["title"][:60] if lec["title"] else f"Lecture {lec['index']}"
        dur = lec.get("duration", 0)
        dur_str = f" ({dur//60}:{dur%60:02d})" if dur else ""
        lines.append(f"  <code>{lec['index']:2d}.</code> {title}{dur_str}")
    return "\n".join(lines)


def parse_range(range_str: str, max_val: int) -> list:
    """Parse '1-5,8,10-12' into list of ints"""
    result = set()
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            result.add(int(part))
    return sorted(x for x in result if 1 <= x <= max_val)
