# Copyright (c) 2026 ropmyung (Rakko ORM modifications and additions).
# Derived from Tortoise ORM; maintained and modified for Rakko ORM.
# SPDX-License-Identifier: Apache-2.0

"""
Tortoise PyLint plugin
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from astroid import MANAGER, inference_tip, nodes
from astroid.exceptions import AstroidError
from astroid.nodes import AnnAssign, Assign, ClassDef

if TYPE_CHECKING:
    from astroid.context import InferenceContext
    from astroid.typing import InferenceResult
    from pylint.lint import PyLinter

MODELS: dict[str, ClassDef] = {}
FUTURE_RELATIONS: dict[str, list[tuple[str, list[InferenceResult]]]] = {}


def register(linter: PyLinter) -> None:  # pylint: disable=unused-argument
    """
    Reset state every time this is called, since we now get new AST to transform.
    """
    MODELS.clear()
    FUTURE_RELATIONS.clear()


def is_model(cls: ClassDef) -> bool:
    """
    Guard to apply this transform to Models only
    """
    metaclass = cls.metaclass()
    return isinstance(metaclass, ClassDef) and metaclass.qname() == "tortoise.models.ModelMeta"


def transform_model(node: ClassDef, infer_function: Any = None) -> None:
    """
    Anything that uses the ModelMeta needs _meta and id.
    Also keep track of relationships and make them in the related model class.
    """
    if node.name != "Model":
        appname = "models"
        for mcls in node.get_children():
            if isinstance(mcls, ClassDef):
                for attr in mcls.get_children():
                    if (isinstance(attr, Assign) and isinstance(attr.targets[0], nodes.AssignName)
                        and attr.targets[0].name == "app" and isinstance(attr.value, nodes.Const)
                        and isinstance(attr.value.value, str)):
                        appname = attr.value.value

        mname = f"{appname}.{node.name}"
        MODELS[mname] = node

        for relname, relval in FUTURE_RELATIONS.get(mname, []):
            node.locals[relname] = relval

        for attr in node.get_children():
            if isinstance(attr, (Assign, AnnAssign)):
                if isinstance(attr.value, nodes.Call) and isinstance(attr.value.func, nodes.Attribute):
                    attrname = attr.value.func.attrname
                    if attrname in ["OneToOneField", "ForeignKeyField", "ManyToManyField"]:
                        tomodel = ""
                        if attr.value.args and isinstance(attr.value.args[0], nodes.Const):
                            if isinstance(attr.value.args[0].value, str):
                                tomodel = attr.value.args[0].value
                        relname = ""
                        if attr.value.keywords:
                            for keyword in attr.value.keywords:
                                if not isinstance(keyword.value, nodes.Const):
                                    continue
                                if not isinstance(keyword.value.value, str):
                                    continue
                                if keyword.arg == "related_name":
                                    relname = keyword.value.value
                                if keyword.arg == "model_name":
                                    tomodel = keyword.value.value

                        if not relname:
                            relname = node.name.lower() + "s"

                        # Injected model attributes need to also have the relation manager
                        relval: list[InferenceResult]
                        if attrname == "ManyToManyField":
                            relval = [
                                # attr.value.func,
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "ManyToManyFieldInstance"
                                )[1][0],
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "ManyToManyRelation"
                                )[1][0],
                            ]
                        elif attrname == "ForeignKeyField":
                            relval = [
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "ForeignKeyFieldInstance"
                                )[1][0],
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "ReverseRelation"
                                )[1][0],
                            ]
                        else:
                            relval = [
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "OneToOneFieldInstance"
                                )[1][0],
                                MANAGER.ast_from_module_name("tortoise.fields.relational").lookup(
                                    "OneToOneRelation"
                                )[1][0],
                            ]

                        if tomodel in MODELS:
                            MODELS[tomodel].locals[relname] = relval
                        else:
                            FUTURE_RELATIONS.setdefault(tomodel, []).append((relname, relval))

    node.locals["_meta"] = [
        MANAGER.ast_from_module_name("tortoise.models").lookup("MetaInfo")[1][0].instantiate_class()
    ]
    if "id" not in node.locals:
        id_nodes: list[InferenceResult] = [
            nodes.ClassDef("id", node.lineno or 0, node.col_offset or 0, node, end_lineno=None, end_col_offset=None)
        ]
        node.locals["id"] = id_nodes


def is_model_field(cls: ClassDef) -> bool:
    """
    Guard to apply this transform to Model Fields only
    """
    type_name = "tortoise.fields.base.Field"
    return bool(cls.is_subtype_of(type_name)) and cls.qname() != type_name


def apply_type_shim(node: ClassDef, context: InferenceContext | None = None, **kwargs: Any) -> Iterator[InferenceResult]:
    """
    Morphs model fields to representative type
    """
    base_nodes: list[InferenceResult] = [node]

    # Use the type inference standard
    try:
        base_nodes.extend(list(node.getattr("field_type")[0].infer()))
    except AstroidError:
        pass

    return iter(base_nodes)


MANAGER.register_transform(nodes.ClassDef, inference_tip(apply_type_shim), is_model_field)
MANAGER.register_transform(nodes.ClassDef, transform_model, is_model)
