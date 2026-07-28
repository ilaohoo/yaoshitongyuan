#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
药食同源｜一家人 · 每日文章自动化系统
策略：70%疼痛康复 + 30%食疗融合 · 部位轮换 · 角度轮换 · 开头轮换
功能：选题 → DeepSeek生成 → PushPlus推送 → 本地保存
"""

import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path

# 导入配置
from settings import CONFIG


# ==================== 选题库 ====================

# 已验证爆款赛道（展现 > 10,000）—— 占比 70%
VERIFIED_TOPICS = [
    {
        "部位": "手麻",
        "病因": "腕管综合征（神经压迫）",
        "反常识": "手麻不一定是颈椎的事，也可能是手腕的问题",
        "动作": "压手腕",
        "场景角度": "白天拿东西麻"
    },
    {
        "部位": "手麻",
        "病因": "颈椎压迫神经",
        "反常识": "手麻不是手的问题，是脖子的事",
        "动作": "收下巴",
        "场景角度": "半夜麻醒"
    },
    {
        "部位": "脚后跟",
        "病因": "足底筋膜炎",
        "反常识": "歇着不一定能好，越歇越严重",
        "动作": "踩台阶",
        "场景角度": "站久了疼"
    },
    {
        "部位": "脚后跟",
        "病因": "足底筋膜炎",
        "反常识": "不是骨刺是筋的事，很多人搞反了",
        "动作": "滚瓶子",
        "场景角度": "早上踩地疼"
    },
    {
        "部位": "膝盖",
        "病因": "髌骨软化/肌肉无力",
        "反常识": "膝盖不是用坏的，是歇坏的",
        "动作": "靠墙坐",
        "场景角度": "蹲下去起不来"
    },
    {
        "部位": "膝盖",
        "病因": "髌骨软化/肌肉无力",
        "反常识": "膝盖在轨道上不稳，肌肉没劲儿撑不住",
        "动作": "直抬腿",
        "场景角度": "上下楼梯疼"
    },
    {
        "部位": "腰痛",
        "病因": "腰肌劳损/梨状肌",
        "反常识": "腰疼不是腰的事，是屁股的事",
        "动作": "猫式伸展",
        "场景角度": "阴雨天加重"
    },
    {
        "部位": "腰痛",
        "病因": "腰肌劳损",
        "反常识": "越歇越没劲，肌肉不用就退化",
        "动作": "侧躺抬腿",
        "场景角度": "翻身疼"
    },
    {
        "部位": "肩膀",
        "病因": "肩袖损伤",
        "反常识": "肩膀疼不是肩周炎，是肌腱磨损了",
        "动作": "钟摆甩臂",
        "场景角度": "晚上疼得睡不着"
    },
    {
        "部位": "坐骨神经痛",
        "病因": "梨状肌压迫神经",
        "反常识": "屁股疼不是腿的事，是梨状肌太紧了",
        "动作": "4字拉伸",
        "场景角度": "走路像过电"
    },
]

# 潜力新赛道 —— 占比 30%
NEW_TOPICS = [
    {
        "部位": "耳鸣",
        "病因": "颈部供血不足",
        "反常识": "耳朵嗡嗡响，问题不在耳朵在脖子",
        "动作": "压耳屏",
        "场景角度": "听不清人说话"
    },
    {
        "部位": "后背发紧",
        "病因": "胸椎灵活度下降",
        "反常识": "后背紧不是累的，是胸椎生锈了",
        "动作": "抱头扩胸",
        "场景角度": "沉得像背石板"
    },
    {
        "部位": "髋部/大腿根",
        "病因": "髋周肌肉劳损",
        "反常识": "大腿根疼不是骨头的事，是肌肉没劲儿",
        "动作": "夹枕头",
        "场景角度": "久坐迈不开腿"
    },
    {
        "部位": "手指关节",
        "病因": "骨关节炎/劳损",
        "反常识": "手指僵不是老了，是气血过不去",
        "动作": "搓手",
        "场景角度": "天冷拿不住东西"
    },
    {
        "部位": "失眠",
        "病因": "心神不宁/气血不足",
        "反常识": "睡不好不一定是脑子想太多",
        "动作": "揉耳垂",
        "场景角度": "躺下2小时睡不着"
    },
]

# 开头场景类型（轮换使用）
OPENING_TYPES = [
    "尴尬场景",      # 公共场合出丑、被陌生人问
    "对比场景",      # 以前能做什么，现在做不到了
    "深夜独处场景",  # 凌晨醒来、睡不着
    "公共场合场景",  # 超市、公园、公交车
    "家人发现场景",  # 家人说的一句话
]

# 食疗融合（每篇随机配一个）
FOOD_THERAPY = [
    {
        "名称": "黄豆猪蹄汤",
        "食材": "猪蹄、黄豆、姜片",
        "做法": "猪蹄焯水，和泡好的黄豆一起放入锅中，加姜片，水没过食材，大火烧开转小火炖2小时，出锅前加盐调味。"
    },
    {
        "名称": "牛骨汤",
        "食材": "牛骨头、姜片、葱段",
        "做法": "牛骨焯水，加姜片、葱段，水没过骨头，大火烧开转小火炖2-3小时，出锅前加盐调味。"
    },
    {
        "名称": "黑豆红枣粥",
        "食材": "黑豆、红枣、大米",
        "做法": "黑豆提前泡一晚，和红枣、大米一起煮粥，早上喝一碗。"
    },
    {
        "名称": "山药小米粥",
        "食材": "山药、小米",
        "做法": "山药去皮切块，和小米一起煮粥，煮到软烂即可。"
    },
]


# ==================== 核心系统 ====================

class DailyArticleSystem:
    """每日文章自动化生成系统"""
    
    def __init__(self):
        self.articles_dir = CONFIG.ARTICLES_DIR
        self.articles_dir.mkdir(exist_ok=True)
        self.data_file = CONFIG.DATA_FILE
        self.used_topics = self._load_used_topics()
    
    def _load_used_topics(self):
        """加载已使用的选题"""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("used_topics", [])
            except:
                return []
        return []
    
    def _save_used_topics(self):
        """保存已使用的选题"""
        data = {
            "used_topics": self.used_topics[-100:],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def select_topic(self):
        """
        智能选题：
        - 70%概率选已验证爆款赛道
        - 30%概率选潜力新赛道
        - 自动轮换部位和角度
        """
        recent_used = self.used_topics[-20:]
        
        # 70%概率选已验证赛道
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
        
        # 随机选开头类型
        topic["开头类型"] = random.choice(OPENING_TYPES)
        
        # 随机配食疗方
        food = random.choice(FOOD_THERAPY)
        topic["食疗名称"] = food["名称"]
        topic["食疗食材"] = food["食材"]
        topic["食疗做法"] = food["做法"]
        
        # 记录使用
        self.used_topics.append(topic["部位"] + topic["场景角度"])
        self._save_used_topics()
        
        return topic
    
    def _get_system_prompt(self):
        """系统提示词"""
        return """你是一个擅长写中老年居家养生文章的创作者，账号叫"药食同源｜一家人"。

## 你的写作风格
1. 第一人称叙事，读者是45-65岁的中老年女性，用"我"的视角写
2. 开头用具体场景代入，不要平铺直叙
3. 语言口语化，像邻居大姐在聊天，有对话、有心理活动
4. 医生诊断时要有一个生活化的比喻（如"像水管被捏住了""像门轴生锈了"）
5. 动作描述要详细，包括"第一次做"的真实反应（酸、抖、疼）
6. 结尾有效果反馈+互动引导
7. 字数800-1200字
8. 每篇必须包含"动作+食疗"融合

## 绝对禁止
- 不要用"首先、其次、最后"的科普腔
- 不要写"专家说""研究表明"
- 不要写"根治、治好、管用"等疗效词
- 不要写成药品说明书

## 文章结构
1. 开头（200字）：具体场景切入
2. 症状发展（150字）：从轻微到加重
3. 医生诊断（150字）：打破常规认知 + 生活化比喻
4. 核心方法（300字）：1-3个动作 + 第一次做感受 + 坚持后变化
5. 食疗融合（150字）：家常食疗推荐 + 简单做法
6. 结尾（100字）：效果反馈 + 一句真实的话 + 互动提问
"""
    
    def _build_prompt(self, topic):
        """构建生成提示词"""
        return f"""
请写一篇关于中老年「{topic['部位']}」的居家康复文章。

## 选题要求
- 部位：{topic['部位']}
- 病因：{topic['病因']}
- 核心动作：{topic['动作']}
- 反常识钩子：{topic['反常识']}
- 场景角度：{topic['场景角度']}
- 开头类型：{topic['开头类型']}
- 食疗搭配：{topic['食疗名称']}（{topic['食疗食材']}）

## 写作要求
1. 开头用{topic['开头类型']}切入，直接进入具体场景
2. 文章中间要自然引出"{topic['反常识']}"这个认知
3. 核心动作是"{topic['动作']}"，要详细写做法和感受
4. 文章后半段加入食疗内容，推荐"{topic['食疗名称']}"，写清楚家常做法
5. 文末互动提问

直接输出完整文章，不要输出大纲。
"""
    
    def generate_article(self, topic):
        """调用 DeepSeek API 生成完整文章"""
        if not CONFIG.is_configured():
            print("❌ API未配置，请检查环境变量")
            return None
        
        prompt = self._build_prompt(topic)
        
        try:
            response = requests.post(
                CONFIG.DEEPSEEK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {CONFIG.DEEPSEEK_API_KEY}"
                },
                json={
                    "model": CONFIG.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.85,
                    "max_tokens": 2500,
                    "top_p": 0.95
                },
                timeout=90
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"❌ API调用失败: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ API调用超时")
            return None
        except Exception as e:
            print(f"❌ 生成文章异常: {e}")
            return None
    
    def generate_title(self, topic):
        """生成标题"""
        templates = [
            f"{topic['部位']}{topic['场景角度']}？社区医生教我“{topic['动作']}”，半个月好了",
            f"被{topic['部位']}折磨？医生说{topic['反常识']}，一个动作管用",
            f"{topic['部位']}不是小事！社区医生教我“{topic['动作']}”，半个月稳了",
        ]
        return random.choice(templates)
    
    def save_article(self, topic, content):
        """保存文章到本地"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{date_str}_{topic['部位']}.md"
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
        """通过 PushPlus 推送到微信"""
        if not CONFIG.PUSHPLUS_TOKEN:
            print("⚠️ 未配置 PushPlus Token")
            return False
        
        # 截断过长内容
        if len(content) > 4000:
            content = content[:4000] + "\n\n...（全文已保存至本地）"
        
        html_content = content.replace("\n", "<br>")
        
        try:
            response = requests.post(
                CONFIG.PUSHPLUS_URL,
                json={
                    "token": CONFIG.PUSHPLUS_TOKEN,
                    "title": title,
                    "content": html_content,
                    "template": "html"
                },
                timeout=15
            )
            result = response.json()
            if result.get("code") == 200:
                print(f"✅ 微信推送成功: {title}")
                return True
            else:
                print(f"❌ 推送失败: {result.get('msg', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 推送异常: {e}")
            return False
    
    def run(self):
        """执行每日完整任务"""
        print(f"\n{'='*60}")
        print(f"📝 药食同源｜一家人 · 每日文章生成")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # 检查配置
        if not CONFIG.is_configured():
            print("❌ 请配置环境变量：")
            print("   DEEPSEEK_API_KEY")
            print("   PUSHPLUS_TOKEN")
            return False
        
        print("\n📊 配置状态：")
        for k, v in CONFIG.get_config_info().items():
            print(f"   {k}: {v}")
        
        # 1. 选题
        print("\n📌 正在智能选题...")
        topic = self.select_topic()
        print(f"   ✅ 部位：{topic['部位']}")
        print(f"   ✅ 反常识：{topic['反常识']}")
        print(f"   ✅ 核心动作：{topic['动作']}")
        print(f"   ✅ 开头类型：{topic['开头类型']}")
        print(f"   ✅ 食疗：{topic['食疗名称']}")
        print(f"   ✅ 类型：{'已验证爆款' if topic['类型']=='verified' else '潜力新赛道'}")
        
        # 2. 生成文章
        print("\n⏳ 正在生成文章（调用DeepSeek API）...")
        article = self.generate_article(topic)
        
        if not article:
            print("❌ 文章生成失败")
            return False
        
        print(f"   ✅ 文章生成成功，字数：{len(article)}")
        
        # 3. 生成标题
        title = self.generate_title(topic)
        print(f"   ✅ 标题：{title}")
        
        # 4. 保存文章
        filepath = self.save_article(topic, article)
        print(f"   ✅ 已保存：{filepath}")
        
        # 5. 推送到微信
        print("\n📤 正在推送微信...")
        push_title = f"📝 今日养生 · {topic['部位']}"
        push_content = f"【选题】{topic['部位']} - {topic['反常识']}\n"
        push_content += f"【动作】{topic['动作']} | 【食疗】{topic['食疗名称']}\n"
        push_content += f"{'─'*40}\n\n{article}"
        
        success = self.push_to_wechat(push_title, push_content)
        
        # 6. 统计
        print(f"\n📊 累计已用选题：{len(self.used_topics)} 个")
        
        if success:
            print("\n✅ 全流程完成！文章已推送至微信")
        else:
            print("\n⚠️ 文章已生成，但微信推送失败")
        
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
            # 测试模式：预览选题
            topic = system.select_topic()
            print("\n📌 测试选题预览：")
            print(f"   部位：{topic['部位']}")
            print(f"   反常识：{topic['反常识']}")
            print(f"   动作：{topic['动作']}")
            print(f"   开头类型：{topic['开头类型']}")
            print(f"   食疗：{topic['食疗名称']}")
            print(f"   类型：{'已验证爆款' if topic['类型']=='verified' else '潜力新赛道'}")
            print(f"\n标题示例：{system.generate_title(topic)}")
        elif cmd == "stats":
            print(f"\n📊 统计：已用 {len(system.used_topics)} 个选题")
        elif cmd == "reset":
            system.used_topics = []
            system._save_used_topics()
            print("✅ 选题记录已重置")
        else:
            print("""
用法:
  python daily_writer.py run       # 生成+推送+保存
  python daily_writer.py test      # 预览选题
  python daily_writer.py stats     # 查看统计
  python daily_writer.py reset     # 重置选题记录
""")
    else:
        system.run()
