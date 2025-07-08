# core/templatetags/badges.py
from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def avatar_with_badge(user, size=64):
	"""
	例）{{ user|avatar_with_badge }}        → 64px
	    {{ user|avatar_with_badge:80 }}    → 80px
	"""
	profile = getattr(user, 'userprofile', None)
	if not profile:
		return ''

	# アバター画像（未設定時はダミー）
	img_url = (
		profile.profile_image.url
		if getattr(profile, 'profile_image', None)
		else static('img/user-unset.webp')
	)

	badge = profile.verification_badge or ''      # blue / pink / silver / gold / ''
	badge_cls = f'--{badge}' if badge else ''

	html = f'''
		<span class="avatar main-avatar check-badge check-badge{badge_cls}">
			<img src="{img_url}" loading="lazy" alt="{user.username}">
		</span>
	'''
	return mark_safe(html)


@register.filter
def get_doc(qs, doc_type):
	"""doc_type='identify' などで該当レコードを返す"""
	return qs.filter(doc_type=doc_type).first() if qs else None