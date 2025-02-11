#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import asyncio
import importlib
import logging
import pkgutil
import random
from inspect import signature
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger("normalize_url")


def escape_sql_symbols(search_content: str) -> str:
    # 对通配符进行转义
    return search_content.replace("%", "\\%").replace("_", "\\_")


def import_submodules(package: str | ModuleType, recursive: bool = True) -> Dict[str, ModuleType]:
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results


def locals_to_params(args: Dict, func: Optional[Callable] = None, exclude: Optional[List[str]] = None) -> Dict:
    params = {}
    default = {}
    default_exclude = ["cls", "self"]

    if func:
        default = {kv[0]: kv[1].default for kv in signature(func).parameters.items() if kv[0]}

    if exclude:
        default_exclude.extend(exclude)

    for arg, value in args.items():
        if arg in default_exclude:
            continue
        if default and arg not in default:
            continue
        if value != default.get(arg):
            params[arg] = value
    return params


def retry(
    *,
    name: Optional[str] = None,
    max_retries: int = 5,
    max_backoff: int = 10,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    error: Optional[str] = None,
    warning: Optional[str] = None,
    raise_max_attempt_retries: Optional[Type[Exception]] = None,
) -> Callable:
    logger = logging.getLogger("retry")
    factor = 5
    max_exponent = 32

    if not exceptions:
        exceptions = (Exception,)

    def wrapper(f: Callable) -> Callable:
        async def retry_decorator(*args: Any, **kwargs: Any) -> Any:
            attempts = 0
            while True:
                attempts += 1
                try:
                    return await f(*args, **kwargs)
                except exceptions as exc:  # type: ignore
                    if attempts > max_retries:
                        if error:
                            logger.error(f"error: {error}", exc_info=True)
                        if raise_max_attempt_retries:
                            raise raise_max_attempt_retries
                        raise

                    message = f"[{attempts}/{max_retries}] ({name or f.__name__}) "
                    if warning:
                        message += f" {warning}"

                    message += f"reason: {exc.args}"

                    logger.warning(message)

                    exponent = min(attempts, max_exponent)
                    backoff = min(factor * 2**exponent, max_backoff)

                    backoff /= 2
                    backoff = backoff + random.uniform(0, backoff)

                    await asyncio.sleep(backoff)

        return retry_decorator

    return wrapper
