#!/usr/bin/env python3
"""Free, keyless logo providers tried before Logo.dev: Hunter, lndev Logos, theSVG.

Each provider turns a brand (name + official domain) into candidate download
URLs. Nothing here proves identity: a 200 response only means the provider has
*an* image for that key, so every selected file still needs visual inspection.
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from retrieve_assets import USER_AGENT, safe_url

HUNTER = 'https://logos.hunter.io/'
LNDEV = 'https://logos.lndev.me/logos/'
THESVG_REGISTRY = 'https://thesvg.org/api/registry.json'
THESVG_ICON = 'https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/{slug}/{variant}.svg'
FREE_PROVIDERS = ('hunter', 'lndev', 'thesvg')
DOMAIN = re.compile(r'^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')


def normalized(value):
    return ''.join(character for character in (value or '').lower() if character.isalnum())


def clean_domain(value):
    """Reduce a URL or host to a bare registrable host; None when not a domain."""
    if not value:
        return None
    text = str(value).strip().lower()
    host = urllib.parse.urlparse(text if '://' in text else 'https://' + text).hostname or ''
    host = host[4:] if host.startswith('www.') else host
    return host if DOMAIN.match(host) else None


def slug_candidates(name, domain=None):
    """Provider file names to try, most specific first, without duplicates."""
    words = re.findall(r'[a-z0-9]+', (name or '').lower())
    stem = domain.split('.')[0] if domain else None
    return list(dict.fromkeys(slug for slug in ('-'.join(words), ''.join(words), stem) if slug))


def hunter_urls(name, domain):
    return [HUNTER + domain] if domain else []


def lndev_urls(name, domain):
    return [LNDEV + slug + '.svg' for slug in slug_candidates(name, domain)]


class TheSvgRegistry:
    """theSVG publishes one JSON index of every icon; load it once per run."""

    def __init__(self, cache_path=None, transport=None, timeout=20, max_bytes=20_000_000):
        self.cache_path = Path(cache_path) if cache_path else None
        self.transport = transport or urllib.request.urlopen
        self.timeout, self.max_bytes = timeout, max_bytes
        self.icons, self.error = None, None

    def load(self):
        if self.icons is not None or self.error:
            return self.icons
        try:
            if self.cache_path and self.cache_path.is_file():
                data = json.loads(self.cache_path.read_text())
            else:
                if not safe_url(THESVG_REGISTRY):
                    raise ValueError('unsafe registry URL')
                request = urllib.request.Request(THESVG_REGISTRY, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
                with self.transport(request, timeout=self.timeout) as response:
                    raw = response.read(self.max_bytes + 1)
                if len(raw) > self.max_bytes:
                    raise ValueError('registry too large')
                data = json.loads(raw)
                if self.cache_path:
                    self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                    self.cache_path.write_bytes(raw)
            self.icons = data.get('icons', []) if isinstance(data, dict) else data
        except Exception as error:  # a registry failure only skips this provider
            self.error = error.__class__.__name__
            self.icons = None
        return self.icons

    def lookup(self, name, domain):
        """Prefer an exact website-domain match, then an exact name/slug/alias match."""
        icons = self.load() or []
        if domain:
            for icon in icons:
                if clean_domain(icon.get('url')) == domain:
                    return icon
        key = normalized(name)
        if key:
            for icon in icons:
                keys = [icon.get('slug'), icon.get('title'), *(icon.get('aliases') or [])]
                if any(normalized(value) == key for value in keys):
                    return icon
        return None

    def urls(self, name, domain):
        icon = self.lookup(name, domain)
        if not icon or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', icon.get('slug') or ''):
            return []
        variants = icon.get('variants') or ['default']
        variant = 'default' if 'default' in variants else variants[0]
        return [THESVG_ICON.format(slug=icon['slug'], variant=variant)]

    def licence(self, name, domain):
        icon = self.lookup(name, domain) or {}
        return icon.get('license')


def provider_sources(provider, name, domain, registry):
    """Candidate source records for one free provider, in try order."""
    if provider == 'hunter':
        urls, evidence = hunter_urls(name, domain), 'Hunter Logos lookup by official domain ' + str(domain) + '.'
    elif provider == 'lndev':
        urls, evidence = lndev_urls(name, domain), 'lndev Logos file-name match for ' + str(name) + '.'
    elif provider == 'thesvg':
        urls, evidence = registry.urls(name, domain), 'theSVG registry match (website domain first, then exact name) for ' + str(name) + '.'
    else:
        raise ValueError('unknown free provider: ' + provider)
    extra = {'usage_licence': registry.licence(name, domain)} if provider == 'thesvg' and urls else {}
    return [{'name': name, 'url': url, 'source_category': provider, 'provider': provider, 'provider_domain': domain, 'identity_evidence': evidence, **extra} for url in urls]
