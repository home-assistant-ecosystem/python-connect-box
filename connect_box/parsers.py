def _parse_general_time(xml_root):
    """Convert <GeneralTime> to"""

    el = xml_root.find("GeneralTime/time")
    if el is not None:
        return ",".join(
            [
                str(int(h) * 60 + int(m))
                for t in el.text.split("-")
                for h, m in [t.split(":")]
            ]
        )
    else:
        return None


def _parse_daily_time(xml_root):
    """Convert contents of <DailyTime> to decimal mask"""
    mask = [[0 for h in range(24)] for d in range(7)]
    for instance in xml_root.findall("DailyTime/time_instance"):
        day = int(instance.find("daily").text) - 1
        s, e = instance.find("time").text.split("-")
        s, e = int(s), int(e) + 1
        mask[day][s:e] = [1] * (e - s)

    output = []
    for daybin in mask:
        daydec = 0
        for bit in daybin:
            daydec = (daydec << 1) | bit
        output.append(str(daydec))

    if output is not None and len(output):
        return ",".join(output)
    else:
        return None
