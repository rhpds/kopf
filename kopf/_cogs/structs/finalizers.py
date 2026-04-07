"""
All the functions to manipulate the object finalization and deletion.

Finalizers are used to block the actual deletion until the finalizers
are removed, meaning that the operator has done all its duties
to "release" the object (e.g. cleanups; delete-handlers in our case).
"""
import re
from re import Pattern

from kopf._cogs.structs import bodies, patches


def is_deletion_ongoing(
        body: bodies.Body,
) -> bool:
    return body.get('metadata', {}).get('deletionTimestamp', None) is not None


def is_deletion_blocked(
        body: bodies.Body,
        finalizer: str,
        deprecated_finalizer: str|Pattern[str]|None,
) -> bool:
    finalizers = body.get('metadata', {}).get('finalizers', [])
    if deprecated_finalizer is not None:
        if isinstance(deprecated_finalizer, Pattern):
            for item in finalizers:
                if deprecated_finalizer.match(item):
                    return True
        elif deprecated_finalizer in finalizers:
            return True
    return finalizer in finalizers

def block_deletion(
        body: bodies.RawBody,
        finalizer: str,
        deprecated_finalizer: str|Pattern[str]|None,
) -> None:
    if not is_deletion_blocked(body=body, finalizer=finalizer, deprecated_finalizer=deprecated_finalizer):
        body.setdefault('metadata', {}).setdefault('finalizers', []).append(finalizer)

def allow_deletion(
        body: bodies.RawBody,
        finalizer: str,
        deprecated_finalizer: str|Pattern[str]|None,
) -> None:
    while finalizer in body.get('metadata', {}).get('finalizers', []):
        body['metadata']['finalizers'].remove(finalizer)
    if deprecated_finalizer is not None:
        if isinstance(deprecated_finalizer, Pattern):
            for item in body['metadata']['finalizers']:
                if deprecated_finalizer.match(item):
                    body['metadata']['finalizers'].remove(item)
        else:
            while deprecated_finalizer in body.get('metadata', {}).get('finalizers', []):
                body['metadata']['finalizers'].remove(finalizer)
    if 'finalizers' in body.get('metadata', {}) and not body.get('metadata', {}).get('finalizers'):
        del body['metadata']['finalizers']
    if 'metadata' in body and not body['metadata']:
        del body['metadata']
