#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蛋仔派对 关系图谱生成器（手动输入版）
版本：1.0
作者：桁数
(imgsr)
功能：手动输入中心玩家 + 好友关系，生成 D3.js 力导向图 HTML
无需联网，不调用任何生产接口
"""

import os
import sys
import json
import time
import re

# === 颜色定义 ===
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
NC = '\033[0m'

# === 关系映射（5 种） ===
REL_MAP = {
    "1": {"key": "0001", "name": "宝子",     "color": "#ff9a9e"},
    "2": {"key": "0002", "name": "最佳拍档", "color": "#6ecb63"},
    "3": {"key": "0004", "name": "挚友",     "color": "#ffd166"},
    "4": {"key": "0005", "name": "闺蜜",     "color": "#db4dff"},
    "5": {"key": "0006", "name": "死党",     "color": "#5e60ce"},
}

# === 脚本所在目录 ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(SCRIPT_DIR, "template.html")
DATA_FILE = os.path.join(SCRIPT_DIR, "egg_graph_data.json")

# === 默认输出目录（依次尝试） ===
def get_default_output_dir():
    """按优先级返回可写的默认输出目录"""
    candidates = []
    if os.path.exists("/storage/emulated/0") and os.access("/storage/emulated/0", os.W_OK):
        candidates.append("/storage/emulated/0/egg_graph")
    if os.environ.get("HOME") and os.access(os.environ["HOME"], os.W_OK):
        candidates.append(os.path.join(os.environ["HOME"], "egg_graph"))
    candidates.append(os.path.join(SCRIPT_DIR, "output"))
    for c in candidates:
        try:
            os.makedirs(c, exist_ok=True)
            if os.access(c, os.W_OK):
                return c
        except Exception:
            continue
    return SCRIPT_DIR


# ==================== 工具函数 ====================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    clear_screen()
    print(f"{CYAN}╔════════════════════════════════════════╗{NC}")
    print(f"{CYAN}║   蛋仔派对 关系图谱生成器 v1.0        ║{NC}")
    print(f"{CYAN}║   （手动输入 · 无需联网）              ║{NC}")
    print(f"{CYAN}╚════════════════════════════════════════╝{NC}")
    print()


def print_menu():
    print(f"{YELLOW}════════════════ 主菜单 ════════════════{NC}")
    print(f"{GREEN}1. 新建图谱{NC}")
    print(f"{GREEN}2. 继续编辑已有数据{NC}")
    print(f"{GREEN}3. 查看当前数据{NC}")
    print(f"{GREEN}4. 生成 HTML{NC}")
    print(f"{RED}0. 退出工具{NC}")
    print(f"{YELLOW}════════════════════════════════════════{NC}")
    print()


def pause():
    input(f"\n{CYAN}按回车键继续...{NC}")


def input_optional(prompt):
    """输入，允许留空"""
    val = input(prompt).strip()
    return val


def input_gender():
    """输入性别，返回 0/1/2"""
    while True:
        v = input("性别 [1男/2女/0保密]（回车默认0）：").strip()
        if v == "":
            return 0
        if v in ("0", "1", "2"):
            return int(v)
        print(f"{RED}无效输入，请输入 0/1/2{NC}")


def input_int(prompt, default=0):
    """输入整数，允许留空"""
    while True:
        v = input(prompt).strip()
        if v == "":
            return default
        if re.fullmatch(r"-?\d+", v):
            return int(v)
        print(f"{RED}请输入数字{NC}")


def input_avatar_choice():
    """
    头像处理：
    返回 (avatar_url, use_placeholder)
    - 输入 1：输入 URL
    - 输入 2：使用占位符
    """
    print(f"{YELLOW}头像处理方式：{NC}")
    print("  1. 输入图片 URL")
    print("  2. 使用占位符（自动生成文字头像）")
    while True:
        c = input("请选择 [1/2]（回车默认2）：").strip()
        if c == "" or c == "2":
            return "", True
        if c == "1":
            url = input("请输入头像 URL：").strip()
            if url:
                return url, False
            print(f"{YELLOW}未输入 URL，自动使用占位符{NC}")
            return "", True
        print(f"{RED}无效选择{NC}")


# ==================== 数据输入 ====================
def input_center_player():
    """输入中心玩家信息"""
    print(f"\n{YELLOW}>>> 请输入中心玩家信息{NC}\n")
    nick = input("昵称（必填）：").strip()
    while not nick:
        print(f"{RED}昵称不能为空{NC}")
        nick = input("昵称（必填）：").strip()

    avatar_url, _ = input_avatar_choice()
    level = input_int("等级（回车默认0）：", 0)
    title = input_optional("称号（回车跳过）：")
    gender = input_gender()

    return {
        "nickName": nick,
        "avatarUrl": avatar_url,
        "level": level,
        "title": title,
        "gender": gender,
    }


def input_friend(relation_key, relation_name):
    """输入一个好友，返回 dict 或 None（跳过）"""
    print(f"\n{YELLOW}--- 添加 [{relation_name}] 关系的好友 ---{NC}")
    print(f"{BLUE}（直接回车跳过该关系）{NC}")
    nick = input("好友昵称：").strip()
    if not nick:
        return None

    avatar_url, _ = input_avatar_choice()
    level = input_int("等级（回车默认0）：", 0)
    gender = input_gender()
    intimacy = input_int("亲密度（回车默认100）：", 100)

    return {
        "nickName": nick,
        "avatarUrl": avatar_url,
        "level": level,
        "gender": gender,
        "intimacy": intimacy,
        "relationKey": relation_key,
        "relationName": relation_name,
    }


def input_all_friends():
    """
    依次输入 5 种关系的好友
    每种关系可输入多个，输入空行结束该关系
    """
    friends = []
    print(f"\n{YELLOW}>>> 开始添加好友{NC}")
    print(f"{BLUE}提示：每种关系可添加多个好友，输入空行结束当前关系，全部关系可跳过{NC}")

    for rel_key in ["1", "2", "3", "4", "5"]:
        meta = REL_MAP[rel_key]
        print(f"\n{CYAN}══════ [{meta['name']}] 关系 ══════{NC}")
        while True:
            f = input_friend(meta["key"], meta["name"])
            if f is None:
                break
            friends.append(f)
            print(f"{GREEN}✅ 已添加：{f['nickName']} ({meta['name']}, 亲密度{f['intimacy']}){NC}")
            more = input(f"{YELLOW}是否继续添加 [{meta['name']}] 关系的好友？[y/n]（回车默认n）：{NC}").strip().lower()
            if more != "y":
                break

    return friends


# ==================== 数据管理 ====================
def save_data(center, friends, path=DATA_FILE):
    """保存数据到 JSON"""
    data = {"center": center, "friends": friends}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"{RED}保存数据失败: {e}{NC}")
        return False


def load_data(path=DATA_FILE):
    """从 JSON 加载数据"""
    if not os.path.exists(path):
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("center"), data.get("friends", [])
    except Exception as e:
        print(f"{RED}读取数据失败: {e}{NC}")
        return None, None


def show_data(center, friends):
    """展示当前数据"""
    if not center:
        print(f"{YELLOW}暂无数据{NC}")
        return
    print(f"\n{CYAN}════════════ 当前数据 ════════════{NC}\n")
    print(f"{GREEN}【中心玩家】{NC}")
    print(f"  昵称：{center.get('nickName', '')}")
    print(f"  头像：{center.get('avatarUrl') or '（占位符）'}")
    print(f"  等级：{center.get('level', 0)}")
    print(f"  称号：{center.get('title') or '（无）'}")
    gmap = {0: "保密", 1: "男", 2: "女"}
    print(f"  性别：{gmap.get(center.get('gender', 0), '保密')}")

    print(f"\n{GREEN}【好友列表】共 {len(friends)} 人{NC}")
    if not friends:
        print(f"  {YELLOW}（暂无好友）{NC}")
        return
    # 按关系分组
    groups = {}
    for f in friends:
        groups.setdefault(f.get("relationKey", ""), []).append(f)
    for rel_key in ["0001", "0002", "0004", "0005", "0006"]:
        group = groups.get(rel_key, [])
        if not group:
            continue
        rel_name = next((m["name"] for m in REL_MAP.values() if m["key"] == rel_key), rel_key)
        print(f"\n  {CYAN}[{rel_name}] {len(group)} 人：{NC}")
        for f in group:
            print(f"    - {f['nickName']} | 等级{f.get('level',0)} | 亲密度{f.get('intimacy',0)} | 性别{gmap.get(f.get('gender',0),'保密')}")


def edit_loop(center, friends):
    """全部输完后，允许用户返回修改"""
    while True:
        show_data(center, friends)
        print(f"\n{YELLOW}════════════ 编辑选项 ════════════{NC}")
        print("  1. 修改中心玩家信息")
        print("  2. 修改某个好友")
        print("  3. 删除某个好友")
        print("  4. 添加好友")
        print("  5. 完成，保存数据")
        print("  0. 放弃修改，返回主菜单")
        c = input("请选择：").strip()

        if c == "1":
            center = input_center_player()
        elif c == "2":
            if not friends:
                print(f"{YELLOW}暂无好友{NC}")
                continue
            for i, f in enumerate(friends, 1):
                print(f"  {i}. {f['nickName']} ({f.get('relationName','')})")
            try:
                idx = int(input("请输入要修改的好友序号：").strip()) - 1
                if 0 <= idx < len(friends):
                    print(f"{YELLOW}重新输入该好友信息（回车保留原值）{NC}")
                    old = friends[idx]
                    nick = input(f"昵称（{old['nickName']}）：").strip() or old["nickName"]
                    print(f"头像当前：{old.get('avatarUrl') or '（占位符）'}")
                    change_avatar = input("是否修改头像？[y/n]（回车默认n）：").strip().lower()
                    if change_avatar == "y":
                        avatar_url, _ = input_avatar_choice()
                    else:
                        avatar_url = old.get("avatarUrl", "")
                    level = input_int(f"等级（{old.get('level',0)}）：", old.get("level", 0))
                    gender_in = input(f"性别 [1男/2女/0保密]（{old.get('gender',0)}）：").strip()
                    gender = int(gender_in) if gender_in in ("0","1","2") else old.get("gender", 0)
                    intimacy = input_int(f"亲密度（{old.get('intimacy',100)}）：", old.get("intimacy", 100))
                    friends[idx] = {
                        "nickName": nick,
                        "avatarUrl": avatar_url,
                        "level": level,
                        "gender": gender,
                        "intimacy": intimacy,
                        "relationKey": old.get("relationKey", "0001"),
                        "relationName": old.get("relationName", "宝子"),
                    }
                    print(f"{GREEN}✅ 已修改{NC}")
                else:
                    print(f"{RED}序号无效{NC}")
            except ValueError:
                print(f"{RED}输入无效{NC}")
        elif c == "3":
            if not friends:
                print(f"{YELLOW}暂无好友{NC}")
                continue
            for i, f in enumerate(friends, 1):
                print(f"  {i}. {f['nickName']} ({f.get('relationName','')})")
            try:
                idx = int(input("请输入要删除的好友序号：").strip()) - 1
                if 0 <= idx < len(friends):
                    removed = friends.pop(idx)
                    print(f"{GREEN}✅ 已删除：{removed['nickName']}{NC}")
                else:
                    print(f"{RED}序号无效{NC}")
            except ValueError:
                print(f"{RED}输入无效{NC}")
        elif c == "4":
            new_friends = input_all_friends()
            friends.extend(new_friends)
            print(f"{GREEN}✅ 已添加 {len(new_friends)} 位好友{NC}")
        elif c == "5":
            save_data(center, friends)
            print(f"{GREEN}✅ 数据已保存到 {DATA_FILE}{NC}")
            pause()
            return center, friends
        elif c == "0":
            return center, friends
        else:
            print(f"{RED}无效选项{NC}")


# ==================== HTML 生成 ====================
def choose_output_dir():
    """让用户选择输出目录"""
    print(f"\n{YELLOW}请选择输出位置：{NC}")
    print("  1. 默认目录")
    print("  2. 当前脚本所在文件夹")
    print("  3. 自定义路径")
    while True:
        c = input("请选择 [1/2/3]（回车默认1）：").strip()
        if c == "" or c == "1":
            return get_default_output_dir()
        if c == "2":
            return SCRIPT_DIR
        if c == "3":
            path = input("请输入输出目录路径：").strip()
            if not path:
                print(f"{RED}路径不能为空{NC}")
                continue
            return path
        print(f"{RED}无效选择{NC}")


def build_html(center, friends, template_path, output_path):
    """
    读取模板，替换占位符，写入 HTML
    返回 (success, message)
    """
    if not os.path.exists(template_path):
        return False, f"模板文件不存在：{template_path}"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        return False, f"读取模板失败：{e}"

    # 构造 centerUser JS 对象
    center_js = {
        "id": "center",
        "name": center.get("nickName", "未知"),
        "avatar": center.get("avatarUrl", ""),
        "level": center.get("level", 0),
        "gender": {0: "保密", 1: "男", 2: "女"}.get(center.get("gender", 0), "保密"),
        "title": center.get("title", ""),
    }

    # 构造 friendRelations（按 relationKey 分组）
    relations = {}
    for f in friends:
        rk = f.get("relationKey", "0001")
        relations.setdefault(rk, []).append({
            "id": f"f{f.get('nickName','')}_{f.get('intimacy',0)}",
            "nickName": f.get("nickName", "未知"),
            "avatarUrl": f.get("avatarUrl", ""),
            "level": f.get("level", 0),
            "gender": f.get("gender", 0),
            "intimacy": f.get("intimacy", 0),
        })

    center_js_str = json.dumps(center_js, ensure_ascii=False)
    relations_str = json.dumps(relations, ensure_ascii=False)

    # 中心头像兜底
    center_avatar = center.get("avatarUrl") or f"https://ui-avatars.com/api/?name={center.get('nickName','玩家')}&background=random&size=80"
    center_fallback = f"https://ui-avatars.com/api/?name={center.get('nickName','玩家')}&background=random&size=80"

    html = html.replace("{{TITLE}}", f"{center.get('nickName','未知')}的关系图谱")
    html = html.replace("{{CENTER_USER}}", center_js_str)
    html = html.replace("{{FRIEND_RELATIONS}}", relations_str)
    html = html.replace("{{CENTER_NAME}}", center.get("nickName", "未知"))
    html = html.replace("{{CENTER_TITLE}}", center.get("title", "") or "无称号")
    html = html.replace("{{CENTER_AVATAR}}", center_avatar)
    html = html.replace("{{CENTER_FALLBACK}}", center_fallback)

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return True, output_path
    except Exception as e:
        return False, str(e)


def generate_html(center, friends):
    """生成 HTML，带降级措施"""
    if not center:
        print(f"{RED}❌ 请先输入中心玩家信息{NC}")
        pause()
        return

    # 选择输出目录
    output_dir = choose_output_dir()

    # 文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[\\/:*?"<>|]', "_", center.get("nickName", "未知"))
    filename = f"关系图谱_{safe_name}_{timestamp}.html"
    output_path = os.path.join(output_dir, filename)

    print(f"\n{BLUE}正在生成 HTML...{NC}")

    # 尝试生成
    success, msg = build_html(center, friends, TEMPLATE_FILE, output_path)

    # 降级：默认目录失败 → 当前文件夹
    if not success:
        print(f"{YELLOW}⚠️ 输出到 {output_dir} 失败：{msg}{NC}")
        print(f"{BLUE}尝试降级到当前脚本文件夹...{NC}")
        output_path = os.path.join(SCRIPT_DIR, filename)
        success, msg = build_html(center, friends, TEMPLATE_FILE, output_path)

    # 再降级：当前文件夹失败 → 脚本同目录下的 output
    if not success:
        print(f"{YELLOW}⚠️ 降级失败：{msg}{NC}")
        fallback_dir = os.path.join(SCRIPT_DIR, "output")
        try:
            os.makedirs(fallback_dir, exist_ok=True)
        except Exception:
            pass
        output_path = os.path.join(fallback_dir, filename)
        success, msg = build_html(center, friends, TEMPLATE_FILE, output_path)

    # 最终结果
    print()
    if success:
        friend_count = len(friends)
        rel_count = len(set(f.get("relationKey") for f in friends))
        print(f"{GREEN}════════════════════════════════════════{NC}")
        print(f"{GREEN}✅ 关系图谱生成成功！{NC}")
        print(f"{CYAN}📁 输出文件: {output_path}{NC}")
        print(f"{CYAN}📊 好友数量: {friend_count} 人（{rel_count} 种关系）{NC}")
        print(f"{GREEN}════════════════════════════════════════{NC}")
        print(f"\n{YELLOW}💡 在浏览器中打开此HTML文件即可查看力导向图{NC}")
    else:
        print(f"{RED}════════════════════════════════════════{NC}")
        print(f"{RED}❌ 关系图谱生成失败{NC}")
        print(f"{RED}   原因: {msg}{NC}")
        print(f"{RED}════════════════════════════════════════{NC}")
        print(f"{YELLOW}💡 请检查模板文件是否存在：{TEMPLATE_FILE}{NC}")

    pause()


# ==================== 主程序 ====================
def main():
    center = None
    friends = []

    while True:
        print_header()
        print_menu()
        choice = input("请选择功能：").strip()

        if choice == "1":
            # 新建
            center = input_center_player()
            friends = input_all_friends()
            print(f"\n{GREEN}✅ 输入完成！共 {len(friends)} 位好友{NC}")
            # 进入编辑循环
            center, friends = edit_loop(center, friends)
        elif choice == "2":
            c, f = load_data()
            if c is None:
                print(f"{YELLOW}未找到已保存的数据{NC}")
                pause()
                continue
            center, friends = c, f
            print(f"{GREEN}✅ 已加载数据：{center.get('nickName','')} + {len(friends)} 位好友{NC}")
            pause()
            center, friends = edit_loop(center, friends)
        elif choice == "3":
            show_data(center, friends)
            pause()
        elif choice == "4":
            generate_html(center, friends)
        elif choice == "0":
            print(f"\n{GREEN}感谢使用蛋仔派对关系图谱生成器！{NC}")
            sys.exit(0)
        else:
            print(f"{RED}无效选项{NC}")
            time.sleep(0.3)


if __name__ == "__main__":
    main()