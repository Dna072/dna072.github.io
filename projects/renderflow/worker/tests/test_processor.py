import pytest
from renderflow_common.enums import JobType
from renderflow_common.models import Job

from worker.processor import process_job


@pytest.mark.parametrize(
    "job_type,expect_output",
    [
        (JobType.TRANSCODE, True),
        (JobType.THUMBNAIL, True),
        (JobType.AUDIO_EXTRACT, True),
        (JobType.METADATA, False),
    ],
)
def test_process_job_dispatches_by_type(tmp_path, job_type, expect_output):
    job = Job(job_type=job_type, input_uri="nonexistent.mp4", params={})

    result = process_job(job, storage_root=tmp_path, force_mock=False)

    assert result.result["mock"] is True  # no real file/ffmpeg -> always mock in tests
    if expect_output:
        assert result.output_uri is not None
    else:
        assert result.output_uri is None
