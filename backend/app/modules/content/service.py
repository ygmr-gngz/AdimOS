from app.modules.content.script_generator import generate_video_script, generate_shorts_script, generate_post_content
from app.modules.content.audio_generator import generate_audio
from app.modules.content.slide_generator import create_slide, create_shorts_slide, create_post_image
from app.modules.content.video_assembler import assemble_video
from app.modules.content.youtube_uploader import upload_to_youtube, make_public
from app.modules.content.instagram_poster import post_image_to_instagram, post_reel_to_instagram
from app.modules.voice.tts import synthesize


def create_normal_video(topic: str, duration_minutes: int = 5) -> dict:
    script = generate_video_script(topic, duration_minutes)

    full_text = " ".join(s["content"] for s in script["sections"])
    audio_path = generate_audio(full_text, voice="onyx")

    slides = [
        create_slide(
            section_title=s["title"],
            content=s["content"],
            section_num=i + 1,
            total_sections=len(script["sections"]),
        )
        for i, s in enumerate(script["sections"])
    ]

    video_path = assemble_video(slides, audio_path)

    script_text = "\n\n".join(f"{s['title']}\n{s['content']}" for s in script["sections"])
    preview_text = script["sections"][0]["content"] if script["sections"] else script["title"]
    try:
        audio_base64 = synthesize(preview_text[:1200], voice="onyx")
    except Exception:
        audio_base64 = None

    return {
        "type": "video",
        "topic": topic,
        "title": script["title"],
        "description": script["description"],
        "tags": script["tags"],
        "video_path": video_path,
        "script": script_text,
        "audio_base64": audio_base64,
        "status": "pending_approval",
    }


def create_short_video(topic: str) -> dict:
    script = generate_shorts_script(topic)

    full_text = f"{script['hook']} {script['content']} {script['cta']}"
    audio_path = generate_audio(full_text, voice="nova")

    slide_path = create_shorts_slide(
        title=script["title"],
        content=script["content"],
        hook=script["hook"],
    )

    video_path = assemble_video([slide_path], audio_path)

    script_text = f"{script['hook']}\n\n{script['content']}\n\n{script['cta']}"
    try:
        audio_base64 = synthesize(full_text[:1200], voice="nova")
    except Exception:
        audio_base64 = None

    return {
        "type": "short",
        "topic": topic,
        "title": script["title"],
        "caption": script["caption"],
        "tags": script["tags"],
        "video_path": video_path,
        "script": script_text,
        "audio_base64": audio_base64,
        "status": "pending_approval",
    }


def create_post(topic: str) -> dict:
    content = generate_post_content(topic)

    points = content.get("answer_points", [])

    image_path = create_post_image(
        question=content["question"],
        answer_points=points,
        image_text=content.get("image_text", ""),
    )

    script_text = content["question"] + "\n\n" + "\n".join(f"• {p}" for p in points) + "\n\n" + content["caption"]
    try:
        audio_base64 = synthesize(script_text[:1200], voice="alloy")
    except Exception:
        audio_base64 = None

    return {
        "type": "post",
        "topic": topic,
        "title": content["title"],
        "caption": content["caption"],
        "image_path": image_path,
        "script": script_text,
        "audio_base64": audio_base64,
        "status": "pending_approval",
    }


def publish_to_youtube(content: dict) -> dict:
    result = upload_to_youtube(
        video_path=content["video_path"],
        title=content["title"],
        description=content.get("description", ""),
        tags=content.get("tags", []),
        privacy="private",
    )
    return result


def publish_to_instagram(content: dict) -> dict:
    if content["type"] == "post":
        return post_image_to_instagram(content["image_path"], content["caption"])
    elif content["type"] == "short":
        return post_reel_to_instagram(content["video_path"], content["caption"])
    return {"error": "Geçersiz içerik tipi"}
