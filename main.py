from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain
from astrbot.api import AstrBotConfig
from func import replace_text  # 确保 func.py 在同目录下

@register("text_modifier", "YourName", "高优先级消息修改插件", "1.0.0")
class TextModifierPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.on_decorating_result(priority=100)
    async def handle_sensitive_words(self, event: AstrMessageEvent):
        result = event.get_result()
        if not result or not result.chain:
            return
        
        for component in result.chain:
            if isinstance(component, Plain):
                component.text = replace_text(self.config, component.text)