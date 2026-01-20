from backend.tests.evaluation.batch_email_downloader import download_emails_batched

download_emails_batched(
    out_dir="backend/tests/evaluation/data/raw_emails_150",
    target_count=150,
    batch_count=5,
    batch_size=30,
    fetch_chunk_size=25,
    secrets_path="secrets.json",
)
