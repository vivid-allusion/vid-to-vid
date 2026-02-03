"""Tests for motion control input parsing."""

import pytest
from pathlib import Path
from src.processing.input_discovery import parse_motion_control_job


class TestParseMotionControlJob:
    """Tests for parse_motion_control_job function."""

    def test_parse_valid_motion_control_job(self, tmp_path):
        """Test parsing a valid motion control markdown file."""
        content = """Santa doing Tai Chi in winter landscape.

![image](https://replicate.delivery/pbxt/santa.png)

![video](https://replicate.delivery/pbxt/taichi.mp4)"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        job = parse_motion_control_job(md_file)

        assert job.prompt == "Santa doing Tai Chi in winter landscape."
        assert job.image_url == "https://replicate.delivery/pbxt/santa.png"
        assert job.video_url == "https://replicate.delivery/pbxt/taichi.mp4"
        assert job.markdown_file == md_file

    def test_parse_missing_lines(self, tmp_path):
        """Test with insufficient lines."""
        content = "Only one line"
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="must have at least 5 lines"):
            parse_motion_control_job(md_file)

    def test_parse_empty_prompt(self, tmp_path):
        """Test with empty prompt line."""
        content = """

![image](https://replicate.delivery/pbxt/santa.png)

![video](https://replicate.delivery/pbxt/taichi.mp4)"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="prompt.*is empty"):
            parse_motion_control_job(md_file)

    def test_parse_missing_image(self, tmp_path):
        """Test with missing image URL."""
        content = """Valid prompt

Some other text

![video](https://replicate.delivery/pbxt/taichi.mp4)"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="image URL.*is empty"):
            parse_motion_control_job(md_file)

    def test_parse_missing_video(self, tmp_path):
        """Test with missing video URL."""
        content = """Valid prompt

![image](https://replicate.delivery/pbxt/santa.png)

Some other text"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="video URL.*is empty"):
            parse_motion_control_job(md_file)

    def test_parse_invalid_image_format(self, tmp_path):
        """Test with invalid image markdown format."""
        content = """Valid prompt

Not a markdown image

![video](https://replicate.delivery/pbxt/taichi.mp4)"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="markdown image format"):
            parse_motion_control_job(md_file)

    def test_parse_invalid_video_format(self, tmp_path):
        """Test with invalid video markdown format."""
        content = """Valid prompt

![image](https://replicate.delivery/pbxt/santa.png)

Not a video URL"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        with pytest.raises(ValueError, match="markdown video format"):
            parse_motion_control_job(md_file)
