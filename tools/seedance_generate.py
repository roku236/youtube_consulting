#!/usr/bin/env python3
"""BytePlus ModelArk の Seedance 2.5 で動画を生成して保存するスクリプト。

使い方:
    export ARK_API_KEY="xxxxxxxx"
    python tools/seedance_generate.py "夕暮れの海辺を歩く柴犬、シネマティック" \
        --ratio 16:9 --duration 5 --resolution 1080p -o output.mp4

    # 画像を最初のフレームとして使う (Image-to-Video)
    python tools/seedance_generate.py "カメラがゆっくりズームイン" \
        --image https://example.com/first.png -o i2v.mp4

外部ライブラリ不要 (Python 3.8+ 標準ライブラリのみ)。
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://ark.ap-southeast.bytepluses.com/api/v3/contents/generations/tasks"
MODEL = "dreamina-seedance-2-5-260628"

TERMINAL_OK = {"succeeded"}
TERMINAL_NG = {"failed", "cancelled", "expired"}


def get_api_key() -> str:
    key = os.environ.get("ARK_API_KEY")
    if not key:
        sys.exit("エラー: 環境変数 ARK_API_KEY が設定されていません。")
    return key


def request_json(method: str, url: str, api_key: str, body: dict | None = None,
                 retries: int = 3) -> dict:
    """JSON API を呼び出す。429/5xx とネットワークエラーは指数バックオフでリトライ。"""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            if (e.code == 429 or e.code >= 500) and attempt < retries:
                wait = 2 ** (attempt + 1)
                print(f"  HTTP {e.code}、{wait}秒後にリトライします...", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"APIエラー (HTTP {e.code}): {detail}")
        except urllib.error.URLError as e:
            if attempt < retries:
                wait = 2 ** (attempt + 1)
                print(f"  接続エラー ({e.reason})、{wait}秒後にリトライします...", file=sys.stderr)
                time.sleep(wait)
                continue
            sys.exit(f"接続エラー: {e.reason}")
    raise RuntimeError("unreachable")


def image_to_url(value: str) -> str:
    """URL ならそのまま、ローカルファイルなら data URI (Base64) に変換。"""
    if value.startswith(("http://", "https://", "data:")):
        return value
    path = Path(value)
    if not path.is_file():
        sys.exit(f"エラー: 画像ファイルが見つかりません: {value}")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_payload(args: argparse.Namespace) -> dict:
    content: list[dict] = [{"type": "text", "text": args.prompt}]
    if args.image:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_to_url(args.image)},
            "role": "first_frame",
        })
    if args.last_image:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_to_url(args.last_image)},
            "role": "last_frame",
        })

    payload: dict = {"model": args.model, "content": content}
    # 指定されたパラメータだけ送る (未指定ならモデルのデフォルト)
    optional = {
        "ratio": args.ratio,
        "duration": args.duration,
        "resolution": args.resolution,
        "seed": args.seed,
        "generate_audio": args.generate_audio,
        "watermark": args.watermark,
        "camera_fixed": args.camera_fixed,
    }
    payload.update({k: v for k, v in optional.items() if v is not None})
    return payload


def create_task(api_key: str, payload: dict) -> str:
    result = request_json("POST", API_URL, api_key, payload)
    task_id = result.get("id")
    if not task_id:
        sys.exit(f"タスクIDが返りませんでした: {json.dumps(result, ensure_ascii=False)}")
    return task_id


def wait_for_task(api_key: str, task_id: str, interval: float, timeout: float) -> dict:
    url = f"{API_URL}/{task_id}"
    start = time.time()
    last_status = None
    while True:
        task = request_json("GET", url, api_key)
        status = task.get("status")
        elapsed = int(time.time() - start)
        if status != last_status:
            print(f"  [{elapsed:>4}s] status: {status}")
            last_status = status
        if status in TERMINAL_OK:
            return task
        if status in TERMINAL_NG:
            err = task.get("error") or {}
            sys.exit(f"生成失敗 ({status}): {err.get('code', '')} {err.get('message', '')}".strip())
        if time.time() - start > timeout:
            sys.exit(f"タイムアウト: {timeout}秒以内に完了しませんでした (task_id={task_id})")
        time.sleep(interval)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=300) as resp, open(tmp, "wb") as f:
        while chunk := resp.read(1 << 20):
            f.write(chunk)
    tmp.replace(dest)


def str2bool(v: str) -> bool:
    if v.lower() in ("true", "1", "yes", "on"):
        return True
    if v.lower() in ("false", "0", "no", "off"):
        return False
    raise argparse.ArgumentTypeError("true/false を指定してください")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seedance 2.5 (BytePlus ModelArk) で動画を生成")
    p.add_argument("prompt", help="動画のプロンプト")
    p.add_argument("-o", "--output", help="保存先 (既定: seedance_<task_id>.mp4)")
    p.add_argument("--model", default=MODEL, help=f"モデルID (既定: {MODEL})")
    p.add_argument("--image", help="最初のフレーム画像 (URL またはローカルパス)")
    p.add_argument("--last-image", help="最後のフレーム画像 (URL またはローカルパス)")
    p.add_argument("--ratio", help="アスペクト比 例: 16:9, 9:16, 1:1, adaptive")
    p.add_argument("--duration", type=int, help="動画の秒数 例: 5, 10")
    p.add_argument("--resolution", help="解像度 例: 480p, 720p, 1080p")
    p.add_argument("--seed", type=int, help="シード値")
    p.add_argument("--generate-audio", type=str2bool, help="音声も生成するか (true/false)")
    p.add_argument("--watermark", type=str2bool, help="透かしを付けるか (true/false)")
    p.add_argument("--camera-fixed", type=str2bool, help="カメラを固定するか (true/false)")
    p.add_argument("--interval", type=float, default=10, help="ポーリング間隔秒 (既定: 10)")
    p.add_argument("--timeout", type=float, default=1800, help="最大待機秒 (既定: 1800)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    api_key = get_api_key()

    payload = build_payload(args)
    print(f"タスク作成中... (model: {args.model})")
    task_id = create_task(api_key, payload)
    print(f"タスクID: {task_id}")

    print("生成完了を待っています...")
    task = wait_for_task(api_key, task_id, args.interval, args.timeout)

    video_url = (task.get("content") or {}).get("video_url")
    if not video_url:
        sys.exit(f"video_url が見つかりません: {json.dumps(task, ensure_ascii=False)}")

    out = Path(args.output or f"seedance_{task_id}.mp4")
    print("ダウンロード中...")
    download(video_url, out)
    print(f"保存しました: {out.resolve()}")

    usage = task.get("usage")
    if usage:
        print(f"usage: {json.dumps(usage, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
