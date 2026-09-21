from .models import Banner, Page, Promotion, SiteSettings


def _url(field):
    return field.url if field else None


def banner_data(b: Banner) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "eyebrow": b.eyebrow,
        "image": _url(b.image),
        "image_mobile": _url(b.image_mobile),
        "link": b.link,
        "cta_label": b.cta_label,
        "placement": b.placement,
        "theme": b.theme,
    }


def promotion_data(p: Promotion) -> dict:
    return {
        "id": p.id,
        "slug": p.slug,
        "title": p.title,
        "description": p.description,
        "discount_percent": p.discount_percent,
        "image": _url(p.image),
        "starts_at": p.starts_at.isoformat() if p.starts_at else None,
        "ends_at": p.ends_at.isoformat() if p.ends_at else None,
    }


def page_data(p: Page, with_body: bool = True) -> dict:
    data = {
        "slug": p.slug,
        "title": p.title,
        "show_in_footer": p.show_in_footer,
        "seo_title": p.seo_title,
        "seo_description": p.seo_description,
        "updated_at": p.updated_at.isoformat(),
    }
    if with_body:
        data["body"] = p.body
    return data


def settings_data(s: SiteSettings) -> dict:
    return {
        "phones": s.phones,
        "email": s.email,
        "address": s.address,
        "work_hours": s.work_hours,
        "map_embed_url": s.map_embed_url,
        "socials": s.socials or {},
        "iban_details": s.iban_details,
        "pickup_note": s.pickup_note,
        "about_short": s.about_short,
        "seo_title": s.seo_title,
        "seo_description": s.seo_description,
    }
