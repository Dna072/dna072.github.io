from pathlib import Path

from worker import ffmpeg_adapter as ffmpeg


def test_should_use_mock_when_forced():
    assert ffmpeg.should_use_mock(force_mock=True, input_path=Path("/does/not/matter")) is True


def test_should_use_mock_when_input_missing(tmp_path):
    # Regardless of whether a real ffmpeg binary exists on this machine, a
    # nonexistent input file must always fall back to the mock adapter.
    missing = tmp_path / "missing.mp4"
    assert ffmpeg.should_use_mock(force_mock=False, input_path=missing) is True


def test_resolve_local_path_variants(tmp_path):
    assert ffmpeg.resolve_local_path("file:///abs/path.mp4", tmp_path) == Path("/abs/path.mp4")
    assert ffmpeg.resolve_local_path("/abs/path.mp4", tmp_path) == Path("/abs/path.mp4")
    assert ffmpeg.resolve_local_path("relative.mp4", tmp_path) == tmp_path / "relative.mp4"


def test_process_transcode_mock_writes_output(tmp_path):
    input_path = tmp_path / "in.mp4"
    output_path = tmp_path / "out" / "out.mp4"

    result = ffmpeg.process_transcode(input_path, output_path, {"codec": "h264"}, use_mock=True)

    assert output_path.exists()
    assert result.result["mock"] is True
    assert result.result["codec"] == "h264"
    assert result.output_uri == str(output_path)


def test_process_metadata_mock(tmp_path):
    result = ffmpeg.process_metadata(tmp_path / "missing.mp4", {}, use_mock=True)
    assert result.result["mock"] is True
    assert result.output_uri is None


def test_process_thumbnail_and_audio_extract_mock(tmp_path):
    thumb = ffmpeg.process_thumbnail(tmp_path / "in.mp4", tmp_path / "t.jpg", {}, use_mock=True)
    assert Path(thumb.output_uri).exists()

    audio = ffmpeg.process_audio_extract(tmp_path / "in.mp4", tmp_path / "a.mp3", {}, use_mock=True)
    assert Path(audio.output_uri).exists()
