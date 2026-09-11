#!/usr/bin/env python3
"""Compatibility launcher for the French 5000 APKG builder.

Some PyPI builds of Anki 26.08.x expose the protobuf request/option types and
Rust backend RPCs, but omit the thin Collection.import_anki_package() /
Collection.export_anki_package() wrappers present in the official source tree.
Install equivalent wrappers before loading the real builder.
"""
from __future__ import annotations

import runpy
from pathlib import Path

from anki import import_export_pb2
from anki.collection import Collection


def _pb_export_limit(limit):
    message = import_export_pb2.ExportLimit()
    if limit is None:
        message.whole_collection.SetInParent()
    elif hasattr(limit, "deck_id"):
        message.deck_id = int(limit.deck_id)
    elif hasattr(limit, "note_ids"):
        message.note_ids.note_ids.extend(int(x) for x in limit.note_ids)
    elif hasattr(limit, "card_ids"):
        message.card_ids.card_ids.extend(int(x) for x in limit.card_ids)
    else:
        raise TypeError(f"Unsupported export limit: {limit!r}")
    return message


def _install_compatibility_wrappers() -> None:
    print("ANKI COLLECTION API:", [name for name in dir(Collection) if "anki_package" in name])

    if not hasattr(Collection, "import_anki_package"):
        def import_anki_package(self, request):
            raw = self._backend.import_anki_package_raw(request.SerializeToString())
            return import_export_pb2.ImportResponse.FromString(raw)

        Collection.import_anki_package = import_anki_package
        print("Installed Collection.import_anki_package compatibility wrapper")

    if not hasattr(Collection, "export_anki_package"):
        def export_anki_package(self, *, out_path, options, limit):
            return self._backend.export_anki_package(
                out_path=out_path,
                options=options,
                limit=_pb_export_limit(limit),
            )

        Collection.export_anki_package = export_anki_package
        print("Installed Collection.export_anki_package compatibility wrapper")


_install_compatibility_wrappers()
runpy.run_path(str(Path(__file__).with_name("build_english_apkg.py")), run_name="__main__")
