#!/usr/bin/env python3
"""
启明志愿 — AI 高考志愿顾问，模型无关、支持实时搜索、结构化槽位采集。

Usage:
  python agent.py                    # 交互式对话
  python agent.py --model qwen-plus   # 指定模型
  python agent.py --no-search         # 禁用搜索
"""

from __future__ import annotations

import argparse

from advisor_core import CONFIG, GaokaoAdvisor, resolve_config, slots_summary, test_connection


def read_clipboard():
    """读取 Windows 剪贴板文本。"""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(13):  # CF_UNICODETEXT
            data = win32clipboard.GetClipboardData(13)
            win32clipboard.CloseClipboard()
            return data
        win32clipboard.CloseClipboard()
    except Exception:
        pass
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="启明志愿 CLI")
    parser.add_argument("--model", help="临时指定模型名，例如 qwen-plus")
    parser.add_argument("--no-search", action="store_true", help="禁用联网搜索")
    return parser.parse_args()


def main():
    args = parse_args()
    config = resolve_config(model_override=args.model, enable_search=False if args.no_search else None)

    print("=" * 60)
    print("  启明志愿 · AI 高考志愿顾问")
    print(f"  模型: {config['model']}")
    print(f"  搜索: {'开' if config['enable_search'] else '关'}")
    print("=" * 60)

    if not config["api_key"]:
        print("\n❌ 未检测到 API Key！")
        print("   请复制 .env.example 为 .env，并填入你的 LLM_API_KEY。")
        print("   如果使用 cliproxyapi / sub2api，请同时填写 LLM_BASE_URL 和 LLM_MODEL。")
        print()
        print("   示例：")
        print("   LLM_API_KEY=你的key")
        print("   LLM_BASE_URL=https://你的代理服务地址/v1")
        print("   LLM_MODEL=你的模型名")
        input("\n   按回车退出...")
        return

    print("  正在测试 API 连接...", end=" ", flush=True)
    ok, msg = test_connection(config)
    if ok:
        print("[OK] 连接成功")
    else:
        print(f"[X] 连接失败: {msg[:200]}")
        print()
        if "401" in msg or "Authentication" in msg:
            print("   → Key 无效或格式错误。检查 Key 是否完整，前后有没有空格。")
        elif "402" in msg or "Insufficient" in msg or "Balance" in msg:
            print("   → 账户余额不足，去 API 平台检查额度。")
        elif "403" in msg or "Forbidden" in msg:
            print("   → Key 没有权限，或上游服务拒绝访问。")
        elif "404" in msg or "Not Found" in msg:
            print("   → 接口地址或模型名不对。检查 LLM_BASE_URL 和 LLM_MODEL。")
        elif "timeout" in msg.lower() or "connect" in msg.lower():
            print("   → 网络连不上 API 服务器。检查网络或代理地址。")
        else:
            print("   检查 .env 中 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL。")
        input("\n   按回车退出...")
        return

    print("=" * 60)
    print("  命令: /paste 粘贴 | /slots 信息 | /reset 重置 | /quit 退出")
    print("  直接描述你的情况，我会帮你分析。")
    print("=" * 60)
    print()

    advisor = GaokaoAdvisor(config=config)

    while True:
        try:
            user_input = input("\n[You] 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("再见！")
            break
        if user_input == "/reset":
            advisor.reset()
            print("[OK] 已重置对话和信息采集")
            continue
        if user_input == "/slots":
            print(slots_summary(advisor.slots))
            continue
        if user_input == "/paste":
            cb = read_clipboard()
            if cb and cb.strip():
                user_input = " ".join(cb.strip().split("\n"))
                print(f"📋 剪贴板已读取 ({len(user_input)}字)")
                print(f"📋 内容: {user_input[:100]}...")
            else:
                print("📋 剪贴板为空或无法读取")
                continue

        print("\n🤖 顾问: ", end="", flush=True)
        result = advisor.chat(user_input)
        print(result["reply"])


if __name__ == "__main__":
    main()
