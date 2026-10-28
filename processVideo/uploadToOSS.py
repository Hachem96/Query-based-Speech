"""
Upload the processed video tree (<root>/<Year>/<VideoName>/...) to Alibaba Cloud OSS, skipping
the derived audio and the embeddings the app doesn't use.

    python -m processVideo.uploadToOSS --source "/Volumes/TOSHIBA EXT/Personal/PromptSpeech/videosPerYear" --dry-run
    python -m processVideo.uploadToOSS --source "/Volumes/TOSHIBA EXT/Personal/PromptSpeech/videosPerYear"

Object keys are "<basename of --source>/<Year>/<VideoName>/<file>", which is the same relative path
addNewVideo.py stores in the DB, so to_media_url() + MEDIA_BASE_URL resolve to the uploaded object.
Rerunning skips objects that already exist with the same size; an interrupted large upload resumes
from its last part (checkpoints live in ~/.py-oss-upload).

Needs `pip install oss2` (not for --dry-run). Reads OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET, plus
OSS_ENDPOINT, OSS_REGION and OSS_BUCKET unless the matching flags are given.
"""
import argparse
import mimetypes
import os
import re
import sys
from collections import defaultdict

# What not to upload. Edit these lists to change the rules.
EXCLUDED_DIR_PREFIXES = ("AudioSegments_",)    # whole folder skipped, never walked
EXCLUDED_EXTENSIONS = (".wav",)                # <VideoName>.wav
EXCLUDED_FILE_NAMES = {
    "jinaV3_embedding.npy",
    "omarelshehy_embedding.npy",
    "Qwen-0.6B_embedding.npy",                 # exact names: qwen3.7-text-embedding_embedding.npy is kept
    ".DS_Store",
}
EXCLUDED_NAME_PREFIXES = ("._",)               # macOS AppleDouble files on exFAT/NTFS drives

CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",       # Arabic transcripts: without a charset browsers garble them
    ".json": "application/json; charset=utf-8",
    ".npy": "application/octet-stream",
}

DEFAULT_BUCKET = "es2alsayed-media"
MULTIPART_THRESHOLD = 100 * 1024 * 1024
PART_SIZE = 10 * 1024 * 1024
UPLOAD_THREADS = 4
YEAR_DIR = re.compile(r"^\d{4}$")


def human_size(nbytes):
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024 or unit == "GB":
            return f"{nbytes:.0f} {unit}" if unit == "B" else f"{nbytes:.1f} {unit}"
        nbytes /= 1024


def exclusion_reason(name):
    """Return the rule that excludes this file name, or None if it should be uploaded."""
    if name in EXCLUDED_FILE_NAMES:
        return name
    if name.startswith(EXCLUDED_NAME_PREFIXES):
        return "._* (AppleDouble)"
    ext = os.path.splitext(name)[1].lower()
    if ext in EXCLUDED_EXTENSIONS:
        return f"*{ext}"
    return None


def folder_stats(path):
    count, total = 0, 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            count += 1
            total += os.path.getsize(os.path.join(dirpath, name))
    return count, total


def collect_files(source, prefix, measure_excluded):
    """
    Walk source and split its files into the ones to upload and the excluded ones.
    Output
        keep: list of (local path, object key, size) in walk order
        excluded: {rule: [file count, bytes]}; folder rules only get sizes when measure_excluded
    """
    keep = []
    excluded = defaultdict(lambda: [0, 0])
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames.sort()
        kept_dirs = []
        for d in dirnames:
            matched = next((p for p in EXCLUDED_DIR_PREFIXES if d.startswith(p)), None)
            if matched is None:
                kept_dirs.append(d)
                continue
            stats = excluded[f"{matched}* folders"]
            if measure_excluded:
                count, total = folder_stats(os.path.join(dirpath, d))
                stats[0] += count
                stats[1] += total
        dirnames[:] = kept_dirs  # prune in place so os.walk never descends into them

        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            size = os.path.getsize(path)
            reason = exclusion_reason(name)
            if reason is not None:
                excluded[reason][0] += 1
                excluded[reason][1] += size
                continue
            rel = os.path.relpath(path, source).replace(os.sep, "/")
            keep.append((path, f"{prefix}/{rel}" if prefix else rel, size))
    return keep, excluded


def print_report(keep, excluded, measured):
    print("Excluded:")
    for reason, (count, total) in sorted(excluded.items()):
        if reason.endswith(" folders") and not measured:
            print(f"  {reason:<40} (not measured; use --dry-run)")
        else:
            print(f"  {reason:<40} {count:>6} files  {human_size(total):>10}")

    by_ext = defaultdict(lambda: [0, 0])
    for path, _, size in keep:
        ext = os.path.splitext(path)[1].lower() or "(none)"
        by_ext[ext][0] += 1
        by_ext[ext][1] += size
    print("To upload:")
    for ext, (count, total) in sorted(by_ext.items()):
        print(f"  {ext:<40} {count:>6} files  {human_size(total):>10}")
    print(f"  {'TOTAL':<40} {len(keep):>6} files  {human_size(sum(s for _, _, s in keep)):>10}")

    print("First keys (must match the DB paths, e.g. SELECT \"linkToMP4\" FROM \"Video\" LIMIT 1):")
    for _, key, _ in keep[:3]:
        print(f"  {key}")


def connect_bucket(bucket_name, endpoint, region):
    import oss2
    from oss2.credentials import EnvironmentVariableCredentialsProvider

    missing = [v for v in ("OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET") if not os.getenv(v)]
    if not endpoint:
        missing.append("OSS_ENDPOINT (or --endpoint)")
    if not region:
        missing.append("OSS_REGION (or --region)")
    if missing:
        sys.exit("Missing configuration: " + ", ".join(missing))

    auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())
    return oss2.Bucket(auth, endpoint, bucket_name, region=region)


def list_remote_sizes(bucket, prefix):
    import oss2

    listing_prefix = f"{prefix}/" if prefix else ""
    return {obj.key: obj.size for obj in oss2.ObjectIterator(bucket, prefix=listing_prefix, max_keys=1000)}


def upload_files(bucket, keep, remote_sizes):
    import oss2

    failed = []
    uploaded = skipped = 0
    total = len(keep)
    for i, (path, key, size) in enumerate(keep, start=1):
        line = f"[{i}/{total}] {key}  {human_size(size)}"
        if remote_sizes.get(key) == size:
            skipped += 1
            print(f"{line}  skipped")
            continue

        ext = os.path.splitext(path)[1].lower()
        content_type = CONTENT_TYPES.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"

        def progress(consumed, total_bytes, line=line):
            if total_bytes:
                print(f"\r{line}  {consumed * 100 // total_bytes}%", end="", flush=True)

        try:
            oss2.resumable_upload(
                bucket, key, path,
                headers={"Content-Type": content_type},
                multipart_threshold=MULTIPART_THRESHOLD,
                part_size=PART_SIZE,
                num_threads=UPLOAD_THREADS,
                progress_callback=progress if size >= MULTIPART_THRESHOLD else None,
            )
        except Exception as e:
            failed.append((key, e))
            print(f"\r{line}  FAILED: {e}")
            continue
        uploaded += 1
        print(f"\r{line}  uploaded")

    print(f"\nDone: {uploaded} uploaded, {skipped} skipped, {len(failed)} failed.")
    for key, e in failed:
        print(f"  FAILED {key}: {e}")
    return not failed


def main():
    parser = argparse.ArgumentParser(description="Upload the video tree to Alibaba Cloud OSS.")
    parser.add_argument("--source", required=True, help="folder that holds the <Year>/ folders, e.g. .../videosPerYear")
    parser.add_argument("--prefix", help="key prefix (default: the --source folder name)")
    parser.add_argument("--bucket", default=os.getenv("OSS_BUCKET", DEFAULT_BUCKET))
    parser.add_argument("--endpoint", default=os.getenv("OSS_ENDPOINT"), help="e.g. https://oss-me-central-1.aliyuncs.com")
    parser.add_argument("--region", default=os.getenv("OSS_REGION"), help="e.g. me-central-1")
    parser.add_argument("--dry-run", action="store_true", help="list what would be uploaded; no OSS access")
    args = parser.parse_args()

    source = os.path.normpath(os.path.expanduser(args.source))
    if not os.path.isdir(source):
        sys.exit(f"'{source}' is not a directory.")
    if not any(YEAR_DIR.match(d) and os.path.isdir(os.path.join(source, d)) for d in os.listdir(source)):
        sys.exit(f"'{source}' has no <Year>/ subfolders. Point --source at the folder that holds them "
                 "(e.g. .../videosPerYear), otherwise every key gets the wrong prefix.")
    prefix = (os.path.basename(source) if args.prefix is None else args.prefix).strip("/")

    keep, excluded = collect_files(source, prefix, measure_excluded=args.dry_run)
    print_report(keep, excluded, measured=args.dry_run)
    if args.dry_run:
        return

    bucket = connect_bucket(args.bucket, args.endpoint, args.region)
    print(f"\nUploading to oss://{args.bucket}/{prefix}/ via {args.endpoint}\n")
    remote_sizes = list_remote_sizes(bucket, prefix)
    if not upload_files(bucket, keep, remote_sizes):
        sys.exit(1)


if __name__ == "__main__":
    main()
