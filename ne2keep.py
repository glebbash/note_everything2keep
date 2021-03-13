#!/usr/bin/env python3

try:
    import click
    import gkeepapi
except ImportError:
    import os
    os.system("pip3 install click gkeepapi")

import sys
import sqlite3
from typing import List
import click
from gkeepapi import Keep, _node as KeepValues


RAW_ITEMS_QUERY = "SELECT _id, title, type, body, folder, sticked, priority FROM Notes"
ID, TITLE, TYPE, BODY, FOLDER, PINNED, PRIORITY = range(7)

LIST_ITEMS_QUERY = "SELECT item_text, checked FROM ChecklistItems WHERE note_id=? ORDER BY sort_order ASC"
TEXT, CHECKED = range(2)


@click.command()
@click.argument("db_path")
@click.option("--email", prompt="Email")
@click.option("--password", prompt="Password", hide_input=True)
def convert(db_path: str, email: str, password: str):
    keep = connect_to_keep(email, password)

    print("Connecting to DB")

    db = sqlite3.connect(db_path)

    print("Reading notes")

    items = get_items(db)

    import_items(items, keep)

    print("Done")


class Item:
    def __init__(
        self,
        title: str,
        body: str,
        folder: str,
        pinned: bool,
        color: KeepValues.ColorValue
    ):
        self.title = title
        self.body = body
        self.folder = folder
        self.pinned = pinned
        self.color = color


class FolderItem(Item):
    def __init__(self, title: str, color: KeepValues.ColorValue):
        super().__init__(title, None, None, False, color)


class ListItem(Item):
    def __init__(self, title: str, items: List[any], pinned: bool, color: KeepValues.ColorValue):
        super().__init__(title, None, None, pinned, color)
        self.items = items


class ProgressBar:
    def __init__(self, max):
        self.max = max
        self.progress = 0
        print()

    def next(self, message: str):
        self.progress += 1
        print("\033[A                             \033[A")
        print(f"{message} {self.progress}/{self.max}")


def import_items(items: List[Item], keep: Keep):
    labels = create_labels(
        [label for label in items if type(label) is FolderItem],
        keep
    )

    items = [item for item in items if type(item) is not FolderItem]

    items_progress = ProgressBar(len(items))

    for item in items:
        item_type = type(item)

        keep_item = None
        if item_type is Item:
            keep_item = keep.createNote(item.title, item.body)
        elif item_type is ListItem:
            keep_item = keep.createList(item.title, item.items)
        else:
            raise f"Unexpected item {item}"

        keep_item.color = item.color
        keep_item.pinned = item.pinned

        if item.folder:
            keep_item.labels.add(labels[item.folder])

        items_progress.next("Adding items")
        keep.sync()


def create_labels(folders: List[FolderItem], keep: Keep):
    labels_progress = ProgressBar(len(folders))
    labels = {}

    for folder in folders:
        if folder.title != "":
            label = keep.findLabel(folder.title)
            if not label:
                label = keep.createLabel(folder.title)
                keep.sync()

            labels[folder.title] = label

        labels_progress.next("Processing labels")

    return labels


def connect_to_keep(email: str, password: str) -> Keep:
    keep = Keep()

    print("Connecting to Google Keep...")

    if not keep.login(email, password):
        print("Cannot connect to Google Keep")
        sys.exit()

    print("Connected")

    return keep


def get_items(db: sqlite3.Connection) -> List[any]:
    raw_items = db.cursor().execute(RAW_ITEMS_QUERY)
    return [transform_item(raw_item, db) for raw_item in raw_items]


def transform_item(raw_item: any, db: sqlite3.Connection) -> any:
    item_id = raw_item[ID]
    item_type = raw_item[TYPE]
    item_title = raw_item[TITLE]
    item_body = raw_item[BODY]
    item_folder = raw_item[FOLDER][1:]
    item_pinned = raw_item[PINNED] == 0
    item_color = priority_to_color(raw_item[PRIORITY])

    if item_type == None:
        return FolderItem(item_folder, item_color)

    if item_type == 4 or item_type == 5:
        items = get_list_items(item_id, db)
        return ListItem(item_title, items, item_pinned, item_color)

    return Item(
        item_title,
        item_body,
        item_folder,
        item_pinned,
        item_color)


def get_list_items(id: int, db: sqlite3.Connection) -> List[any]:
    items = db.cursor().execute(LIST_ITEMS_QUERY, (id,))
    list_items = [transform_list_item(item) for item in items]
    return list_items


def transform_list_item(raw_list_item: any):
    return raw_list_item[TEXT], raw_list_item[CHECKED] != 0


def priority_to_color(priority: int) -> KeepValues.ColorValue:
    if priority == 0:
        return KeepValues.ColorValue.White
    elif priority == 1:
        return KeepValues.ColorValue.DarkBlue
    elif priority == 2:
        return KeepValues.ColorValue.Blue
    elif priority == 3:
        return KeepValues.ColorValue.Gray
    elif priority == 4:
        return KeepValues.ColorValue.Yellow
    elif priority == 5:
        return KeepValues.ColorValue.Red
    else:
        print(f"Unsupported item priority: #{priority}")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    convert()
