from post_office import mail

def send_notification_email(*, user, template, context):
	"""
	日本語サイトのみ → language=''（空）で固定。
	"""
	mail.send(
		recipients=[user.email],
		template=template,
		context=context,
		language='',        # ← Admin 側も Language を空欄にしておく
		priority='now',
	)
