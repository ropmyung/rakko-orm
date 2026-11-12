# Modified for Rakko ORM: correct type annotations used by documentation introspection.

import ast
import inspect
import sys
import textwrap
import typing
from typing import Any, AnyStr, Generic, NewType, Protocol, TypeVar, Union, get_type_hints

import type_globals
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.inspect import signature as Signature
from sphinx.util.inspect import stringify_signature

logger = logging.getLogger(__name__)
pydata_annotations = {
    "Any",
    "AnyStr",
    "Callable",
    "ClassVar",
    "NoReturn",
    "Optional",
    "Tuple",
    "Union",
}


def format_annotation(annotation: Any, fully_qualified: bool = False) -> str:
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        if annotation.__qualname__ == "NoneType":
            return "``None``"
        else:
            return f':py:class:`{annotation.__qualname__}`'

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ == "typing":
        class_name = str(annotation).split('[')[0].split('.')[-1]
        params = None
        module = "typing"
        extra = ""

        origin = getattr(annotation, "__origin__", None)
        if inspect.isclass(origin):
            annotation_cls = origin
            try:
                mro = annotation_cls.mro()
                if Generic in mro or Protocol in mro:
                    module = annotation_cls.__module__
            except TypeError:
                pass  # annotation_cls was either the "type" object or typing.Type

        if annotation is Any:
            return ":py:data:`{}typing.Any`".format("" if fully_qualified else '~')
        elif annotation is AnyStr:
            return ":py:data:`{}typing.AnyStr`".format("" if fully_qualified else '~')
        elif isinstance(annotation, TypeVar):
            bound = annotation.__bound__
            if bound:
                if "ForwardRef(" in str(bound):
                    try:
                        bound = bound._evaluate(sys.modules[annotation.__module__].__dict__, None)
                    except Exception:
                        try:
                            bound = bound._evaluate(type_globals.__dict__, None)
                        except Exception:
                            bound = bound.__forward_arg__
                return format_annotation(bound, fully_qualified)
            return f'\\{annotation!r}'
        elif annotation is Union or getattr(annotation, "__origin__", None) is Union:
            params = getattr(annotation, "__args__", None)

            if (
                params
                and len(params) == 2
                and (hasattr(params[1], "__qualname__") and params[1].__qualname__ == "NoneType")
            ):
                class_name = "Optional"
                params = (params[0],)
        elif annotation_cls.__qualname__ == "Callable":
            arg_annotations = result_annotation = None
            args = getattr(annotation, "__args__", ())
            if args:
                arg_annotations = args[:-1]
                result_annotation = args[-1]

            if arg_annotations in (Ellipsis, (Ellipsis,)):
                params = [Ellipsis, result_annotation]
            elif arg_annotations is not None:
                params = [
                    "\\[{}]".format(
                        ", ".join(
                            format_annotation(param, fully_qualified) for param in arg_annotations
                        )
                    ),
                    result_annotation,
                ]
        elif getattr(annotation, "__args__", None) is not None:
            params = getattr(annotation, "__args__")
        elif hasattr(annotation, "__parameters__"):
            params = getattr(annotation, "__parameters__")

        if params:
            extra = "\\[{}]".format(
                ", ".join(format_annotation(param, fully_qualified) for param in params)
            )

        return "{prefix}`{qualify}{module}.{name}`{extra}".format(
            prefix=":py:data:" if class_name in pydata_annotations else ":py:class:",
            qualify="" if fully_qualified else '~',
            module=module,
            name=class_name,
            extra=extra,
        )
    elif annotation is Ellipsis:
        return "..."
    elif isinstance(annotation, NewType):
        return ":py:func:`{qualify}typing.NewType`\\(:py:data:`~{name}`, {extra})".format(
            qualify="" if fully_qualified else '~',
            name=annotation.__name__,
            extra=format_annotation(annotation.__supertype__, fully_qualified),
        )
    elif inspect.isclass(annotation) or inspect.isclass(getattr(annotation, "__origin__", None)):
        if not inspect.isclass(annotation):
            annotation_cls = getattr(annotation, "__origin__")

        extra = ""
        try:
            mro = annotation_cls.mro()
        except TypeError:
            pass
        else:
            if Generic in mro or Protocol in mro:
                params = getattr(annotation, "__parameters__", None) or getattr(
                    annotation, "__args__", None
                )
                if params:
                    extra = "\\[{}]".format(
                        ", ".join(format_annotation(param, fully_qualified) for param in params)
                    )

        return ":py:class:`{qualify}{module}.{name}`{extra}".format(
            qualify="" if fully_qualified else '~',
            module=annotation.__module__,
            name=annotation_cls.__qualname__,
            extra=extra,
        )

    return str(annotation)


def process_signature(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Any,
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str, None] | None:
    if not callable(obj):
        return

    if what in ("class", "exception"):
        obj = getattr(obj, "__init__", getattr(obj, "__new__", None))

    if not callable(obj) or not getattr(obj, "__annotations__", None):
        return

    obj = inspect.unwrap(obj)
    inspected_signature = Signature(obj)
    parameters = [
        param.replace(annotation=inspect.Parameter.empty)
        for param in inspected_signature.parameters.values()
    ]

    if "<locals>" in obj.__qualname__:
        logger.warning(
            'Cannot treat a function defined as a local function: "%s"  (use @functools.wraps)',
            name,
        )
        return

    if parameters:
        if what in ("class", "exception"):
            del parameters[0]
        elif what == "method":
            outer = inspect.getmodule(obj)
            for clsname in obj.__qualname__.split('.')[:-1]:
                outer = getattr(outer, clsname)

            method_name = obj.__name__
            if method_name.startswith("__") and not method_name.endswith("__"):
                # If the method starts with double underscore (dunder)
                # Python applies mangling so we need to prepend the class name.
                # This doesn't happen if it always ends with double underscore.
                class_name = obj.__qualname__.split('.')[-2]
                method_name = f'_{class_name}{method_name}'

            method_object = outer.__dict__[method_name] if outer else obj
            if not isinstance(method_object, (classmethod, staticmethod)):
                del parameters[0]

    inspected_signature = inspected_signature.replace(
        parameters=parameters, return_annotation=inspect.Signature.empty
    )

    return stringify_signature(inspected_signature).replace('\\', "\\\\"), None


def get_all_type_hints(obj: Any, name: str) -> dict[str, Any]:
    rv = {}

    try:
        rv = get_type_hints(obj)
    except (AttributeError, TypeError, RecursionError):
        # Introspecting a slot wrapper will raise TypeError, and and some recursive type
        # definitions will cause a RecursionError (https://github.com/python/typing/issues/574).
        pass
    except NameError:
        try:
            rv = get_type_hints(obj, localns=type_globals.__dict__)
        except Exception as exc:
            logger.warning(
                'Cannot resolve forward reference in type annotations of "%s": %s', name, exc
            )
            rv = obj.__annotations__

    if rv:
        return rv

    rv = backfill_type_hints(obj, name)

    try:
        obj.__annotations__ = rv
    except (AttributeError, TypeError):
        return rv

    try:
        rv = get_type_hints(obj)
    except (AttributeError, TypeError):
        pass
    except NameError as exc:
        try:
            rv = get_type_hints(obj, localns=type_globals.__dict__)
        except Exception:
            logger.warning(
                'Cannot resolve forward reference in type annotations of "%s": %s', name, exc
            )
            rv = obj.__annotations__

    return rv


def backfill_type_hints(obj: Any, name: str) -> dict[str, str]:
    try:
        module = ast.parse(textwrap.dedent(inspect.getsource(obj)), type_comments=True)
    except TypeError:
        return {}

    if len(module.body) != 1:
        logger.warning(
            'Did not get exactly one node from AST for "%s", got %s', name, len(module.body)
        )
        return {}

    obj_ast = module.body[0]
    if not isinstance(obj_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {}

    type_comment = obj_ast.type_comment
    if not type_comment:
        return {}

    try:
        comment_args_str, comment_returns = type_comment.split(" -> ")
    except ValueError:
        logger.warning('Unparsable type hint comment for "%s": Expected to contain ` -> `', name)
        return {}

    rv = {}
    if comment_returns:
        rv["return"] = comment_returns

    args = load_args(obj_ast)
    comment_args: list[str | None] = list(split_type_comment_args(comment_args_str))
    is_inline = len(comment_args) == 1 and comment_args[0] == "..."
    if not is_inline:
        if args and args[0].arg in ("self", "cls") and len(comment_args) != len(args):
            comment_args.insert(0, None)  # self/cls may be omitted in type comments, insert blank

        if len(args) != len(comment_args):
            logger.warning('Not enough type comments found on "%s"', name)
            return rv

    for at, arg in enumerate(args):
        if is_inline:  # the type information now is tied to the argument
            value = arg.type_comment
        else:  # type data from comment
            value = comment_args[at]

        if value is not None:
            rv[arg.arg] = value

    return rv


def load_args(obj_ast: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    func_args = obj_ast.args
    args = [*func_args.posonlyargs, *func_args.args]
    if func_args.vararg:
        args.append(func_args.vararg)

    args.extend(func_args.kwonlyargs)
    if func_args.kwarg:
        args.append(func_args.kwarg)

    return args


def split_type_comment_args(comment: str) -> list[str]:
    def add(val: str) -> None:
        result.append(val.strip().lstrip('*'))  # remove spaces, and var/kw arg marker

    comment = comment.strip().lstrip('(').rstrip(')')
    result: list[str] = []
    if not comment:
        return result

    brackets, start_arg_at, at = 0, 0, 0
    for at, char in enumerate(comment):
        if char in ('[', '('):
            brackets += 1
        elif char in (']', ')'):
            brackets -= 1
        elif char == ',' and brackets == 0:
            add(comment[start_arg_at:at])
            start_arg_at = at + 1

    add(comment[start_arg_at : at + 1])
    return result


def process_docstring(
    app: Sphinx,
    what: str,
    name: str,
    obj: Any,
    options: Any,
    lines: list[str],
) -> None:
    if isinstance(obj, property):
        obj = obj.fget

    if callable(obj):
        if what in ("class", "exception"):
            obj = getattr(obj, "__init__")

        obj = inspect.unwrap(obj)
        type_hints = get_all_type_hints(obj, name)

        for argname, annotation in type_hints.items():
            if argname == "return":
                continue  # this is handled separately later
            if argname.endswith('_'):
                argname = f'{argname[:-1]}\\_'

            formatted_annotation = format_annotation(
                annotation, fully_qualified=app.config.typehints_fully_qualified
            )

            searchfor = f':param {argname}:'
            insert_index = None

            for i, line in enumerate(lines):
                if line.startswith(searchfor):
                    insert_index = i
                    break

            if insert_index is None and app.config.always_document_param_types:
                lines.append(searchfor)
                insert_index = len(lines)

            if insert_index is not None:
                lines.insert(insert_index, f':type {argname}: {formatted_annotation}')

        if "return" in type_hints and what not in ("class", "exception"):
            formatted_annotation = format_annotation(
                type_hints["return"], fully_qualified=app.config.typehints_fully_qualified
            )

            insert_index = len(lines)
            for i, line in enumerate(lines):
                if line.startswith(":rtype:"):
                    insert_index = None
                    break
                elif line.startswith(":return:") or line.startswith(":returns:"):
                    insert_index = i

            if insert_index is not None:
                if insert_index == len(lines):
                    # Ensure that :rtype: doesn't get joined with a paragraph of text, which
                    # prevents it being interpreted.
                    lines.append("")
                    insert_index += 1

                lines.insert(insert_index, f':rtype: {formatted_annotation}')


def builder_ready(app: Sphinx) -> None:
    if app.config.set_type_checking_flag:
        typing.TYPE_CHECKING = True


def setup(app: Sphinx) -> dict[str, bool]:
    app.add_config_value("set_type_checking_flag", False, "html")
    app.add_config_value("always_document_param_types", False, "html")
    app.add_config_value("typehints_fully_qualified", False, "env")
    app.connect("builder-inited", builder_ready)
    app.connect("autodoc-process-signature", process_signature)
    app.connect("autodoc-process-docstring", process_docstring)
    return dict(parallel_read_safe=True)
