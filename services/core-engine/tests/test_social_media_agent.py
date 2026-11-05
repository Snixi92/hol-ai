import pytest
from src.services.social_media_agent import SocialMediaAgentService


def test_create_linkedin_post():
    res = SocialMediaAgentService.create_post(
        platform="LinkedIn",
        topic="Annonce Gemini 1 milliard d'utilisateurs et 150M d'images par jour",
        tone_style="expert",
        scheduled_time="Jeudi 21 août à 08h00"
    )

    assert res["status"] in ["DRAFT", "SCHEDULED", "PUBLISHED"]
    assert res["platform"] == "LinkedIn"
    assert "Gemini" in res["content"] or "milliard" in res["content"]
    assert res["scheduled_time"] == "Jeudi 21 août à 08h00"
    assert len(res["hashtags"]) > 0


def test_publish_social_post():
    res = SocialMediaAgentService.publish_post(
        platform="LinkedIn",
        post_id="post-123"
    )
    assert res["status"] == "PUBLISHED"
    assert "LinkedIn" in res["message"]


def test_generate_or_search_media():
    res = SocialMediaAgentService.generate_or_search_media("Sundar Pichai conférence Google IO")
    assert res["status"] == "READY"
    assert "Sundar Pichai" in res["title"]
    assert res["image_url"].startswith("http") or res["image_url"].startswith("/")
