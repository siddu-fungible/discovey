from web.fun_test.django_interactive import *

from web.fun_test.models import User
from django.contrib.auth.models import User as AuthUser

old_users = User.objects.all()

for old_user in old_users:
    print old_user.email
    disabled_users = ["chhan", "durg", "fred", "icloud", "pendse", "priyanko", "nazir", "rick", "aamir", "biji"]
    if [disabled_user for disabled_user in disabled_users if disabled_user in old_user.email]:
        continue
    new_auth_user = AuthUser(username=old_user.email,
                             email=old_user.email,
                             password="fun123fun123",
                             is_superuser=False,
                             is_active=True,
                             is_staff=True,
                             first_name=old_user.first_name,
                             last_name=old_user.last_name)
    new_auth_user.save()
    new_auth_user.set_password('fun123fun123')
    new_auth_user.save()