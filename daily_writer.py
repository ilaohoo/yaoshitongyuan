#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
药食同源｜一家人 · 每日文章自动化系统
策略：70%疼痛康复 + 30%食疗融合 · 部位轮换 · 角度轮换 · 开头轮换
功能：选题 → DeepSeek生成 → PushPlus推送 → 本地保存
"""

import json
import random
import requests
from datetime import datetime
from pathlib import Path

from settings import CONFIG


# ==================== 选题库 ====================

VERIFIED_TOPICS = [
    {
        "部位": "手麻",
        "病因": "腕管综合征",
        "反常识": "手麻不一定是颈椎的事，也可能是手腕的问题",
        "动作": "压手腕",
        "场景角度": "白天拿东西麻",
        "时间": "3年"
    },
    {
        "部位": "手麻",
        "病因": "颈椎压迫神经",
        "反常识": "手麻不是手的问题，是脖子的事",
        "动作": "收下巴",
        "场景角度": "半夜麻醒",
        "时间": "3年"
    },
    {
        "部位": "脚后跟",
        "病因": "足底筋膜炎",
        "反常识": "不是骨刺是筋的事，很多人搞反了",
        "动作": "滚瓶子",
        "场景角度": "早上踩地疼",
        "时间": "2年"
    },
    {
        "部位": "脚后跟",
        "病因": "足底筋膜炎",
        "反常识": "歇着不一定能好，越歇越严重",
        "动作": "踩台阶",
        "场景角度": "站久了疼",
        "时间": "2年"
    },
    {
        "部位": "膝盖",
        "病因": "髌骨软化/肌肉无力",
        "反常识": "膝盖不是用坏的，是歇坏的",
        "动作": "靠墙坐",
        "场景角度": "蹲下去起不来",
        "时间": "2年"
    },
    {
        "部位": "膝盖",
        "病因": "髌骨软化/肌肉无力",
        "反常识": "膝盖在轨道上不稳，肌肉没劲儿撑不住",
        "动作": "直抬腿",
        "场景角度": "上下楼梯疼",
        "时间": "3年"
    },
    {
        "部位": "腰痛",
        "病因": "腰肌劳损/梨状肌",
        "反常识": "腰疼不是腰的事，是屁股的事",
        "动作": "猫式伸展",
        "场景角度": "阴雨天加重",
        "时间": "5年"
    },
    {
        "部位": "腰痛",
        "病因": "腰肌劳损",
        "反常识": "越歇越没劲，肌肉不用就退化",
        "动作": "侧躺抬腿",
        "场景角度": "翻身疼",
        "时间": "3年"
    },
    {
        "部位": "肩膀",
        "病因": "肩袖损伤",
        "反常识": "肩膀疼不是肩周炎，是肌腱磨损了",
        "动作": "钟摆甩臂",
        "场景角度": "晚上疼得睡不着",
        "时间": "2年"
    },
    {
        "部位": "坐骨神经痛",
        "病因": "梨状肌压迫神经",
        "反常识": "屁股疼不是腿的事，是梨状肌太紧了",
        "动作": "4字拉伸",
        "场景角度": "走路像过电",
        "时间": "2年"
    },
]

NEW_TOPICS = [
    {
        "部位": "耳鸣",
        "病因": "颈部供血不足",
        "反常识": "耳朵嗡嗡响，问题不在耳朵在脖子",
        "动作": "压耳屏",
        "场景角度": "听不清人说话",
        "时间": "1年"
    },
    {
        "部位": "后背发紧",
        "病因": "胸椎灵活度下降",
        "反常识": "后背紧不是累的，是胸椎生锈了",
        "动作": "抱头扩胸",
        "场景角度": "沉得像背石板",
        "时间": "2年"
    },
    {
        "部位": "大腿根",
        "病因": "髋周肌肉劳损",
        "反常识": "大腿根疼不是骨头的事，是肌肉没劲儿",
        "动作": "夹枕头",
        "场景角度": "久坐迈不开腿",
        "时间": "1年"
    },
    {
        "部位": "手指关节",
        "病因": "骨关节炎/劳损",
        "反常识": "手指僵不是老了，是气血过不去",
        "动作": "搓手",
        "场景角度": "天冷拿不住东西",
        "时间": "2年"
    },
    {
        "部位": "失眠",
        "病因": "心神不宁/气血不足",
        "反常识": "睡不好不一定是脑子想太多",
        "动作": "揉耳垂",
        "场景角度": "躺下2小时睡不着",
        "时间": "3年"
    },
]

OPENING_TYPES = ["尴尬场景", "对比场景", "深夜独处场景", "公共场合场景", "家人发现场景"]

FOOD_THERAPY = [
    {
        "名称": "黄豆猪蹄汤",
        "食材": "猪蹄、黄豆、姜片",
        "做法": "猪蹄焯水，和泡好的黄豆一起炖2小时"
    },
    {
        "名称": "牛骨汤",
        "食材": "牛骨头、姜片、葱段",
        "做法": "牛骨焯水，加姜片炖2-3小时"
    },
    {
        "名称": "黑豆红枣粥",
        "食材": "黑豆、红枣、大米",
        "做法": "黑豆泡一晚，和红枣大米一起煮粥"
    },
    {
        "名称": "山药小米粥",
        "食材": "山药、小米",
        "做法": "山药去皮切块，和小米一起煮粥"
    },
]


# ==================== 核心系统 ====================

class DailyArticleSystem:
    def __init__(self):
        self.articles_dir = CONFIG.ARTICLES_DIR
        self.articles_dir.mkdir(exist_ok=True)
        self.data_file = CONFIG.DATA_FILE
        self.used_topics = self._load_used_topics()

    def _load_used_topics(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("used_topics", [])
            except:
                return []
        return []

    def _save_used_topics(self):
        data = {
            "used_topics": self.used_topics[-100:],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def select_topic(self):
        recent_used = self.used_topics[-20:]

        if random.random() < 0.7:
            available = [t for t in VERIFIED_TOPICS 
                        if t["部位"] + t["场景角度"] not in recent_used]
            if not available:
                available = VERIFIED_TOPICS
            topic = random.choice(available).copy()
            topic["类型"] = "verified"
        else:
            available = [t for t in NEW_TOPICS 
                        if t["部位"] + t["场景角度"] not in recent_used]
            if not available:
                available = NEW_TOPICS
            topic = random.choice(available).copy()
            topic["类型"] = "new"

        topic["开头类型"] = random.choice(OPENING_TYPES)
        food = random.choice(FOOD_THERAPY)
        topic["食疗名称"] = food["名称"]
        topic["食疗食材"] = food["食材"]
        topic["食疗做法"] = food["做法"]

        self.used_topics.append(topic["部位"] + topic["场景角度"])
        self._save_used_topics()
        return topic

    def generate_title(self, topic):
        """生成爆款标题（按标准公式）"""
        templates = [
            f"被{topic['部位']}折磨{topic.get('时间', '多年')}，{topic['反常识']}！社区医生教我“{topic['动作']}”，半个月好了",
            f"{topic['部位']}{topic['场景角度']}？{topic['反常识']}！社区医生教我“{topic['动作']}”，半个月稳了",
        ]
        return random.choice(templates)

    def _get_system_prompt(self):
        return """你是中老年养生账号"药食同源｜一家人"的创作者。
风格：第一人称叙事，口语化，像邻居大姐聊天。
每篇必须有：具体场景开头 + 生活化比喻 + 动作描述 + 家常食疗 + 互动提问。
禁止：科普腔、疗效词、首先其次最后。"""

    def _build_prompt(self, topic):
        return f"""
写一篇中老年「{topic['部位']}」居家康复文章。

部位：{topic['部位']}
病因：{topic['病因']}
核心动作：{topic['动作']}
反常识钩子：{topic['反常识']}
开头类型：{topic['开头类型']}
食疗：{topic['食疗名称']}（{topic['食疗食材']}）

结构：场景开头 → 症状发展 → 医生诊断+比喻 → 动作+感受 → 食疗 → 效果+互动
直接输出文章，不要大纲。
"""

    def generate_article(self, topic):
        if not CONFIG.is_configured():
            print("❌ API未配置")
            return None

        try:
            response = requests.post(
                CONFIG.DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {CONFIG.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": CONFIG.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": self._build_prompt(topic)}
                    ],
                    "temperature": 0.85,
                    "max_tokens": 2500
                },
                timeout=90
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"❌ API错误: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 生成异常: {e}")
            return None

    def save_article(self, topic, content):
        """保存文章 - 已修复路径安全问题"""
        date_str = datetime.now().strftime("%Y%m%d")
        # 替换部位名称中的非法字符
        safe_name = topic['部位'].replace("/", "_").replace("\\", "_")
        filename = f"{date_str}_{safe_name}.md"
        filepath = self.articles_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {topic['部位']} · {topic['反常识']}\n\n")
            f.write(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**选题信息**：\n")
            f.write(f"- 部位：{topic['部位']}\n")
            f.write(f"- 病因：{topic['病因']}\n")
            f.write(f"- 核心动作：{topic['动作']}\n")
            f.write(f"- 反常识钩子：{topic['反常识']}\n")
            f.write(f"- 场景角度：{topic['场景角度']}\n")
            f.write(f"- 开头类型：{topic['开头类型']}\n")
            f.write(f"- 食疗：{topic['食疗名称']}\n")
            f.write(f"- 类型：{'已验证爆款' if topic['类型']=='verified' else '潜力新赛道'}\n\n")
            f.write("---\n\n")
            f.write(content)

        return filepath

    def push_to_wechat(self, title, content):
        if not CONFIG.PUSHPLUS_TOKEN:
            print("⚠️ 未配置 PushPlus Token")
            return False

        if len(content) > 4000:
            content = content[:4000] + "\n\n...（全文已保存至本地）"

        try:
            response = requests.post(
                CONFIG.PUSHPLUS_URL,
                json={
                    "token": CONFIG.PUSHPLUS_TOKEN,
                    "title": title,
                    "content": content.replace("\n", "<br>"),
                    "template": "html"
                },
                timeout=15
            )
            result = response.json()
            if result.get("code") == 200:
                print(f"✅ 微信推送成功: {title}")
                return True
            else:
                print(f"❌ 推送失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False

    def run(self):
        print(f"\n{'='*60}")
        print(f"📝 药食同源｜一家人 · 每日文章生成")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        if not CONFIG.is_configured():
            print("❌ 请配置环境变量：DEEPSEEK_API_KEY 和 PUSHPLUS_TOKEN")
            return False

        topic = self.select_topic()
        print(f"📌 选题：{topic['部位']} - {topic['反常识']}")
        print(f"📌 动作：{topic['动作']} | 食疗：{topic['食疗名称']}")
        print(f"📌 开头类型：{topic['开头类型']}")

        print("\n⏳ 正在生成文章...")
        article = self.generate_article(topic)

        if not article:
            print("❌ 文章生成失败")
            return False

        print(f"✅ 文章生成成功（{len(article)}字）")

        # 保存文章
        filepath = self.save_article(topic, article)
        print(f"✅ 已保存：{filepath}")

        # 生成并推送标题
        title = self.generate_title(topic)
        print(f"📌 推送标题：{title}")

        push_content = f"【选题】{topic['部位']} - {topic['反常识']}\n"
        push_content += f"【动作】{topic['动作']} | 【食疗】{topic['食疗名称']}\n"
        push_content += f"{'─'*40}\n\n{article}"

        success = self.push_to_wechat(title, push_content)

        if success:
            print("✅ 全流程完成！文章已推送至微信")
        else:
            print("⚠️ 文章已生成，但微信推送失败")

        print(f"{'='*60}")
        return True


# ==================== 入口 ====================

if __name__ == "__main__":
    import sys
    system = DailyArticleSystem()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "run":
            system.run()
        elif cmd == "test":
            topic = system.select_topic()
            print(f"\n📌 测试选题预览：")
            print(f"   部位：{topic['部位']}")
            print(f"   反常识：{topic['反常识']}")
            print(f"   动作：{topic['动作']}")
            print(f"   开头类型：{topic['开头类型']}")
            print(f"   食疗：{topic['食疗名称']}")
            print(f"\n标题示例：{system.generate_title(topic)}")
        elif cmd == "reset":
            system.used_topics = []
            system._save_used_topics()
            print("✅ 选题记录已重置")
        elif cmd == "stats":
            print(f"\n📊 已使用选题数：{len(system.used_topics)}")
        else:
            print("""
用法:
  python daily_writer.py run      # 完整执行（生成+推送+保存）
  python daily_writer.py test     # 测试模式（预览选题）
  python daily_writer.py reset    # 重置选题记录
  python daily_writer.py stats    # 查看统计
""")
    else:
        system.run()
