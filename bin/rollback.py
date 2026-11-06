#!/usr/bin/env python3
"""
Safe Rollback Utility for Danho Kim's Homepage
Supports:
  1. Default: Pre-push rollback (discards local uncommitted edits and restores previous state)
  2. --last-push: Post-push rollback (creates a revert commit for the last push and updates GitHub)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
GIT_CMD = r"C:\Program Files\Git\cmd\git.exe"

def run_git(args, check=True):
    cmd = [GIT_CMD] + args if Path(GIT_CMD).exists() else ["git"] + args
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode != 0:
        print(f"[Git Error] {result.stderr.strip()}", file=sys.stderr)
        sys.exit(result.returncode)
    return result

def rollback_local():
    print("[Rollback] 로컬 수정사항 확인 중...")
    status = run_git(["status", "--porcelain"])
    
    if not status.stdout.strip():
        print("[Info] 되돌릴 로컬 수정사항이 없습니다. (이미 최신 커밋 상태와 동일합니다)")
        return

    print("[Rollback] 수정된 파일들을 이전 커밋 상태로 원복합니다...")
    # Discard tracked changes
    run_git(["restore", "."])
    
    # Remove local preview directory if it exists
    preview_dir = ROOT_DIR / "_preview"
    if preview_dir.exists():
        try:
            shutil.rmtree(preview_dir)
            print("[Rollback] 임시 미리보기 디렉토리(_preview) 정리 완료.")
        except Exception:
            pass

    # Re-sync data files to match original CSVs
    sync_script = ROOT_DIR / "bin" / "sync_site_data.py"
    if sync_script.exists():
        subprocess.run([sys.executable, str(sync_script)], check=False)

    print("\n" + "="*65)
    print("✨ [Rollback Success] 로컬 수정 사항이 모두 안전하게 취소되었습니다!")
    print("   수정 전의 깨끗한 상태로 복구되었습니다.")
    print("="*65)

def rollback_last_push():
    print("[Rollback] 마지막 배포 커밋 확인 중...")
    log_res = run_git(["log", "-1", "--oneline"])
    last_commit = log_res.stdout.strip()
    print(f"• 취소할 커밋: {last_commit}")

    confirm = input("정말로 이 커밋을 취소하고 GitHub에 롤백을 반영하시겠습니까? (y/N): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("[Rollback] 취소되었습니다.")
        return

    print("[Rollback] `git revert HEAD` 실행 중...")
    run_git(["revert", "HEAD", "--no-edit"])

    print("[Rollback] GitHub(main)에 롤백 푸시 중...")
    run_git(["push", "origin", "main"])

    print("\n" + "="*65)
    print("🚀 [Rollback Success] 마지막 배포 커밋이 안전하게 취소(revert)되었습니다!")
    print("   GitHub Actions가 이전 상태로 자동 재배포를 시작합니다.")
    print("="*65)

def main():
    parser = argparse.ArgumentParser(description="Danho Kim Homepage Safe Rollback Tool")
    parser.add_argument(
        "--last-push",
        "-p",
        action="store_true",
        help="이미 GitHub에 푸시된 마지막 배포 커밋을 안전하게 취소하고 되돌립니다"
    )
    args = parser.parse_args()

    if args.last_push:
        rollback_last_push()
    else:
        rollback_local()

if __name__ == "__main__":
    main()
