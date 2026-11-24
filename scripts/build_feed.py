"""Собирает YML-фид для Яндекс Директа из data/feed.json и проверяет его по правилам Директа.

Запуск:  python3 scripts/build_feed.py
Результат: feeds/estate_start_feed.yml

Правила (см. docs/direct_feed_rules.md):
- ID товара — только число (нужно для фильтров), уникальный;
- заголовок объявления до 56 символов, текст до 81 (description + sales_notes);
- в name и description нет рекламного текста и сведений о продаже, нет обещаний дохода;
- property name до 26 символов, не больше 10 характеристик;
- до 5 картинок на товар.
"""
import json
import sys
from pathlib import Path
from xml.dom import minidom
from xml.sax.saxutils import escape, quoteattr

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "feed.json"
OUT = ROOT / "feeds" / "estate_start_feed.yml"

NAME_MAX = 56
TEXT_MAX = 81
PROP_NAME_MAX = 26
PROPS_MAX = 10
PICTURES_MAX = 5
# Запрещено в name/description: призывы, продажа, доходность (закон о рекламе и требования Директа).
BANNED = ["купить", "продаж", "доход", "прибыл", "окупаем", "бесплатн", "гарант"]
# Доходность нельзя и в sales_notes.
BANNED_ANYWHERE = ["доход", "прибыл", "окупаем", "гарант"]


def validate(data):
    errors = []
    ids = set()
    for o in data["offers"]:
        oid = o["id"]
        tag = f"offer {oid}"
        if not isinstance(oid, int) or oid <= 0:
            errors.append(f"{tag}: ID должен быть положительным числом")
        if oid in ids:
            errors.append(f"{tag}: ID повторяется")
        ids.add(oid)
        if o["object"] not in data["objects"]:
            errors.append(f"{tag}: неизвестный объект {o['object']}")
        if len(o["name"]) > NAME_MAX:
            errors.append(f"{tag}: name {len(o['name'])} > {NAME_MAX} символов")
        text_len = len(o["description"]) + 1 + len(o.get("sales_notes", ""))
        if text_len > TEXT_MAX:
            errors.append(f"{tag}: description + sales_notes {text_len} > {TEXT_MAX} символов")
        low = (o["name"] + " " + o["description"]).lower()
        for w in BANNED:
            if w in low:
                errors.append(f"{tag}: запрещённое слово «{w}» в name/description")
        for w in BANNED_ANYWHERE:
            if w in o.get("sales_notes", "").lower():
                errors.append(f"{tag}: запрещённое слово «{w}» в sales_notes")
    for key, obj in data["objects"].items():
        if len(obj["properties"]) > PROPS_MAX:
            errors.append(f"{key}: больше {PROPS_MAX} характеристик")
        for pn, _ in obj["properties"]:
            if len(pn) > PROP_NAME_MAX:
                errors.append(f"{key}: property name «{pn}» длиннее {PROP_NAME_MAX}")
        if not 1 <= len(obj["pictures"]) <= PICTURES_MAX:
            errors.append(f"{key}: картинок должно быть от 1 до {PICTURES_MAX}")
    return errors


def build(data):
    shop = data["shop"]
    objs = data["objects"]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<yml_catalog date="2026-11-24T12:00">',
        "  <shop>",
        f"    <name>{escape(shop['name'])}</name>",
        f"    <company>{escape(shop['company'])}</company>",
        f"    <url>{escape(shop['url'])}</url>",
        '    <currencies><currency id="RUR" rate="1"/></currencies>',
        "    <categories>",
    ]
    for obj in objs.values():
        lines.append(f'      <category id="{obj["category_id"]}">{escape(obj["category"])}</category>')
    lines += ["    </categories>", "    <offers>"]
    for o in data["offers"]:
        obj = objs[o["object"]]
        lines += [
            f'      <offer id="{o["id"]}" available="true">',
            f"        <name>{escape(o['name'])}</name>",
            f"        <url>{escape(obj['url'])}</url>",
            f'        <price from="true">{obj["price"]}</price>',
            "        <currencyId>RUR</currencyId>",
            f"        <categoryId>{obj['category_id']}</categoryId>",
        ]
        lines += [f"        <picture>{escape(p)}</picture>" for p in obj["pictures"]]
        lines.append(f"        <description>{escape(o['description'])}</description>")
        if o.get("sales_notes"):
            lines.append(f"        <sales_notes>{escape(o['sales_notes'])}</sales_notes>")
        lines += [
            f"        <custom_label_0>{escape(o['object'])}</custom_label_0>",
            f"        <custom_label_1>{escape(o['variant'])}</custom_label_1>",
        ]
        lines += [
            f"        <property name={quoteattr(pn)}>{escape(pv)}</property>"
            for pn, pv in obj["properties"]
        ]
        lines.append("      </offer>")
    lines += ["    </offers>", "  </shop>", "</yml_catalog>", ""]
    return "\n".join(lines)


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print("Фид НЕ собран, ошибки:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    xml = build(data)
    minidom.parseString(xml.encode("utf-8"))  # проверка, что XML валиден
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(xml, encoding="utf-8")
    print(f"OK: {OUT.relative_to(ROOT)}, товаров: {len(data['offers'])}")
    for o in data["offers"]:
        print(f"  {o['id']}  {o['object']:<8} {o['variant']}  {o['name']}")


if __name__ == "__main__":
    main()
