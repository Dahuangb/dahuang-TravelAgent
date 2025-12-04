def export_full_md(itinerary_days):
    """
    itinerary_days: List[DayPlan]  # 每天一个 DayPlan
    返回：Markdown 文本
    """
    lines = ["# 全程旅行行程单", ""]
    total_km = 0.0
    total_min = 0

    for day in itinerary_days:
        lines.append(f"## Day {day.day} 行程")
        day_km = 0.0
        day_min = 0
        for act in day.activities:
            # 只对步行活动显示步行时间和符号
            if act.transport_mode == "步行" and act.transport_duration > 0:
                lines.append(f"- {act.start.strftime('%m-%d %H:%M')} - {act.end.strftime('%H:%M')}　{act.name}　🚶{act.transport_duration}min")
                day_km += act.transport_duration * 80 / 1000   # 80 m/min → km（简化）
                day_min += act.transport_duration
            else:
                lines.append(f"- {act.start.strftime('%m-%d %H:%M')} - {act.end.strftime('%H:%M')}　{act.name}")
        lines.append(f"> 本日步行：{day_km:.2f} km · {day_min} min")
        total_km += day_km
        total_min += day_min
        lines.append("")

    lines.append("---")
    lines.append(f"**全程总结**：总步行 {total_km:.2f} km · 总时长 {total_min} min**")
    return "\n".join(lines)