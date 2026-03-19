import re
from astrbot.api import logger
from astrbot.api import AstrBotConfig



def replace_text(config: AstrBotConfig, text: str) -> str:
    
    # 工具名称替换列表，格式为 ["工具名称:替换文本", ...]
    disguise_map_raw = config.get("disguise_map", [])

    # 是否默认输出前缀 "🔨"
    enable_default_prefix = bool(config.get("enable_default_prefix", False))

    # 不在列表的工具的处理方式: "保持系统默认"/"使用通用伪装"/ "彻底隐藏"
    unknown_tool_behavior = str(config.get("unknown_tool_behavior", "保持系统默认"))

    # 通用伪装文本，适用于未在列表中映射的工具
    generic_disguise = str(config.get("generic_disguise", "[正在努力处理中...]"))

    # 工具调用的正则匹配模式，默认匹配 "🔨 调用工具: 工具名称"
    matching_regex = str(config.get("matching_regex", "🔨 调用工具: (.*)"))

    # 是否记录被拦截和替换的工具调用日志
    log_intercept = bool(config.get("log_intercept", True))


    # 替换映射元组
    mapping = _parse_disguise_map(disguise_map_raw)

    # 检测用户填写的正则表达式是否有效，若无效则使用默认正则表达式
    try:
        pattern = re.compile(f"^{matching_regex}$")
    except re.error:
        pattern = re.compile(r"^🔨 调用工具: (.*)$")

    # 过滤非工具调用的文本
    if not pattern.search(text):
        return text

    def _replacement(match: re.Match) -> str:
        tool_name = match.group(1).strip() if match.lastindex and match.group(1) is not None else match.group(0)
        result = None

        # 遍历映射列表，找到匹配的工具名称并获取对应的替换文本
        for key, value in mapping:
            if tool_name == key:
                result = value
                break

        if result is None:
            if unknown_tool_behavior == "使用通用伪装":
                result = generic_disguise
            elif unknown_tool_behavior == "彻底隐藏":
                result = ""
            else:
                return match.group(0)

        if enable_default_prefix and result:
            if not result.startswith("🔨"):
                result = f"🔨 {result}"

        return result

    replaced_text = pattern.sub(_replacement, text)

    if log_intercept and replaced_text != text:
        try:
            logger.info(f"拦截并替换: '{text}' => '{replaced_text}'")
        except Exception:
            pass

    return replaced_text



def _parse_disguise_map(raw_map: list) -> list:
    """
    解析字符串列表格式的映射表。

    将类似 ["get_weather:查询天气"] 的原始列表转换为 (键, 值) 元组列表。
    函数会自动处理冒号两边的空格，并确保只拆分第一个出现的冒号。

    Args:
        raw_map (list): 格式为 ["key:value", ...] 的字符串列表。

    Returns:
        list[tuple[str, str]]: 解析后的元组列表，例如 [("get_weather", "查询天气")]。
        如果输入不是列表或格式不符，将返回空列表。
    """
    mapping = []
    if not isinstance(raw_map, list):
        logger.warning("伪装替换列表配置项格式错误，应该是一个字符串列表。")
        return mapping

    for item in raw_map:
        # 确保元素是字符串且包含冒号
        if isinstance(item, str) and ":" in item:
            # split(":", 1) 确保即便 value 中有冒号也不会被拆分
            key, value = item.split(":", 1)
            mapping.append((key.strip(), value.strip()))
            
    return mapping